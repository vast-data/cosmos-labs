"""
Authentication service for VAST system integration
"""
import logging
import requests
import jwt
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Optional, Annotated
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import api_key
from src.models.user import User
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# FastAPI security scheme
auth_scheme = api_key.APIKeyHeader(name="Authorization", auto_error=False)

# Token cache to avoid validating every request
# Format: {token: (user_data, expiry_time)}
_token_cache = {}


def get_admin_token(address: str) -> Optional[str]:
    """
    Get admin JWT token for API queries
    
    Args:
        address: VAST management hostname or IP
        
    Returns:
        JWT token if successful, None otherwise
    """
    try:
        logger.debug(f"Getting admin token from VAST: {address}")
        
        login_url = f"https://{address}/api/token/"
        response = requests.post(
            login_url,
            json={
                "username": settings.vast_admin_username,
                "password": settings.vast_admin_password
            },
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access")
            logger.debug("Admin token obtained successfully")
            return access_token
        else:
            logger.error(f"Admin authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting admin token: {str(e)}")
        return None


def query_user_by_username(vast_host: str, username: str, admin_token: str) -> Optional[dict]:
    """
    Query VAST API to get user info by username
    Searches all providers: local, Active Directory, LDAP, NIS
    
    Args:
        vast_host: VAST cluster address
        username: Username to query
        admin_token: Admin JWT token for authentication
        
    Returns:
        User data dict if found, None otherwise
    """
    try:
        response = requests.get(
            f"https://{vast_host}/api/users/query/",
            params={
                "username": username,
                "context": "aggregated"  # Search all providers (local, AD, LDAP, NIS)
            },
            headers={"Authorization": f"Bearer {admin_token}"},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"User query failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error querying user: {str(e)}")
        return None


def get_user_s3_keys(vast_host: str, user_id: int, admin_token: str) -> list:
    """
    Get all S3 access keys for a user
    
    Args:
        vast_host: VAST cluster address
        user_id: User ID
        admin_token: Admin JWT token
        
    Returns:
        List of access key dicts
    """
    try:
        response = requests.get(
            f"https://{vast_host}/api/users/{user_id}/",
            headers={"Authorization": f"Bearer {admin_token}"},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            access_keys = user_data.get("access_keys", [])
            logger.debug(f"Found {len(access_keys)} S3 keys for user {user_id}")
            return access_keys
        else:
            logger.warning(f"Failed to get S3 keys: {response.status_code}")
            return []
        
    except Exception as e:
        logger.error(f"Error getting S3 keys: {str(e)}")
        return []


def validate_s3_credentials(vast_host: str, access_key: str, secret_key: str) -> bool:
    """
    Validate S3 credentials by making a test API call
    Uses s3_endpoint from settings if configured
    
    Args:
        vast_host: VAST cluster address (fallback if s3_endpoint not configured)
        access_key: S3 access key
        secret_key: S3 secret key
        
    Returns:
        True if credentials are valid, False otherwise
    """
    # Get S3 endpoint from settings (preferred) or fallback to vast_host
    s3_endpoint = getattr(settings, 's3_endpoint', None)
    if not s3_endpoint:
        # Fallback: construct from vast_host
        protocol = 'http' if not getattr(settings, 's3_use_ssl', True) else 'https'
        s3_endpoint = f'{protocol}://{vast_host}'
        logger.warning(f"No s3_endpoint configured, using constructed endpoint: {s3_endpoint}")
    
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            verify=False,
            config=Config(signature_version='s3v4')
        )
        
        s3_client.list_buckets()
        return True
        
    except ClientError as e:
        logger.warning(f"S3 ClientError for key {access_key}: {e.response.get('Error', {}).get('Code', 'Unknown')}")
        return False
    except Exception as e:
        logger.error(f"Error validating S3 credentials: {type(e).__name__}: {str(e)}")
        return False


def authenticate_local_user(address: str, username: str, secret_key: str) -> Optional[dict]:
    """
    Authenticate VAST user with username + S3 secret key
    Supports users from all providers: local, Active Directory, LDAP, NIS
    
    Args:
        address: VAST management hostname or IP
        username: User's username (from any provider)
        secret_key: User's S3 secret key
        
    Returns:
        User info dict if authenticated, None otherwise
    """
    logger.info(f"Authenticating user: {username} at {address}")
    
    # Step 1: Get admin token for API queries
    admin_token = get_admin_token(address)
    if not admin_token:
        logger.error("Failed to obtain admin token")
        return None
    
    # Step 2: Query user by username
    user_data = query_user_by_username(address, username, admin_token)
    if not user_data:
        logger.warning(f"User not found: {username}")
        return None
    
    # Get VAST ID (vid) as user identifier
    user_id = user_data.get("vid") or user_data.get("uid")
    if not user_id:
        logger.error(f"No vid/uid in query response. Available fields: {list(user_data.keys())}")
        return None
    
    # Step 3: Get S3 access keys from query response (they're already included!)
    access_keys_raw = user_data.get("access_keys", [])
    if not access_keys_raw:
        logger.warning(f"No S3 keys found for user: {username}")
        return None
    
    logger.debug(f"Found {len(access_keys_raw)} S3 keys for user {username}")
    
    # Step 4: Validate secret_key with each access_key
    # Format: [['ACCESS_KEY', 'enabled', 'local', '2025-11-27T09:46:27+00:00'], ...]
    for key_data in access_keys_raw:
        if not isinstance(key_data, list) or len(key_data) < 2:
            continue
            
        access_key = key_data[0]
        status = key_data[1]
        
        if status != "enabled":
            logger.debug(f"Skipping disabled key: {access_key}")
            continue
        
        # Validate credentials
        if validate_s3_credentials(address, access_key, secret_key):
            logger.info(f"Successfully authenticated {username} with S3 credentials")
            return {
                "user_id": user_id,
                "username": username,
                "access_key": access_key,
                "auth_type": "s3_local",
                "email": user_data.get("email"),
                "uid": user_data.get("uid"),
                "gid": user_data.get("leading_gid")
            }
    
    logger.warning(f"Invalid secret key for user: {username}")
    return None




def create_internal_jwt(user_data: dict) -> str:
    """
    Create internal JWT token for authenticated user
    
    Args:
        user_data: User information dict
        
    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_data.get("user_id"),
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "auth_type": user_data.get("auth_type"),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=8)  # 8 hour token lifetime
    }
    
    # Create token without signature (we're using cache for validation)
    token = jwt.encode(payload, "not-used", algorithm="HS256")
    return token


async def get_current_user(authorization: Annotated[Optional[str], Depends(auth_scheme)] = None) -> User:
    """
    FastAPI dependency to get current authenticated user
    Uses caching to validate internal JWT tokens
    
    Args:
        authorization: Authorization header value
        
    Returns:
        User object
        
    Raises:
        HTTPException if authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization:
        logger.error("No authorization header provided")
        raise credentials_exception
    
    # Extract token (handle "Bearer <token>" format)
    token = authorization
    if authorization.lower().startswith("bearer "):
        token = authorization[7:]
    
    if not token:
        logger.error("Empty token after processing")
        raise credentials_exception
    
    try:
        # Check cache first
        if token in _token_cache:
            cached_data, expiry = _token_cache[token]
            if datetime.now() < expiry:
                logger.debug(f"Using cached token for user: {cached_data['username']}")
                return User(
                    username=cached_data.get("username", ""),
                    email=cached_data.get("email"),
                    auth_type=cached_data.get("auth_type", "s3_local"),
                    token_claims=cached_data
                )
            else:
                # Cache expired, remove it
                del _token_cache[token]
                logger.warning("Token expired")
            raise credentials_exception
        
        # Token not in cache - invalid
        logger.warning("Token not found in cache")
        raise credentials_exception
        
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise credentials_exception


async def get_current_user_from_token(token: str) -> User:
    """
    Validate token and return user (used for video streaming with token in URL)
    
    This function is similar to get_current_user but accepts the token
    as a string parameter instead of extracting it from headers.
    This is needed for HTML5 <video> elements which cannot send custom headers.
    
    Args:
        token: JWT token string
        
    Returns:
        User object
        
    Raises:
        Exception if authentication fails
    """
    if not token:
        raise Exception("No token provided")
    
    try:
        # Check cache
        if token in _token_cache:
            cached_data, expiry = _token_cache[token]
            if datetime.now() < expiry:
                logger.debug(f"Using cached token for user: {cached_data['username']}")
                return User(
                    username=cached_data.get("username", ""),
                    email=cached_data.get("email"),
                    auth_type=cached_data.get("auth_type", "s3_local"),
                    token_claims=cached_data
                )
            else:
                # Cache expired
                del _token_cache[token]
                raise Exception("Token expired")
            
        # Token not in cache - invalid
        raise Exception("Invalid token")
    
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]

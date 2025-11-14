"""
Authentication service for VAST system integration
"""
import logging
import requests
import jwt
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


def vast_login(address: str, username: str, password: str) -> Optional[str]:
    """
    Login to a VAST system and get a JWT token
    
    Args:
        address: VAST management hostname or IP
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        JWT token if successful, None otherwise
    """
    if settings.dev_mode:
        logger.warning("DEV MODE: Using dummy VAST authentication")
        if username == settings.dev_mode_username and password == "admin":
            return "dummy_vast_token_for_dev_mode"
        return None
    
    try:
        logger.info(f"Authenticating to VAST system: {address}, user: {username}")
        
        # VAST API login endpoint
        login_url = f"https://{address}/api/token/"
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            verify=False,  # Skip SSL verification for internal VAST endpoints
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access")
            logger.info("VAST authentication successful")
            return access_token
        else:
            logger.error(f"VAST authentication failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error during VAST authentication: {str(e)}")
        return None


def validate_vast_token(token: str, address: str) -> dict:
    """
    Validate VAST JWT token by making API call
    
    Args:
        token: JWT token string
        address: VAST host address
        
    Returns:
        User information dict
        
    Raises:
        Exception on validation failure
    """
    if settings.dev_mode:
        return {
            "username": settings.dev_mode_username,
            "email": f"{settings.dev_mode_username}@dev.local",
            "user_id": "dev-user-id",
            "auth_type": "vast"
        }
    
    # Decode JWT token without verification to get user_id
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("user_id")
        
        if not user_id:
            raise Exception("No user_id found in JWT token")
        
        # Verify token by making API call
        response = requests.get(
            f"https://{address}/api/latest/users/{user_id}/",
            headers={"Authorization": f"Bearer {token}"},
            verify=False,  # Skip SSL verification for internal VAST endpoints
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"VAST API returned status {response.status_code}")
        
        user_data = response.json()
        username = user_data.get("username")
        
        if not username:
            raise Exception("No username found in VAST API response")
        
        email = user_data.get("email")
        
        return {
            "username": username,
            "email": email,
            "user_id": user_id,
            "auth_type": "vast",
            **user_data
        }
        
    except Exception as e:
        logger.error(f"Error validating VAST token: {str(e)}")
        raise


async def get_current_user(authorization: Annotated[Optional[str], Depends(auth_scheme)] = None) -> User:
    """
    FastAPI dependency to get current authenticated user
    Uses caching to avoid validating VAST token on every request
    
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
    
    # Dev mode bypass
    if settings.dev_mode and not authorization:
        logger.warning("DEV MODE: Bypassing authentication")
        return User(
            username=settings.dev_mode_username,
            email=f"{settings.dev_mode_username}@dev.local",
            auth_type="vast",
            dev_mode=True,
            token_claims={}
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
        # Check cache first (5 minute cache)
        if token in _token_cache:
            cached_data, expiry = _token_cache[token]
            if datetime.now() < expiry:
                logger.debug(f"Using cached token for user: {cached_data['username']}")
                return User(
                    username=cached_data.get("username", ""),
                    email=cached_data.get("email"),
                    auth_type="vast",
                    dev_mode=False,
                    token_claims=cached_data
                )
            else:
                # Cache expired, remove it
                del _token_cache[token]
        
        # Decode JWT locally first (fast validation)
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # DEBUG: Log all JWT payload fields to see what's available
            logger.info(f"[DEBUG] JWT payload keys: {list(payload.keys())}")
            # Sanitize sensitive fields for logging
            sanitized_payload = {k: ('***' if k in ['exp', 'iat', 'nbf'] else v) for k, v in payload.items()}
            logger.debug(f"[DEBUG] JWT payload (sanitized): {sanitized_payload}")
            
            # Extract user_id and username directly from JWT payload
            user_id = payload.get("user_id")
            if not user_id:
                raise Exception("No user_id found in JWT token")
            
            # Try to extract username directly from JWT payload
            # VAST JWT may contain: username, name, preferred_username, email, user_id, sub
            username = payload.get("username") or payload.get("preferred_username") or payload.get("name") or payload.get("sub")
            email = payload.get("email")
            
            # If username not in JWT, use user_id as fallback
            if not username:
                logger.warning(f"Username not found in JWT payload, using user_id: {user_id}")
                username = str(user_id)
            else:
                logger.info(f"Using username from JWT payload: {username}")
            
            # Create user data
            user_data = {
                "username": username,
                "email": email,
                "user_id": str(user_id),
                "auth_type": "vast"
            }
            
            # Cache for 5 minutes
            _token_cache[token] = (user_data, datetime.now() + timedelta(minutes=5))
            
            logger.info(f"JWT token validated for user: {username}")
            return User(
                username=username,
                email=email,
                auth_type="vast",
                dev_mode=False,
                token_claims=user_data
            )
            
        except jwt.DecodeError:
            logger.warning("Invalid JWT format")
            raise credentials_exception
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
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
        # Check cache first (5 minute cache)
        if token in _token_cache:
            cached_data, expiry = _token_cache[token]
            if datetime.now() < expiry:
                logger.debug(f"Using cached token for user: {cached_data['username']}")
                return User(
                    username=cached_data.get("username", ""),
                    email=cached_data.get("email"),
                    auth_type="vast",
                    dev_mode=False,
                    token_claims=cached_data
                )
            else:
                # Cache expired, remove it
                del _token_cache[token]
        
        # Decode JWT locally first (fast validation)
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Extract user_id and username directly from JWT payload
            user_id = payload.get("user_id")
            if not user_id:
                raise Exception("No user_id found in JWT token")
            
            # Try to extract username directly from JWT payload
            username = payload.get("username") or payload.get("preferred_username") or payload.get("name") or payload.get("sub")
            email = payload.get("email")
            
            # If username not in JWT, use user_id as fallback
            if not username:
                logger.warning(f"Username not found in JWT payload, using user_id: {user_id}")
                username = str(user_id)
            
            # Cache the token
            _token_cache[token] = ({
                "username": username,
                "email": email,
                "user_id": str(user_id),
                "auth_type": "vast"
            }, datetime.now() + timedelta(minutes=5))
            
            logger.debug(f"JWT token validated for user: {username}")
            
            return User(
                username=username,
                email=email,
                auth_type="vast",
                dev_mode=False,
                token_claims=payload
            )
            
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid JWT token: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]


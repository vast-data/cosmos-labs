"""
Authentication API endpoints
"""
import logging
import jwt
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from src.schemas.auth import VastLoginRequest, Token, UserInfo
from src.services.auth_service import vast_login, CurrentUser, _token_cache
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(request: VastLoginRequest):
    """
    Login with VAST credentials
    
    Args:
        request: Login request with username, password, and VAST host
        
    Returns:
        JWT token and user information
    """
    logger.info(f"Login attempt for user: {request.username} at host: {request.vast_host}")
    
    token = vast_login(
        address=request.vast_host,
        username=request.username,
        password=request.password
    )
    
    if not token:
        logger.warning(f"Login failed for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or unable to connect to VAST system"
        )
    
    # Decode token to get actual username from VAST
    settings = get_settings()
    actual_username = request.username  # Default fallback (form input)
    user_id = None  # Initialize
    
    try:
        # Decode JWT to get user_id
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("user_id")
        
        # Try to get username from JWT payload first (most reliable)
        jwt_username = payload.get("username") or payload.get("preferred_username") or payload.get("name") or payload.get("sub")
        if jwt_username and jwt_username != str(user_id):
            actual_username = jwt_username
            logger.info(f"Login successful for user: {actual_username} (from JWT payload)")
        elif user_id:
            # Fallback: Fetch username from VAST API
            try:
                response = requests.get(
                    f"https://{request.vast_host}/api/latest/users/{user_id}/",
                    headers={"Authorization": f"Bearer {token}"},
                    verify=False,  # Skip SSL verification for internal VAST endpoints
                    timeout=5
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    actual_username = user_data.get("username", request.username)
                    logger.info(f"Login successful for user: {actual_username} (from VAST API, user_id: {user_id})")
                else:
                    logger.warning(f"Failed to fetch username from VAST API (status {response.status_code}), using form input: {request.username}")
            except Exception as api_error:
                logger.warning(f"Error calling VAST API: {api_error}, using form input: {request.username}")
        else:
            logger.warning(f"No user_id in JWT, using form input: {request.username}")
    except Exception as e:
        logger.warning(f"Error decoding JWT: {e}, using form input: {request.username}")
    
    # Cache the username with the token for future requests
    _token_cache[token] = ({
        "username": actual_username,
        "email": None,  # Will be populated by get_current_user if needed
        "user_id": str(user_id) if user_id else None,
        "auth_type": "vast"
    }, datetime.now() + timedelta(minutes=5))
    
    return Token(
        access_token=token,
        token_type="bearer",
        username=actual_username
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        User information
    """
    logger.info(f"User info request for: {current_user.username}")
    
    return UserInfo(
        username=current_user.username,
        email=current_user.email,
        auth_type=current_user.auth_type
    )


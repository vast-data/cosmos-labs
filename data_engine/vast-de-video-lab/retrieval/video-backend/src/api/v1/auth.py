"""
Authentication API endpoints
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from src.schemas.auth import VastLoginRequest, Token, UserInfo
from src.services.auth_service import authenticate_local_user, create_internal_jwt, CurrentUser, _token_cache
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(request: VastLoginRequest):
    """
    Login with VAST user credentials (username + S3 secret key + tenant name)
    Supports users from all providers: local, Active Directory, LDAP, NIS
    Supports both default and non-default tenants
    
    Args:
        request: Login request with username, secret_key, vast_host, and tenant_name
        
    Returns:
        JWT token and user information
    """
    logger.info(f"Login attempt for user: {request.username} at host: {request.vast_host} (tenant: {request.tenant_name})")
    
    # Authenticate user with username + S3 secret key (any provider, any tenant)
    user_data = authenticate_local_user(
        address=request.vast_host,
        username=request.username,
        secret_key=request.secret_key,
        tenant_name=request.tenant_name
    )
    
    if not user_data:
        logger.warning(f"Login failed for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username, secret key, or tenant"
        )
    
    logger.info(f"Login successful for user: {user_data['username']} (tenant: {request.tenant_name})")
    
    # Create internal JWT token for our application
    internal_token = create_internal_jwt(user_data)
    
    # Cache user data with token (8 hour cache to match token lifetime)
    _token_cache[internal_token] = (user_data, datetime.now() + timedelta(hours=8))
    
    return Token(
        access_token=internal_token,
        token_type="bearer",
        username=user_data["username"]
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

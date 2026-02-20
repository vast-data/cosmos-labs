"""
Authentication routes
"""
import logging
from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from typing import Optional

from models import LoginRequest, LoginResponse
from services.auth import (
    authenticate_with_rag, decode_jwt,
    get_azure_ad_authorization_url, exchange_azure_ad_code_for_tokens, validate_azure_ad_jwt
)

logger = logging.getLogger(__name__)


class AuthRouter:
    """Router for authentication endpoints"""
    
    @staticmethod
    async def login(request: LoginRequest = LoginRequest()) -> LoginResponse:
        """
        Authenticate with RAG backend and get access token.
        
        Returns:
            LoginResponse with access_token, jwt_token, and jwt_payload
        """
        try:
            token = authenticate_with_rag(
                base_url=request.base_url,
                username=request.username,
                password=request.password
            )
            
            jwt_payload = decode_jwt(token)
            
            return LoginResponse(
                access_token=token,
                token_type="Bearer",
                jwt_token=token,
                jwt_payload=jwt_payload
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    @staticmethod
    async def azure_ad_login(request: Request):
        """
        Initiate Azure AD OAuth login flow.
        Redirects user to Azure AD authorization endpoint.
        """
        try:
            # Generate state for CSRF protection
            state = request.query_params.get("state")
            auth_url = get_azure_ad_authorization_url(state=state)
            return RedirectResponse(url=auth_url)
        except Exception as e:
            logger.error(f"Azure AD login error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initiate Azure AD login: {str(e)}")
    
    @staticmethod
    async def azure_ad_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
        """
        Handle Azure AD OAuth callback.
        Exchanges authorization code for tokens and validates JWT.
        
        Args:
            code: Authorization code from Azure AD
            state: State parameter for CSRF protection
            error: Error from Azure AD if authentication failed
        
        Returns:
            RedirectResponse with token in URL fragment or error page
        """
        try:
            # Check for errors from Azure AD
            if error:
                logger.error(f"Azure AD callback error: {error}")
                # Redirect to frontend with error
                from config import AUTH_AZURE_NEXTAUTH_URL
                frontend_url = AUTH_AZURE_NEXTAUTH_URL or str(request.base_url).rstrip('/')
                error_url = f"{frontend_url}/login?error={error}"
                return RedirectResponse(url=error_url)
            
            if not code:
                raise HTTPException(status_code=400, detail="Authorization code missing")
            
            # Exchange code for tokens
            token_response = exchange_azure_ad_code_for_tokens(code)
            id_token = token_response.get("id_token")
            access_token = token_response.get("access_token")
            
            if not id_token:
                raise HTTPException(status_code=500, detail="No ID token in response")
            
            # Validate the ID token
            jwt_payload = validate_azure_ad_jwt(id_token)
            
            # Use Azure AD id_token directly - this is the JWT the user will use to access the system
            app_token = id_token
            
            # Store token temporarily in memory with a short session ID
            # This avoids URL length limits with long tokens
            import secrets
            import time
            session_id = secrets.token_urlsafe(16)  # 16 bytes = 22 chars base64
            
            # Store in a simple in-memory dict (in production, use Redis or similar)
            if not hasattr(AuthRouter.azure_ad_callback, '_token_cache'):
                AuthRouter.azure_ad_callback._token_cache = {}
            
            # Store token with 5 minute expiry
            AuthRouter.azure_ad_callback._token_cache[session_id] = {
                'token': app_token,
                'expires_at': time.time() + 300  # 5 minutes
            }
            
            # Clean up expired entries
            current_time = time.time()
            AuthRouter.azure_ad_callback._token_cache = {
                k: v for k, v in AuthRouter.azure_ad_callback._token_cache.items()
                if v['expires_at'] > current_time
            }
            
            # Redirect to frontend home page with session ID instead of full token
            from config import AUTH_AZURE_NEXTAUTH_URL
            frontend_url = AUTH_AZURE_NEXTAUTH_URL or str(request.base_url).rstrip('/')
            # Redirect directly to home page (chat/new) with session_id
            success_url = f"{frontend_url}/#/chat/new?session_id={session_id}&provider=azuread"
            logger.info(f"Redirecting to frontend home page with session_id (token length: {len(app_token)})")
            return RedirectResponse(url=success_url)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Azure AD callback error: {e}", exc_info=True)
            from config import AUTH_AZURE_NEXTAUTH_URL
            frontend_url = AUTH_AZURE_NEXTAUTH_URL or str(request.base_url).rstrip('/')
            error_url = f"{frontend_url}/login?error=callback_failed"
            return RedirectResponse(url=error_url)
    
    @staticmethod
    async def exchange_session_token(request: Request) -> dict:
        """
        Exchange a session ID for the Azure AD token.
        This is used to avoid URL length limits with long tokens.
        
        Args:
            request: FastAPI Request object containing session_id query parameter
            
        Returns:
            dict with 'token' key containing the Azure AD token
        """
        import time
        
        session_id = request.query_params.get('session_id')
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id query parameter required")
        
        # Check if token cache exists
        if not hasattr(AuthRouter.azure_ad_callback, '_token_cache'):
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get token from cache
        cache_entry = AuthRouter.azure_ad_callback._token_cache.get(session_id)
        if not cache_entry:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check expiry
        if cache_entry['expires_at'] <= time.time():
            # Remove expired entry
            del AuthRouter.azure_ad_callback._token_cache[session_id]
            raise HTTPException(status_code=404, detail="Session expired")
        
        # Remove from cache after use (one-time use)
        token = cache_entry['token']
        del AuthRouter.azure_ad_callback._token_cache[session_id]
        
        return {'token': token}


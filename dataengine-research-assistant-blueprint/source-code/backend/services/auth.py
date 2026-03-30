"""
Authentication service
Handles JWT token validation and user authentication
"""

import os
import json
import base64
import logging
import secrets
import urllib.parse
from typing import Dict, Any, Optional
from fastapi import HTTPException, Header
import httpx
import jwt
from jwt import PyJWKClient

from config import (
    RAG_BASE_URL, RAG_USERNAME, RAG_PASSWORD, RAG_SSL_VERIFY, RAG_TIMEOUT,
    AUTH_AZURE_CLIENT_ID, AUTH_AZURE_CLIENT_SECRET, AUTH_AZURE_NEXTAUTH_SECRET,
    AUTH_AZURE_AUTHORIZATION_ENDPOINT, AUTH_AZURE_TOKEN_ENDPOINT,
    AUTH_AZURE_ISSUER_ENDPOINT, AUTH_AZURE_JWKS_ENDPOINT, AUTH_AZURE_REDIRECT_URI
)

logger = logging.getLogger(__name__)


def authenticate_with_rag(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """
    Authenticate with RAG backend and get access token.
    
    Args:
        base_url: Base URL of the RAG API (defaults to RAG_BASE_URL config)
        username: Username for authentication (defaults to RAG_USERNAME config)
        password: Password for authentication (defaults to RAG_PASSWORD config)
    
    Returns:
        Access token string
    
    Raises:
        HTTPException: If authentication fails
    """
    base_url = (base_url or RAG_BASE_URL).rstrip('/')
    username = username or RAG_USERNAME
    password = password or RAG_PASSWORD
    
    client = httpx.Client(
        base_url=base_url,
        verify=RAG_SSL_VERIFY,
        timeout=RAG_TIMEOUT
    )
    
    try:
        response = client.post(
            "/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        token_data = response.json()
        token = token_data.get("access_token")
        if not token:
            raise ValueError("Failed to get access token from authentication response")
        return token
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Authentication failed: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during authentication: {str(e)}"
        )
    finally:
        client.close()


def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Decode JWT token without verification (just to read the payload).
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded JWT payload as dictionary
    """
    try:
        # JWT tokens have 3 parts separated by dots: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed for base64 decoding
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        # Decode base64
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_str = decoded_bytes.decode('utf-8')
        
        # Parse JSON
        return json.loads(decoded_str)
    except Exception as e:
        # If decoding fails, return empty dict
        return {"error": f"Failed to decode JWT: {str(e)}"}


def get_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and validate token from Authorization header.
    Token should be in format: "Bearer <token>"
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <token>'")
    
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    return token


def get_headers(token: str) -> Dict[str, str]:
    """
    Get headers with authentication token for RAG API requests.
    
    Args:
        token: JWT token string
    
    Returns:
        Dictionary with headers including Authorization Bearer token
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# Azure AD OAuth functions
def get_azure_ad_authorization_url(state: Optional[str] = None) -> str:
    """
    Generate Azure AD OAuth authorization URL.
    
    Args:
        state: Optional state parameter for CSRF protection
    
    Returns:
        Authorization URL string
    """
    if not AUTH_AZURE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Azure AD client ID not configured")
    
    if not state:
        state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": AUTH_AZURE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": AUTH_AZURE_REDIRECT_URI,
        "response_mode": "query",
        "scope": "openid profile email",
        "state": state
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"{AUTH_AZURE_AUTHORIZATION_ENDPOINT}?{query_string}"


def exchange_azure_ad_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchange Azure AD authorization code for access and ID tokens.
    
    Args:
        code: Authorization code from Azure AD callback
    
    Returns:
        Dictionary containing tokens and token info
    
    Raises:
        HTTPException: If token exchange fails
    """
    if not AUTH_AZURE_CLIENT_ID or not AUTH_AZURE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Azure AD credentials not configured")
    
    client = httpx.Client(timeout=30.0)
    
    try:
        response = client.post(
            AUTH_AZURE_TOKEN_ENDPOINT,
            data={
                "client_id": AUTH_AZURE_CLIENT_ID,
                "client_secret": AUTH_AZURE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": AUTH_AZURE_REDIRECT_URI,
                "grant_type": "authorization_code"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Azure AD token exchange failed: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to exchange authorization code: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error during Azure AD token exchange: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during token exchange: {str(e)}"
        )
    finally:
        client.close()


def validate_azure_ad_jwt(token: str) -> Dict[str, Any]:
    """
    Validate Azure AD JWT token using JWKS endpoint.
    
    Args:
        token: JWT token string from Azure AD
    
    Returns:
        Decoded and validated JWT payload
    
    Raises:
        HTTPException: If token validation fails
    """
    if not AUTH_AZURE_JWKS_ENDPOINT or not AUTH_AZURE_ISSUER_ENDPOINT:
        raise HTTPException(status_code=500, detail="Azure AD endpoints not configured")
    
    try:
        # Create JWKS client to fetch signing keys
        jwks_client = PyJWKClient(AUTH_AZURE_JWKS_ENDPOINT)
        
        # Get the signing key from the token header
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and validate the token
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUTH_AZURE_CLIENT_ID,
            issuer=AUTH_AZURE_ISSUER_ENDPOINT
        )
        
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid Azure AD token: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Error validating Azure AD token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error validating token: {str(e)}")


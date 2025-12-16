"""
Authentication schemas
"""
from pydantic import BaseModel


class VastLoginRequest(BaseModel):
    """Login request with VAST user credentials (all providers supported)"""
    username: str
    secret_key: str  # S3 secret key (for local, AD, LDAP, or NIS users)
    vast_host: str


class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str
    username: str


class UserInfo(BaseModel):
    """User information response"""
    username: str
    email: str | None = None
    auth_type: str

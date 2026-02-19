"""
User models for authentication
"""
from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """User model after authentication"""
    username: str
    email: Optional[str] = None
    auth_type: str  # "s3_local"
    token_claims: dict = {}

    @property
    def normalized_username(self) -> str:
        """
        Username normalized for VastDB compatibility
        pi.no_cchio@domain.com -> pi_no_cchio
        simon.golan -> simon_golan
        """
        return self.username.split('@')[0].lower().replace(".", "_").replace(" ", "_")


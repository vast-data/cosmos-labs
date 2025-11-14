"""
Configuration API endpoint to view backend settings
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from ...services.auth_service import get_current_user
from ...models.user import User
from ...config import get_settings

router = APIRouter(prefix="/config", tags=["config"])


def _mask_sensitive(value: str) -> str:
    """Mask sensitive configuration values"""
    if not value:
        return "••••••••"
    return "••••••••"


@router.get("", response_model=Dict[str, Any])
async def get_configuration(current_user: User = Depends(get_current_user)):
    """
    Get backend configuration settings
    Requires authentication
    Sensitive values (access keys, secrets, API keys) are masked
    """
    settings = get_settings()
    
    config = {
        "s3": {
            "s3_endpoint": settings.s3_endpoint,
            "s3_access_key": _mask_sensitive(settings.s3_access_key),
            "s3_secret_key": _mask_sensitive(settings.s3_secret_key),
            "s3_upload_bucket": settings.s3_upload_bucket,
            "s3_segments_bucket": settings.s3_segments_bucket,
            "s3_region": settings.s3_region,
            "s3_use_ssl": settings.s3_use_ssl,
        },
        "vastdb": {
            "vdb_endpoint": settings.vdb_endpoint,
            "vdb_bucket": settings.vdb_bucket,
            "vdb_schema": settings.vdb_schema,
            "vdb_collection": settings.vdb_collection,
            "vdb_access_key": _mask_sensitive(settings.vdb_access_key),
            "vdb_secret_key": _mask_sensitive(settings.vdb_secret_key),
        },
        "embedding": {
            "embedding_host": settings.embedding_host,
            "embedding_port": settings.embedding_port,
            "embedding_http_scheme": settings.embedding_http_scheme,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "nvidia_api_key": _mask_sensitive(settings.nvidia_api_key),
            "embedding_default": settings.embedding_default,
        },
        "llm": {
            "llm_model_name": settings.llm_model_name,
            "llm_host": settings.llm_host,
            "llm_port": settings.llm_port,
            "llm_http_scheme": settings.llm_http_scheme,
            "llm_timeout_seconds": settings.llm_timeout_seconds,
            "llm_top_n_summaries": settings.llm_top_n_summaries,
            "system_prompt_path": settings.system_prompt_path,
        },
        "app": {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
            "max_upload_size_mb": settings.max_upload_size_mb,
            "allowed_video_extensions": settings.allowed_video_extensions,
            "dev_mode": settings.dev_mode,
            "dev_mode_username": settings.dev_mode_username,
            "cors_origins": settings.cors_origins,
        }
    }
    
    return config


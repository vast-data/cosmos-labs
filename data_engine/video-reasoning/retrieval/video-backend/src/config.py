"""
Configuration management for Video Reasoning Backend
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
import yaml
import os


class Settings(BaseSettings):
    """Application settings loaded from environment or secret file"""
    
    # API Settings (defaults only, not required in secret)
    app_name: str = Field(default="Video Reasoning API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # VastDB Settings
    vdb_endpoint: str = Field(..., description="VastDB endpoint")
    vdb_bucket: str = Field(default="videoreasoningdb", description="VastDB bucket")
    vdb_schema: str = Field(default="video_schema", description="VastDB schema")
    vdb_collection: str = Field(default="processedvideos", description="VastDB collection")
    vdb_access_key: str = Field(..., description="VastDB access key")
    vdb_secret_key: str = Field(..., description="VastDB secret key")
    
    # S3 Settings
    s3_endpoint: str = Field(..., description="S3 endpoint URL")
    s3_access_key: str = Field(..., description="S3 access key")
    s3_secret_key: str = Field(..., description="S3 secret key")
    s3_upload_bucket: str = Field(default="video-uploads", description="S3 bucket for video uploads")
    s3_segments_bucket: str = Field(default="video-segments", description="S3 bucket for processed video segments")
    s3_region: str = Field(default="us-east-1", description="S3 region")
    s3_use_ssl: bool = False
    
    # NVIDIA NIM Embedding Settings
    embedding_host: str = Field(..., description="NVIDIA NIM embedding host")
    embedding_port: int = Field(default=80, description="NVIDIA NIM embedding port")
    embedding_http_scheme: str = Field(default="http", description="HTTP scheme")
    embedding_model: str = Field(default="nvidia/nv-embedqa-e5-v5", description="Embedding model")
    embedding_dimensions: int = Field(default=1024, description="Embedding dimensions")
    nvidia_api_key: Optional[str] = Field(default="", description="NVIDIA API key (for cloud)")
    embedding_default: bool = Field(default=True, description="Use default NVIDIA Cloud")
    
    # Upload Settings
    max_upload_size_mb: int = Field(default=25, description="Maximum upload size in MB")
    allowed_video_extensions: list[str] = Field(
        default=[".mp4", ".avi", ".mov", ".mkv", ".webm"],
        description="Allowed video file extensions"
    )
    
    # LLM Settings (NVIDIA API)
    llm_model_name: str = Field(default="meta/llama-3.1-8b-instruct", description="LLM model name")
    llm_host: str = Field(default="integrate.api.nvidia.com", description="LLM API host")
    llm_port: int = Field(default=443, description="LLM API port")
    llm_http_scheme: str = Field(default="https", description="LLM HTTP scheme")
    llm_timeout_seconds: int = Field(default=10, description="LLM API timeout in seconds")
    llm_top_n_summaries: int = Field(default=3, description="Number of summaries to send to LLM")
    system_prompt_path: str = Field(default="/app/config/system_prompt.txt", description="Path to system prompt file")
    
    # Authentication Settings
    dev_mode: bool = Field(default=False, description="Development mode (skip auth)")
    dev_mode_username: str = Field(default="dev_user", description="Dev mode username")
    
    # CORS Settings (defaults only, not required in secret)
    cors_origins: list[str] = Field(
        default=["http://localhost:4200"],
        description="Allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings: Optional[Settings] = None


def load_settings_from_yaml(yaml_path: str) -> dict:
    """Load settings from YAML file"""
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        # Handle nested structure (e.g., videobackendsecret: {...})
        if isinstance(data, dict) and len(data) == 1:
            key = list(data.keys())[0]
            return data[key]
        return data


def get_settings() -> Settings:
    """Get or create global settings instance"""
    global _settings
    if _settings is None:
        # Try to load from mounted secret file first
        secret_path = os.getenv("SECRET_PATH", "/etc/secrets/config.yaml")
        if os.path.exists(secret_path):
            print(f"📄 Loading configuration from {secret_path}")
            config_data = load_settings_from_yaml(secret_path)
            _settings = Settings(**config_data)
        else:
            print("📄 Loading configuration from environment variables")
            _settings = Settings()
    return _settings


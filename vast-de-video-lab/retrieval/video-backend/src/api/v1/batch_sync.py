"""
Video Batch Sync Management API

Proxies requests to the video batch sync service running in the same namespace.
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from src.services.auth_service import get_current_user
from src.models.user import User
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Internal K8s DNS for batch sync service (same namespace)
BATCH_SYNC_SERVICE_URL = "http://video-batch-sync-service:5000"


# Models
class BatchSyncConfigPrefill(BaseModel):
    """Response model for batch sync config prefill data"""
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    bucket_name: str


class BatchSyncCheckObjectsRequest(BaseModel):
    """Request model for checking objects in source bucket"""
    access_key: str = Field(..., description="S3 access key")
    secret_key: str = Field(..., description="S3 secret key")
    s3_endpoint: str = Field(..., description="S3 endpoint URL")
    bucket: str = Field(..., description="S3 bucket name")
    prefix: str = Field(..., description="S3 prefix/path")
    use_ssl: bool = Field(default=False, description="Use SSL for S3 endpoint")


class BatchSyncStartRequest(BaseModel):
    """Request model for starting batch sync"""
    # Source S3 configuration
    source_access_key: str = Field(..., description="Source S3 access key")
    source_secret_key: str = Field(..., description="Source S3 secret key")
    source_s3_endpoint: str = Field(..., description="Source S3 endpoint URL")
    source_bucket: str = Field(..., description="Source S3 bucket name")
    source_prefix: str = Field(..., description="Source S3 prefix/path")
    source_use_ssl: bool = Field(default=False, description="Use SSL for source S3 endpoint")
    
    # Destination S3 configuration (uses backend default if not provided)
    dest_access_key: Optional[str] = Field(None, description="Destination S3 access key (optional, uses backend default)")
    dest_secret_key: Optional[str] = Field(None, description="Destination S3 secret key (optional, uses backend default)")
    dest_s3_endpoint: Optional[str] = Field(None, description="Destination S3 endpoint (optional, uses backend default)")
    dest_bucket: Optional[str] = Field(None, description="Destination S3 bucket (optional, uses backend default)")
    dest_use_ssl: Optional[bool] = Field(None, description="Use SSL for destination S3 endpoint")
    
    # Batch sync configuration
    batch_size: float = Field(default=1.0, ge=0.1, le=60.0, description="Delay between files in seconds (rate limiting)")
    
    # Video metadata (same for all files)
    is_public: bool = Field(default=True, description="Make videos publicly accessible")
    tags: Optional[List[str]] = Field(default=None, description="Comma-separated tags")
    allowed_users: Optional[List[str]] = Field(default=None, description="Comma-separated list of allowed users")
    
    # Streaming metadata (optional)
    camera_id: Optional[str] = Field(default=None, description="Camera identifier")
    capture_type: Optional[str] = Field(default=None, description="Capture type: traffic, streets, crowds, malls")
    neighborhood: Optional[str] = Field(default=None, description="Geographic area/neighborhood")


class BatchSyncStatusResponse(BaseModel):
    """Response model for batch sync status"""
    success: bool
    status: Optional[dict] = None
    message: Optional[str] = None


class BatchSyncOperationResponse(BaseModel):
    """Response model for batch sync operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    job_id: Optional[str] = None


class BatchSyncCheckObjectsResponse(BaseModel):
    """Response model for check objects operation"""
    success: bool
    count: int = 0
    files: Optional[List[dict]] = None
    error: Optional[str] = None


@router.get("/prefill", response_model=BatchSyncConfigPrefill)
async def get_batch_sync_prefill(
    current_user: User = Depends(get_current_user)
):
    """
    Get S3 configuration for pre-filling the batch sync form
    
    Returns the S3 credentials and endpoint from backend config
    for authenticated users to pre-fill the batch sync configuration.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        BatchSyncConfigPrefill with S3 configuration
    """
    logger.info(f"[BATCH_SYNC] Prefill config requested by {current_user.username}")
    
    settings = get_settings()
    
    return BatchSyncConfigPrefill(
        s3_endpoint=settings.s3_endpoint,
        s3_access_key=settings.s3_access_key,
        s3_secret_key=settings.s3_secret_key,
        bucket_name=settings.s3_upload_bucket
    )


@router.post("/check-objects", response_model=BatchSyncCheckObjectsResponse)
async def check_objects(
    request: BatchSyncCheckObjectsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check and count MP4 files in source S3 bucket/prefix
    
    Args:
        request: Batch sync check objects configuration
        current_user: Current authenticated user
        
    Returns:
        BatchSyncCheckObjectsResponse with file count and preview
    """
    logger.info(f"[BATCH_SYNC] Check objects requested by {current_user.username}")
    logger.info(f"[BATCH_SYNC] Bucket: {request.bucket}, Prefix: {request.prefix}")
    
    try:
        payload = {
            "access_key": request.access_key,
            "secret_key": request.secret_key,
            "s3_endpoint": request.s3_endpoint,
            "bucket": request.bucket,
            "prefix": request.prefix,
            "use_ssl": request.use_ssl
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BATCH_SYNC_SERVICE_URL}/check-objects",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[BATCH_SYNC] Found {data.get('count', 0)} MP4 files")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[BATCH_SYNC] Timeout connecting to batch sync service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout connecting to batch sync service"
        )
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("error", e.response.text)
        except:
            error_detail = e.response.text
            
        logger.error(f"[BATCH_SYNC] HTTP error checking objects: {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"[BATCH_SYNC] Error checking objects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check objects: {str(e)}"
        )


@router.post("/start", response_model=BatchSyncOperationResponse)
async def start_batch_sync(
    request: BatchSyncStartRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start batch sync operation
    
    Copies MP4 files from source S3 bucket to destination S3 bucket
    using server-side copy operations.
    
    Args:
        request: Batch sync start configuration
        current_user: Current authenticated user
        
    Returns:
        BatchSyncOperationResponse indicating success or failure
    """
    logger.info(f"[BATCH_SYNC] Start requested by {current_user.username}")
    logger.info(f"[BATCH_SYNC] Source: s3://{request.source_bucket}/{request.source_prefix}")
    
    try:
        settings = get_settings()
        
        # Use backend defaults for destination if not provided
        dest_access_key = request.dest_access_key or settings.s3_access_key
        dest_secret_key = request.dest_secret_key or settings.s3_secret_key
        dest_s3_endpoint = request.dest_s3_endpoint or settings.s3_endpoint
        dest_bucket = request.dest_bucket or settings.s3_upload_bucket
        dest_use_ssl = request.dest_use_ssl if request.dest_use_ssl is not None else settings.s3_use_ssl
        
        # Prepare payload for batch sync service
        payload = {
            "username": current_user.username,
            "source_access_key": request.source_access_key,
            "source_secret_key": request.source_secret_key,
            "source_s3_endpoint": request.source_s3_endpoint,
            "source_bucket": request.source_bucket,
            "source_prefix": request.source_prefix,
            "source_use_ssl": request.source_use_ssl,
            "dest_access_key": dest_access_key,
            "dest_secret_key": dest_secret_key,
            "dest_s3_endpoint": dest_s3_endpoint,
            "dest_bucket": dest_bucket,
            "dest_use_ssl": dest_use_ssl,
            "batch_size": request.batch_size,
            "is_public": request.is_public,
            "tags": request.tags or [],
            "allowed_users": request.allowed_users or [],
            "camera_id": request.camera_id or "",
            "capture_type": request.capture_type or "",
            "neighborhood": request.neighborhood or ""
        }
        
        logger.info(f"[BATCH_SYNC] Destination: s3://{dest_bucket}")
        logger.info(f"[BATCH_SYNC] Delay between files: {request.batch_size} seconds")
        logger.info(f"[BATCH_SYNC] Metadata: camera_id={request.camera_id}, capture_type={request.capture_type}, neighborhood={request.neighborhood}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BATCH_SYNC_SERVICE_URL}/start",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[BATCH_SYNC] Started successfully for {current_user.username}, job_id={data.get('job_id')}")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[BATCH_SYNC] Timeout starting batch sync service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout starting batch sync service"
        )
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("error", e.response.text)
        except:
            error_detail = e.response.text
            
        logger.error(f"[BATCH_SYNC] HTTP error starting batch sync: {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"[BATCH_SYNC] Error starting batch sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch sync: {str(e)}"
        )


@router.get("/status", response_model=BatchSyncStatusResponse)
async def get_batch_sync_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get batch sync status for current user
    
    Returns the status of the user's active batch sync job including
    progress, completed files, failed files, etc.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        BatchSyncStatusResponse with job status
    """
    logger.info(f"[BATCH_SYNC] Status check requested by {current_user.username}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BATCH_SYNC_SERVICE_URL}/status",
                params={"username": current_user.username}
            )
            response.raise_for_status()
            
            data = response.json()
            status_info = data.get('status') or {}
            logger.info(f"[BATCH_SYNC] Status: {status_info.get('status', 'no job')}")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[BATCH_SYNC] Timeout connecting to batch sync service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout connecting to batch sync service"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"[BATCH_SYNC] HTTP error from batch sync service: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Batch sync service error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"[BATCH_SYNC] Error getting status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch sync status: {str(e)}"
        )

@router.post("/stop", response_model=BatchSyncOperationResponse)
async def stop_batch_sync(current_user: User = Depends(get_current_user)):
    """
    Stop active batch sync job for the current user
    
    Returns:
        BatchSyncOperationResponse with success status
    """
    logger.info(f"[BATCH_SYNC] Stop requested by {current_user.username}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BATCH_SYNC_SERVICE_URL}/stop",
                json={"username": current_user.username}
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[BATCH_SYNC] Stop result: {data.get('success', False)}")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[BATCH_SYNC] Timeout connecting to batch sync service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout connecting to batch sync service"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"[BATCH_SYNC] HTTP error from batch sync service: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Batch sync service error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"[BATCH_SYNC] Error stopping batch sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop batch sync: {str(e)}"
        )


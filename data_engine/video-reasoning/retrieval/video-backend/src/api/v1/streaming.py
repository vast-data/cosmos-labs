"""
Video Streaming Management API

Proxies requests to the video streaming capture service running in the same namespace.
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

from src.services.auth_service import get_current_user
from src.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Internal K8s DNS for streaming service (same namespace)
STREAMING_SERVICE_URL = "http://video-stream-capture-service:5000"

# Models
class StreamingStartRequest(BaseModel):
    """Request model for starting video capture"""
    youtube_url: str = Field(..., description="YouTube video URL to capture")
    access_key: str = Field(..., description="S3 access key")
    secret_key: str = Field(..., description="S3 secret key")
    s3_endpoint: str = Field(..., description="S3 endpoint URL")
    name: str = Field(default="capture", description="Custom prefix for video files")
    bucket_name: str = Field(..., description="S3 bucket name for storing captures")
    capture_interval: int = Field(default=10, ge=1, le=300, description="Capture interval in seconds")


class StreamingStatusResponse(BaseModel):
    """Response model for streaming status"""
    success: bool
    status: dict
    timestamp: str


class StreamingOperationResponse(BaseModel):
    """Response model for start/stop operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


@router.get("/status", response_model=StreamingStatusResponse)
async def get_streaming_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed streaming service status
    
    Proxies to the video streaming capture service to check if:
    - A capture is currently running
    - What configuration is active
    - How many temporary files exist
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        StreamingStatusResponse with detailed status
    """
    logger.info(f"[STREAMING] Status check requested by {current_user.username}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{STREAMING_SERVICE_URL}/status")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[STREAMING] Status: is_running={data.get('status', {}).get('is_running', False)}")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[STREAMING] Timeout connecting to streaming service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout connecting to streaming service"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"[STREAMING] HTTP error from streaming service: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Streaming service error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"[STREAMING] Error getting status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get streaming status: {str(e)}"
        )


@router.post("/start", response_model=StreamingOperationResponse)
async def start_streaming(
    request: StreamingStartRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start video capture from YouTube stream
    
    Initiates continuous video capture from a YouTube URL, saving segments to S3.
    
    Args:
        request: Streaming start configuration
        current_user: Current authenticated user
        
    Returns:
        StreamingOperationResponse indicating success or failure
    """
    logger.info(f"[STREAMING] Start requested by {current_user.username}")
    logger.info(f"[STREAMING] YouTube URL: {request.youtube_url}")
    logger.info(f"[STREAMING] Bucket: {request.bucket_name}, Name: {request.name}, Interval: {request.capture_interval}s")
    
    try:
        # Prepare payload for streaming service
        payload = {
            "youtube_url": request.youtube_url,
            "access_key": request.access_key,
            "secret_key": request.secret_key,
            "s3_endpoint": request.s3_endpoint,
            "name": request.name,
            "bucket_name": request.bucket_name,
            "capture_interval": request.capture_interval
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{STREAMING_SERVICE_URL}/start",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[STREAMING] Started successfully for {current_user.username}")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[STREAMING] Timeout starting streaming service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout starting streaming service"
        )
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("error", e.response.text)
        except:
            error_detail = e.response.text
            
        logger.error(f"[STREAMING] HTTP error starting stream: {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"[STREAMING] Error starting stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start streaming: {str(e)}"
        )


@router.post("/stop", response_model=StreamingOperationResponse)
async def stop_streaming(
    current_user: User = Depends(get_current_user)
):
    """
    Stop active video capture
    
    Stops the currently running video capture process and cleans up temporary files.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        StreamingOperationResponse indicating success or failure
    """
    logger.info(f"[STREAMING] Stop requested by {current_user.username}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(f"{STREAMING_SERVICE_URL}/stop")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[STREAMING] Stopped successfully for {current_user.username}")
            
            return data
            
    except httpx.TimeoutException:
        logger.error("[STREAMING] Timeout stopping streaming service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout stopping streaming service"
        )
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("error", e.response.text)
        except:
            error_detail = e.response.text
            
        logger.error(f"[STREAMING] HTTP error stopping stream: {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"[STREAMING] Error stopping stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop streaming: {str(e)}"
        )


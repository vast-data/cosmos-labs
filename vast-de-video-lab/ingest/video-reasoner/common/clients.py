import logging
import time
import tempfile
import os
import base64
from typing import Dict, Any, Optional, List
from io import BytesIO
import requests
import paramiko
import boto3
from botocore.exceptions import ClientError
from opentelemetry import trace

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("opencv-python not available. Nemotron frame extraction will fail.")

from .prompts import get_prompt_for_scenario


class S3Client:
    """S3 client for downloading videos"""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3endpoint,
            aws_access_key_id=settings.s3accesskey,
            aws_secret_access_key=settings.s3secretkey,
            verify=False
        )
    
    def download_file(self, bucket: str, key: str) -> bytes:
        """Download file from S3"""
        logging.info(f"[S3_CLIENT] Downloading s3://{bucket}/{key}")
        response = self.client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        logging.info(f"[S3_CLIENT] Downloaded {len(content)} bytes")
        return content
    
    def head_object(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get object metadata from S3"""
        logging.info(f"[S3_CLIENT] Fetching metadata for s3://{bucket}/{key}")
        response = self.client.head_object(Bucket=bucket, Key=key)
        logging.info(f"[S3_CLIENT] Retrieved metadata: {response.get('Metadata', {})}")
        return response


class CosmosReasoningClient:
    """Cosmos reasoning client for video analysis"""

    def __init__(self, settings):
        """Initialize Cosmos reasoning client"""
        self.settings = settings
        self.cosmos_url = settings.cosmos_url
        self.cosmos_ssh_host = settings.cosmos_ssh_host
        self.cosmos_upload_path = settings.cosmos_upload_path
        self.session = requests.Session()
        
        # Initialize tracer
        self.tracer = trace.get_tracer(__name__)

    def upload_video_to_cosmos_server(self, video_content: bytes, filename: str) -> str:
        """Upload video to Cosmos server via SFTP"""
        with self.tracer.start_as_current_span("Video Upload to Cosmos Server") as span:
            span.set_attributes({
                "filename": filename,
                "file_size_bytes": len(video_content),
                "cosmos_host": self.settings.cosmos_host
            })
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_file.write(video_content)
                temp_file_path = temp_file.name
            
            try:
                remote_path = f"{self.cosmos_upload_path}{filename}"
                start_time = time.time()
                
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                try:
                    try:
                        ssh_client.connect(
                            hostname=self.settings.cosmos_host,
                            username=self.settings.cosmos_username,
                            password=self.settings.cosmos_password,
                            timeout=60
                        )
                    except paramiko.AuthenticationException:
                        ssh_client.connect(
                            hostname=self.settings.cosmos_host,
                            username=self.settings.cosmos_username,
                            timeout=60
                        )
                    
                    sftp_client = ssh_client.open_sftp()
                    
                    try:
                        try:
                            sftp_client.stat(self.cosmos_upload_path)
                        except FileNotFoundError:
                            sftp_client.mkdir(self.cosmos_upload_path)
                        
                        sftp_client.put(temp_file_path, remote_path)
                        upload_time = time.time() - start_time
                        file_size_mb = len(video_content) / (1024 * 1024)
                        throughput = file_size_mb / upload_time if upload_time > 0 else 0
                        
                        span.set_attributes({
                            "upload_time_seconds": upload_time,
                            "upload_success": True
                        })
                        
                        logging.info(f"[UPLOAD] {filename} ({file_size_mb:.2f}MB) → {self.settings.cosmos_host} | {upload_time:.2f}s @ {throughput:.1f}MB/s")
                        
                        video_url = f"http://{self.settings.cosmos_host}:{self.settings.cosmos_video_port}/{filename}"
                        span.set_attributes({"video_url": video_url})
                        
                        return video_url
                        
                    finally:
                        sftp_client.close()
                        
                finally:
                    ssh_client.close()
                
            except paramiko.AuthenticationException as e:
                span.set_attributes({"upload_error": str(e)})
                raise RuntimeError(f"SSH authentication failed: {e}")
                
            except paramiko.SSHException as e:
                span.set_attributes({"upload_error": str(e)})
                raise RuntimeError(f"SSH connection failed: {e}")
                
            except Exception as e:
                span.set_attributes({"upload_error": str(e)})
                raise RuntimeError(f"Upload failed: {e}")
                
            finally:
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

    def get_cosmos_reasoning(self, video_url: str, prompt: str = "Describe the main events in this clip.") -> Dict[str, Any]:
        """Get reasoning content from Cosmos API"""
        with self.tracer.start_as_current_span("Cosmos Reasoning API Call") as span:
            span.set_attributes({
                "video_url": video_url,
                "cosmos_url": self.cosmos_url,
                "model": self.settings.cosmos_model
            })
            
            # Verify video URL is accessible
            try:
                url_test_response = self.session.head(video_url, timeout=30)
                
                if url_test_response.status_code == 200:
                    span.set_attributes({"video_url_accessible": True})
                elif url_test_response.status_code == 404:
                    raise RuntimeError(f"Video not found: {video_url}")
                else:
                    raise RuntimeError(f"Video URL returned status {url_test_response.status_code}")
                    
            except requests.exceptions.ConnectionError as e:
                raise RuntimeError(f"Cannot connect to video server: {e}")
            except requests.exceptions.Timeout as e:
                raise RuntimeError(f"Timeout accessing video URL: {e}")
            
            payload = {
                "model": self.settings.cosmos_model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "video_url", "video_url": {"url": video_url}}
                    ],
                }],
                "max_tokens": 400,
            }
            
            # Retry with exponential backoff
            max_retries = 3
            retry_delay = 2
            
            start_time = time.time()
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    
                    response = self.session.post(self.cosmos_url, json=payload, timeout=600)
                    break
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Request failed after {max_retries} attempts: {e}")
            
            reasoning_time = time.time() - start_time
            span.set_attributes({
                "reasoning_time_seconds": reasoning_time,
                "http_status_code": response.status_code
            })
            
            if response.status_code != 200:
                raise RuntimeError(f"Cosmos API error ({response.status_code}): {response.text}")
            
            response_data = response.json()
            
            choices = response_data.get("choices", [])
            if not choices:
                raise RuntimeError("No choices in Cosmos API response")
            
            reasoning_content = choices[0].get("message", {}).get("content", "")
            usage = response_data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            span.set_attributes({
                "reasoning_content_length": len(reasoning_content),
                "tokens_used": tokens_used
            })
            
            logging.info(f"[REASONING] {self.settings.cosmos_model} | {len(reasoning_content)} chars, {tokens_used} tokens | {reasoning_time:.2f}s")
            
            return {
                "reasoning_content": reasoning_content,
                "tokens_used": tokens_used,
                "processing_time": reasoning_time,
                "cosmos_model": self.settings.cosmos_model,
                "raw_response": response_data
            }

    def analyze_video(self, video_content: bytes, filename: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Complete video analysis pipeline using Cosmos reasoning."""
        if prompt is None:
            prompt = get_prompt_for_scenario(self.settings.scenario)
        
        with self.tracer.start_as_current_span("Complete Video Analysis") as span:
            span.set_attributes({
                "filename": filename,
                "file_size_bytes": len(video_content),
                "scenario": self.settings.scenario
            })
            
            # Check video size limit
            max_size_bytes = self.settings.max_video_size_mb * 1024 * 1024
            if len(video_content) > max_size_bytes:
                raise ValueError(f"Video too large: {len(video_content)} > {max_size_bytes} bytes")
            
            video_url = self.upload_video_to_cosmos_server(video_content, filename)
            reasoning_result = self.get_cosmos_reasoning(video_url, prompt)
            
            result = {
                "filename": filename,
                "reasoning_content": reasoning_result["reasoning_content"],
                "cosmos_model": reasoning_result["cosmos_model"],
                "tokens_used": reasoning_result["tokens_used"],
                "processing_time": reasoning_result["processing_time"],
                "video_url": video_url
            }
            
            span.set_attributes({
                "reasoning_content_length": len(result["reasoning_content"]),
                "total_tokens": result["tokens_used"],
                "total_processing_time": result["processing_time"]
            })
            
            return result

    def close(self):
        """Close HTTP session"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def extract_frames_from_video(video_bytes: bytes, num_frames: int = 1, frame_interval: Optional[float] = None) -> List[bytes]:
    """
    Extract multiple frames from video bytes and return as PNG image bytes.
    
    Args:
        video_bytes: Video file content as bytes
        num_frames: Number of frames to extract (default: 1)
        frame_interval: Interval in seconds between frames (None = evenly spaced)
    
    Returns:
        List of PNG image bytes
    """
    if not CV2_AVAILABLE:
        raise ImportError("opencv-python is required for video frame extraction. Install with: pip install opencv-python")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name
    
    try:
        cap = cv2.VideoCapture(tmp_path)
        
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        duration = total_frames / fps if total_frames > 0 else 0
        
        if total_frames == 0:
            raise ValueError("Video has no frames")
        
        # Determine which frames to extract
        if num_frames == 1:
            frame_indices = [0]
        elif frame_interval is not None:
            # Extract frames at specific time intervals
            frame_indices = []
            current_time = 0
            while current_time < duration and len(frame_indices) < num_frames:
                frame_idx = int(current_time * fps)
                if frame_idx < total_frames:
                    frame_indices.append(frame_idx)
                current_time += frame_interval
        else:
            # Extract evenly spaced frames
            if num_frames >= total_frames:
                frame_indices = list(range(total_frames))
            else:
                step = total_frames / num_frames
                frame_indices = [int(i * step) for i in range(num_frames)]
        
        # Extract frames
        frames = []
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                _, buffer = cv2.imencode('.png', frame)
                frames.append(buffer.tobytes())
        
        cap.release()
        
        if not frames:
            raise ValueError("Could not extract any frames from video")
        
        return frames
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


class NemotronReasoningClient:
    """Nemotron reasoning client for video analysis using NVIDIA Build Cloud API"""

    def __init__(self, settings):
        """Initialize Nemotron reasoning client"""
        self.settings = settings
        self.api_key = settings.nvidia_api_key
        self.model = settings.nemotron_model
        self.endpoint_base = settings.nemotron_endpoint.rstrip('/')
        if not self.endpoint_base.endswith('/v1'):
            self.endpoint_base = f"{self.endpoint_base}/v1"
        self.endpoint_url = f"{self.endpoint_base}/chat/completions"
        self.session = requests.Session()
        
        # Initialize tracer
        self.tracer = trace.get_tracer(__name__)
        
        if not self.api_key:
            raise ValueError("nvidia_api_key is required for Nemotron provider")

    def get_nemotron_reasoning(self, video_content: bytes, prompt: str = "Describe the main events in this clip.") -> Dict[str, Any]:
        """Get reasoning content from Nemotron API using extracted frames"""
        with self.tracer.start_as_current_span("Nemotron Reasoning API Call") as span:
            span.set_attributes({
                "model": self.model,
                "endpoint": self.endpoint_url,
                "num_frames": self.settings.nemotron_num_frames
            })
            
            # Extract frames from video
            logging.info(f"[NEMOTRON] Extracting {self.settings.nemotron_num_frames} frame(s) from video...")
            start_extract = time.time()
            
            try:
                frame_png_bytes_list = extract_frames_from_video(
                    video_content,
                    num_frames=self.settings.nemotron_num_frames,
                    frame_interval=self.settings.nemotron_frame_interval
                )
                extract_time = time.time() - start_extract
                total_size_kb = sum(len(f) for f in frame_png_bytes_list) / 1024
                logging.info(f"[NEMOTRON] Extracted {len(frame_png_bytes_list)} frame(s) ({total_size_kb:.1f} KB) in {extract_time:.2f}s")
                
                span.set_attributes({
                    "frames_extracted": len(frame_png_bytes_list),
                    "extract_time_seconds": extract_time,
                    "total_frames_size_kb": total_size_kb
                })
            except Exception as e:
                span.set_attributes({"extract_error": str(e)})
                raise RuntimeError(f"Failed to extract frames from video: {e}")
            
            # Prepare content with text prompt and images
            content = [
                {"type": "text", "text": prompt}
            ]
            
            # Add all extracted frames as images
            for frame_bytes in frame_png_bytes_list:
                frame_base64 = base64.b64encode(frame_bytes).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{frame_base64}"}
                })
            
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": content
                }],
                "max_tokens": self.settings.nemotron_max_tokens,
                "temperature": self.settings.nemotron_temperature,
                "top_p": self.settings.nemotron_top_p
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Retry with exponential backoff
            max_retries = 3
            retry_delay = 2
            
            start_time = time.time()
            response = None
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        logging.info(f"[NEMOTRON] Retry attempt {attempt + 1}/{max_retries}...")
                    
                    response = self.session.post(
                        self.endpoint_url,
                        headers=headers,
                        json=payload,
                        timeout=600
                    )
                    break
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    if attempt == max_retries - 1:
                        span.set_attributes({"request_error": str(e)})
                        raise RuntimeError(f"Request failed after {max_retries} attempts: {e}")
            
            reasoning_time = time.time() - start_time
            span.set_attributes({
                "reasoning_time_seconds": reasoning_time,
                "http_status_code": response.status_code if response else 0
            })
            
            if not response or response.status_code != 200:
                error_text = response.text if response else "No response"
                span.set_attributes({"api_error": error_text})
                raise RuntimeError(f"Nemotron API error ({response.status_code if response else 'unknown'}): {error_text}")
            
            response_data = response.json()
            
            choices = response_data.get("choices", [])
            if not choices:
                raise RuntimeError("No choices in Nemotron API response")
            
            reasoning_content = choices[0].get("message", {}).get("content", "")
            usage = response_data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0) if usage else 0
            
            span.set_attributes({
                "reasoning_content_length": len(reasoning_content),
                "tokens_used": tokens_used
            })
            
            logging.info(f"[NEMOTRON] {self.model} | {len(reasoning_content)} chars, {tokens_used} tokens | {reasoning_time:.2f}s")
            
            return {
                "reasoning_content": reasoning_content,
                "tokens_used": tokens_used,
                "processing_time": reasoning_time,
                "cosmos_model": self.model,  # Using same field name for compatibility
                "raw_response": response_data
            }

    def analyze_video(self, video_content: bytes, filename: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Complete video analysis pipeline using Nemotron reasoning."""
        if prompt is None:
            prompt = get_prompt_for_scenario(self.settings.scenario)
        
        with self.tracer.start_as_current_span("Complete Video Analysis (Nemotron)") as span:
            span.set_attributes({
                "filename": filename,
                "file_size_bytes": len(video_content),
                "scenario": self.settings.scenario,
                "num_frames": self.settings.nemotron_num_frames
            })
            
            # Check video size limit
            max_size_bytes = self.settings.max_video_size_mb * 1024 * 1024
            if len(video_content) > max_size_bytes:
                raise ValueError(f"Video too large: {len(video_content)} > {max_size_bytes} bytes")
            
            reasoning_result = self.get_nemotron_reasoning(video_content, prompt)
            
            result = {
                "filename": filename,
                "reasoning_content": reasoning_result["reasoning_content"],
                "cosmos_model": reasoning_result["cosmos_model"],
                "tokens_used": reasoning_result["tokens_used"],
                "processing_time": reasoning_result["processing_time"],
                "video_url": "",  # Not used for Nemotron
            }
            
            span.set_attributes({
                "reasoning_content_length": len(result["reasoning_content"]),
                "total_tokens": result["tokens_used"],
                "total_processing_time": result["processing_time"]
            })
            
            return result

    def close(self):
        """Close HTTP session"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


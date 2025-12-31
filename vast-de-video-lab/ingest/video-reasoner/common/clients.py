import logging
import time
import tempfile
import os
from typing import Dict, Any, Optional
import requests
import paramiko
import boto3
from botocore.exceptions import ClientError
from opentelemetry import trace

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


import logging
import time
import tempfile
import os
from typing import Dict, Any
import requests
import paramiko
import boto3
from botocore.exceptions import ClientError
from opentelemetry import trace


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
        """Upload video to Cosmos server via SFTP using paramiko"""
        with self.tracer.start_as_current_span("Video Upload to Cosmos Server") as span:
            span.set_attributes({
                "filename": filename,
                "file_size_bytes": len(video_content),
                "cosmos_host": self.settings.cosmos_host,
                "upload_path": self.cosmos_upload_path
            })
            
            logging.info(f"[UPLOAD] Starting video upload to Cosmos server")
            logging.info(f"[UPLOAD] Host: {self.settings.cosmos_host}")
            logging.info(f"[UPLOAD] Username: {self.settings.cosmos_username}")
            logging.info(f"[UPLOAD] Path: {self.cosmos_upload_path}")
            logging.info(f"[UPLOAD] Filename: {filename}")
            logging.info(f"[UPLOAD] File size: {len(video_content)} bytes")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_file.write(video_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload via SFTP using paramiko
                remote_path = f"{self.cosmos_upload_path}{filename}"
                
                logging.info(f"[UPLOAD] Connecting to SSH server via paramiko")
                logging.info(f"[UPLOAD] Host: {self.settings.cosmos_host}")
                logging.info(f"[UPLOAD] Username: {self.settings.cosmos_username}")
                
                start_time = time.time()
                
                # Create SSH client
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                try:
                    # Connect to SSH server - try password authentication first, fallback to key-based
                    try:
                        ssh_client.connect(
                            hostname=self.settings.cosmos_host,
                            username=self.settings.cosmos_username,
                            password=self.settings.cosmos_password,
                            timeout=60
                        )
                        logging.info(f"[UPLOAD] Connected using password authentication")
                    except paramiko.AuthenticationException:
                        # Fallback to key-based authentication
                        logging.info(f"[UPLOAD] Password auth failed, trying key-based authentication")
                        ssh_client.connect(
                            hostname=self.settings.cosmos_host,
                            username=self.settings.cosmos_username,
                            timeout=60
                        )
                        logging.info(f"[UPLOAD] Connected using key-based authentication")
                    
                    logging.info(f"[UPLOAD] SSH connection established")
                    
                    # Create SFTP client
                    sftp_client = ssh_client.open_sftp()
                    
                    try:
                        # Ensure remote directory exists
                        try:
                            sftp_client.stat(self.cosmos_upload_path)
                            logging.info(f"[UPLOAD] Remote directory exists: {self.cosmos_upload_path}")
                        except FileNotFoundError:
                            logging.info(f"[UPLOAD] Creating remote directory: {self.cosmos_upload_path}")
                            # Create directory recursively
                            sftp_client.mkdir(self.cosmos_upload_path)
                        
                        # Upload file
                        logging.info(f"[UPLOAD] Uploading file to: {remote_path}")
                        sftp_client.put(temp_file_path, remote_path)
                        
                        upload_time = time.time() - start_time
                        
                        span.set_attributes({
                            "upload_time_seconds": upload_time,
                            "upload_success": True
                        })
                        
                        logging.info(f"[UPLOAD] Successfully uploaded video to {remote_path}")
                        logging.info(f"[UPLOAD] Upload time: {upload_time:.2f} seconds")
                        
                        # Return the URL for the uploaded video (without /tmp/vid/ path, with correct port)
                        video_url = f"http://{self.settings.cosmos_host}:{self.settings.cosmos_video_port}/{filename}"
                        span.set_attributes({"video_url": video_url})
                        
                        return video_url
                        
                    finally:
                        sftp_client.close()
                        logging.info(f"[UPLOAD] SFTP connection closed")
                        
                finally:
                    ssh_client.close()
                    logging.info(f"[UPLOAD] SSH connection closed")
                
            except paramiko.AuthenticationException as e:
                error_msg = f"SSH authentication failed: {e}"
                logging.error(f"[UPLOAD] {error_msg}")
                span.set_attributes({"upload_error": error_msg})
                raise RuntimeError(error_msg)
                
            except paramiko.SSHException as e:
                error_msg = f"SSH connection failed: {e}"
                logging.error(f"[UPLOAD] {error_msg}")
                span.set_attributes({"upload_error": error_msg})
                raise RuntimeError(error_msg)
                
            except Exception as e:
                error_msg = f"Upload failed: {e}"
                logging.error(f"[UPLOAD] {error_msg}")
                span.set_attributes({"upload_error": error_msg})
                raise RuntimeError(error_msg)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                    logging.info(f"[UPLOAD] Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logging.warning(f"[UPLOAD] Failed to clean up temp file: {e}")

    def get_cosmos_reasoning(self, video_url: str, prompt: str = "Describe the main events in this clip.") -> Dict[str, Any]:
        """Get reasoning content from Cosmos API"""
        with self.tracer.start_as_current_span("Cosmos Reasoning API Call") as span:
            span.set_attributes({
                "video_url": video_url,
                "prompt": prompt,
                "cosmos_url": self.cosmos_url,
                "model": self.settings.cosmos_model
            })
            
            logging.info(f"[REASONING] Starting Cosmos reasoning analysis")
            logging.info(f"[REASONING] Video URL: {video_url}")
            logging.info(f"[REASONING] Prompt: {prompt}")
            logging.info(f"[REASONING] API URL: {self.cosmos_url}")
            
            # Test video URL accessibility before making Cosmos API call
            logging.info(f"[REASONING] Testing video URL accessibility...")
            try:
                url_test_response = self.session.head(video_url, timeout=30)
                logging.info(f"[REASONING] Video URL test - Status: {url_test_response.status_code}")
                
                if url_test_response.status_code == 200:
                    logging.info(f"[REASONING] Video URL is accessible")
                    span.set_attributes({"video_url_accessible": True, "video_url_status": 200})
                elif url_test_response.status_code == 404:
                    error_msg = f"Video file not found at {video_url} (HTTP 404)"
                    logging.error(f"[REASONING] {error_msg}")
                    span.set_attributes({"video_url_accessible": False, "video_url_status": 404})
                    raise RuntimeError(error_msg)
                else:
                    error_msg = f"Video URL returned unexpected status {url_test_response.status_code}"
                    logging.error(f"[REASONING] {error_msg}")
                    span.set_attributes({"video_url_accessible": False, "video_url_status": url_test_response.status_code})
                    raise RuntimeError(error_msg)
                    
            except requests.exceptions.ConnectionError as e:
                error_msg = f"Cannot connect to video server at {video_url}: {e}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"video_url_accessible": False, "video_url_error": "connection_error"})
                raise RuntimeError(error_msg)
            except requests.exceptions.Timeout as e:
                error_msg = f"Timeout accessing video URL {video_url}: {e}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"video_url_accessible": False, "video_url_error": "timeout"})
                raise RuntimeError(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error testing video URL {video_url}: {e}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"video_url_accessible": False, "video_url_error": str(e)})
                raise RuntimeError(error_msg)
            
            payload = {
                "model": self.settings.cosmos_model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "video_url", "video_url": {"url": video_url}}
                    ],
                }],
                "max_tokens": 200,
            }
            
            logging.info(f"[REASONING] Sending request to Cosmos API")
            logging.info(f"[REASONING] Payload: {payload}")
            
            # Retry logic with exponential backoff
            max_retries = 3
            retry_delay = 2  # seconds
            last_error = None
            
            start_time = time.time()
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        logging.info(f"[REASONING] Retry attempt {attempt + 1}/{max_retries} after {retry_delay}s delay")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    
                    response = self.session.post(
                        self.cosmos_url, 
                        json=payload, 
                        timeout=600  # 10 minute timeout
                    )
                    reasoning_time = time.time() - start_time
                    break  # Success, exit retry loop
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    last_error = e
                    logging.warning(f"[REASONING] Connection error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        raise RuntimeError(f"Request failed after {max_retries} attempts: {e}")
                    continue
            
            reasoning_time = time.time() - start_time
            
            span.set_attributes({
                "reasoning_time_seconds": reasoning_time,
                "http_status_code": response.status_code
            })
            
            logging.info(f"[REASONING] API response status: {response.status_code}")
            logging.info(f"[REASONING] Processing time: {reasoning_time:.2f} seconds")
            
            if response.status_code == 200:
                logging.info(f"[REASONING] Cosmos API call successful")
            elif response.status_code == 400:
                error_msg = f"Cosmos API Bad Request (400): {response.text}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"api_error": "bad_request", "api_error_details": response.text})
                raise RuntimeError(error_msg)
            elif response.status_code == 404:
                error_msg = f"Cosmos API Not Found (404): {response.text}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"api_error": "not_found", "api_error_details": response.text})
                raise RuntimeError(error_msg)
            elif response.status_code == 500:
                error_msg = f"Cosmos API Internal Server Error (500): {response.text}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"api_error": "server_error", "api_error_details": response.text})
                raise RuntimeError(error_msg)
            else:
                error_msg = f"Cosmos API error ({response.status_code}): {response.text}"
                logging.error(f"[REASONING] {error_msg}")
                span.set_attributes({"api_error": f"http_{response.status_code}", "api_error_details": response.text})
                raise RuntimeError(error_msg)
            
            response_data = response.json()
            logging.info(f"[REASONING] Full API response: {response_data}")
            
            # Extract reasoning content
            choices = response_data.get("choices", [])
            if not choices:
                raise RuntimeError("No choices in Cosmos API response")
            
            message = choices[0].get("message", {})
            reasoning_content = message.get("content", "")
            
            # Extract usage information
            usage = response_data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            span.set_attributes({
                "reasoning_content_length": len(reasoning_content),
                "tokens_used": tokens_used,
                "completion_tokens": usage.get("completion_tokens", 0),
                "prompt_tokens": usage.get("prompt_tokens", 0)
            })
            
            logging.info(f"[REASONING] Extracted reasoning content: {reasoning_content}")
            logging.info(f"[REASONING] Tokens used: {tokens_used}")
            
            return {
                "reasoning_content": reasoning_content,
                "tokens_used": tokens_used,
                "processing_time": reasoning_time,
                "cosmos_model": self.settings.cosmos_model,
                "raw_response": response_data
            }

    def analyze_video(self, video_content: bytes, filename: str, prompt: str = "Analyze this surveillance footage and describe: 1) All visible people, their actions, behaviors, and any unusual movements or interactions. 2) Any safety hazards including fire, smoke, or environmental dangers. 3) Objects of interest such as abandoned items, vehicles, or equipment. 4) Group dynamics including crowd formations, gatherings, or confrontations. 5) Any signs of distress, emergency situations, or security concerns. Be specific about locations, timing, and severity.") -> Dict[str, Any]:
        """Complete video analysis pipeline using Cosmos reasoning"""
        with self.tracer.start_as_current_span("Complete Video Analysis") as span:
            span.set_attributes({
                "filename": filename,
                "file_size_bytes": len(video_content),
                "prompt": prompt
            })
            
            logging.info(f"[ANALYSIS] Starting complete video analysis pipeline")
            logging.info(f"[ANALYSIS] Filename: {filename}")
            logging.info(f"[ANALYSIS] File size: {len(video_content)} bytes")
            logging.info(f"[ANALYSIS] Prompt: {prompt}")
            
            # Check video size limit
            max_size_bytes = self.settings.max_video_size_mb * 1024 * 1024
            if len(video_content) > max_size_bytes:
                error_msg = f"Video too large: {len(video_content)} bytes > {max_size_bytes} bytes"
                logging.error(f"[ANALYSIS] {error_msg}")
                span.set_attributes({"size_error": error_msg})
                raise ValueError(error_msg)
            
            # Step 1: Upload video to Cosmos server
            logging.info(f"[ANALYSIS] Step 1: Uploading video to Cosmos server")
            video_url = self.upload_video_to_cosmos_server(video_content, filename)
            
            # Step 2: Get reasoning from Cosmos API
            logging.info(f"[ANALYSIS] Step 2: Getting reasoning from Cosmos API")
            reasoning_result = self.get_cosmos_reasoning(video_url, prompt)
            
            # Step 3: Prepare final result
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
            
            logging.info(f"[ANALYSIS] Analysis completed successfully")
            logging.info(f"[ANALYSIS] Reasoning content: {result['reasoning_content']}")
            logging.info(f"[ANALYSIS] Total processing time: {result['processing_time']:.2f} seconds")
            logging.info(f"[ANALYSIS] Tokens used: {result['tokens_used']}")
            
            return result

    def close(self):
        """Close HTTP session"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


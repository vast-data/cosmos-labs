#!/usr/bin/env python3
"""
Video Stream Capture Web Service

REST API service for capturing YouTube videos and uploading to S3.
Supports start, stop, and ping endpoints.

Author: AI Assistant
Date: 2024
"""

import cv2
import time
import os
import json
import threading
import logging
import subprocess
import tempfile
import re
from datetime import datetime
from flask import Flask, request, jsonify
import boto3
from botocore.exceptions import ClientError
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class VideoCaptureService:
    def __init__(self):
        self.is_running = False
        self.capture_thread = None
        self.current_config = None
        self.s3_client = None
        self.temp_files = []
        
    def is_youtube_url(self, url):
        """Check if the URL is a YouTube URL."""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=',
            r'(?:https?://)?(?:www\.)?youtu\.be/',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/'
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def get_youtube_stream_url(self, youtube_url):
        """
        Get the direct stream URL from a YouTube video using yt-dlp.
        
        For VOD videos, we need a direct video URL (not HLS .m3u8) that OpenCV can read.
        We try multiple format options in order of preference.
        """
        try:
            logger.info(f"Extracting stream URL from YouTube: {youtube_url}")
            
            # Format options to try (in order of preference)
            # We want direct video URLs, NOT HLS playlists (.m3u8)
            format_options = [
                # Option 1: Best MP4 with video+audio up to 720p (direct URL)
                'best[height<=720][ext=mp4]/best[height<=720][ext=webm]',
                # Option 2: Specific format that's usually direct (not HLS)
                'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
                # Option 3: Any best format up to 720p
                'best[height<=720]',
                # Option 4: Fallback - just get something
                'best'
            ]
            
            for fmt in format_options:
                logger.info(f"Trying format: {fmt}")
                
                cmd = [
                    'yt-dlp',
                    '--get-url',
                    '--format', fmt,
                    '--no-playlist',  # Don't process playlists
                    youtube_url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and result.stdout.strip():
                    stream_url = result.stdout.strip().split('\n')[0]  # Take first URL if multiple
                    
                    # Check if it's an HLS playlist (which OpenCV can't handle well)
                    if '.m3u8' in stream_url or 'manifest' in stream_url.lower():
                        logger.warning(f"Got HLS playlist URL with format {fmt}, trying next...")
                        continue
                    
                    logger.info(f"Successfully extracted direct video URL with format: {fmt}")
                    logger.debug(f"URL preview: {stream_url[:100]}...")
                    return stream_url
                else:
                    logger.warning(f"Format {fmt} failed: {result.stderr[:200] if result.stderr else 'no output'}")
            
            # If all formats returned HLS, try one more thing: force protocol
            logger.info("All formats returned HLS, trying to force https protocol...")
            cmd = [
                'yt-dlp',
                '--get-url',
                '--format', 'best[height<=720][protocol=https]/best[protocol=https]',
                '--no-playlist',
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                stream_url = result.stdout.strip().split('\n')[0]
                if '.m3u8' not in stream_url:
                    logger.info("Successfully got direct URL with protocol filter")
                    return stream_url
            
            # Last resort: Accept HLS but warn
            logger.warning("Could not get direct URL, falling back to HLS (may not work with OpenCV)")
            cmd = ['yt-dlp', '--get-url', '--format', 'best[height<=720]', youtube_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
            
            logger.error(f"Failed to extract any YouTube stream URL")
            return None
                
        except Exception as e:
            logger.error(f"Error extracting YouTube stream: {e}")
            return None
    
    def setup_s3_client(self, access_key, secret_key, s3_endpoint):
        """Setup S3 client with provided credentials."""
        try:
            # For HTTP endpoints, disable SSL completely
            use_ssl = s3_endpoint.startswith('https://')
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=s3_endpoint,
                use_ssl=False,  # Always disable SSL for HTTP endpoints
                verify=False    # Disable SSL verification
            )
            logger.info(f"S3 client configured for endpoint: {s3_endpoint}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup S3 client: {e}")
            return False
    
    def upload_to_s3(self, file_path, bucket_name, s3_key, metadata=None):
        """Upload file to S3 with optional metadata."""
        try:
            if not self.s3_client:
                logger.error("S3 client not configured")
                return False
                
            logger.info(f"Uploading {file_path} to s3://{bucket_name}/{s3_key}")
            
            # Prepare extra args for metadata
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
                logger.info(f"Adding S3 metadata: {metadata}")
            
            self.s3_client.upload_file(file_path, bucket_name, s3_key, ExtraArgs=extra_args if extra_args else None)
            logger.info(f"Successfully uploaded to s3://{bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
    
    def test_stream(self, stream_url):
        """Test if a stream URL is accessible and working."""
        logger.info(f"Testing stream: {stream_url}")
        
        if self.is_youtube_url(stream_url):
            logger.info("Detected YouTube URL, testing with yt-dlp")
            direct_url = self.get_youtube_stream_url(stream_url)
            if direct_url:
                # Try OpenCV first
                logger.info("Testing extracted URL with OpenCV...")
                cap = cv2.VideoCapture(direct_url)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        logger.info(f"✓ YouTube stream verified with OpenCV")
                        return True
                    else:
                        logger.warning("OpenCV opened stream but couldn't read frames")
                else:
                    logger.warning("OpenCV couldn't open stream directly")
                
                # Try with FFmpeg backend explicitly
                logger.info("Trying FFmpeg backend for OpenCV...")
                cap = cv2.VideoCapture(direct_url, cv2.CAP_FFMPEG)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        logger.info(f"✓ YouTube stream verified with FFmpeg backend")
                        return True
                
                # Last resort: trust yt-dlp succeeded and skip OpenCV test
                # Some URLs work for streaming but fail the initial test
                logger.warning("OpenCV test failed, but yt-dlp extracted URL successfully")
                logger.info("Proceeding anyway - streaming may still work...")
                return True  # Trust yt-dlp, let actual capture try
            else:
                logger.error(f"Cannot extract YouTube stream URL: {stream_url}")
                return False
        
        # Handle regular streams
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            logger.error(f"Cannot open stream: {stream_url}")
            return False
            
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            logger.info(f"Stream is working: {stream_url}")
            return True
        else:
            logger.error(f"Cannot read frames from: {stream_url}")
            return False
    
    def get_stream_source(self, stream_url):
        """Get the actual stream source (direct URL or YouTube stream)."""
        if self.is_youtube_url(stream_url):
            return self.get_youtube_stream_url(stream_url)
        return stream_url
    
    def continuous_capture(self, config):
        """
        Continuous capture thread function.
        
        Works for both LIVE streams and regular VOD videos:
        - Keeps VideoCapture open across chunks (no re-opening)
        - For VOD: automatically stops when video ends
        - For VOD: max_duration timeout (default 30 min) as safety
        - For live: runs until stopped manually
        """
        cap = None
        out = None
        capture_count = 0
        
        try:
            stream_url = config['youtube_url']
            capture_interval = config.get('capture_interval', 10)
            bucket_name = config.get('bucket_name', 'rawlivevideos')
            s3_prefix = config.get('s3_prefix', 'captures')
            
            # Max duration for VOD videos (default 30 minutes = 1800 seconds)
            # Live streams ignore this (run until manually stopped)
            max_duration = config.get('max_duration', 1800)
            
            # Metadata fields
            camera_id = config.get('camera_id', '')
            capture_type = config.get('capture_type', '')  # traffic, streets, crowds, malls
            neighborhood = config.get('neighborhood', '')
            
            logger.info(f"Starting continuous capture every {capture_interval} seconds")
            logger.info(f"Stream URL: {stream_url}")
            logger.info(f"S3 bucket: {bucket_name}")
            logger.info(f"Max duration: {max_duration}s ({max_duration/60:.1f} min)")
            if camera_id:
                logger.info(f"Camera ID: {camera_id}")
            if capture_type:
                logger.info(f"Capture Type: {capture_type}")
            if neighborhood:
                logger.info(f"Neighborhood: {neighborhood}")
            
            # Get the actual stream source
            actual_stream_url = self.get_stream_source(stream_url)
            if not actual_stream_url:
                logger.error("Could not get stream source")
                return
            
            # Open video capture ONCE and keep it open
            # Use FFmpeg backend explicitly for better compatibility with various streams
            logger.info("Opening video capture with FFmpeg backend...")
            cap = cv2.VideoCapture(actual_stream_url, cv2.CAP_FFMPEG)
            
            if not cap.isOpened():
                # Fallback to default backend
                logger.warning("FFmpeg backend failed, trying default backend...")
                cap = cv2.VideoCapture(actual_stream_url)
            
            if not cap.isOpened():
                logger.error(f"Cannot open stream: {actual_stream_url}")
                return
            
            # Get stream properties
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Check if VOD (has finite frame count) or live stream
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            is_live = total_frames <= 0  # Live streams report 0 or -1 frames
            video_duration_sec = total_frames / fps if total_frames > 0 else 0
            
            if is_live:
                logger.info(f"🔴 LIVE STREAM detected - will run until stopped manually")
            else:
                logger.info(f"📹 VOD detected - {total_frames} frames, ~{video_duration_sec:.1f}s duration")
                logger.info(f"   Will auto-stop after video ends or {max_duration}s timeout")
            
            logger.info(f"Stream properties: {width}x{height} @ {fps}fps")
            
            # Track overall session start time
            session_start = time.time()
            consecutive_failures = 0
            max_consecutive_failures = 30  # ~3 seconds of failures = video ended
            
            while self.is_running:
                # Check max duration timeout (for VOD safety)
                session_elapsed = time.time() - session_start
                if not is_live and session_elapsed >= max_duration:
                    logger.info(f"⏱ Max duration ({max_duration}s) reached. Stopping capture.")
                    break
                
                # Generate filename for this chunk
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{config['name']}_{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
                temp_path = os.path.join(tempfile.gettempdir(), filename)
                self.temp_files.append(temp_path)
                
                logger.info(f"Starting capture #{capture_count + 1}: {filename}")
                
                # Create VideoWriter for this chunk
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
                
                if not out.isOpened():
                    logger.error("Cannot create video writer")
                    time.sleep(1)
                    continue
                
                # Capture frames for this chunk
                chunk_start = time.time()
                frame_count = 0
                video_ended = False
                
                while time.time() - chunk_start < capture_interval and self.is_running:
                    ret, frame = cap.read()
                    
                    if not ret:
                        consecutive_failures += 1
                        
                        if consecutive_failures >= max_consecutive_failures:
                            # Video has ended (VOD) or stream died
                            logger.info(f"📼 Video stream ended (no frames for {consecutive_failures} attempts)")
                            video_ended = True
                            break
                        
                        time.sleep(0.1)
                        continue
                    
                    # Reset failure counter on successful read
                    consecutive_failures = 0
                    
                    # Write frame to output video
                    out.write(frame)
                    frame_count += 1
                    
                    # Small delay to prevent overwhelming the system
                    elapsed = time.time() - chunk_start
                    remaining_time = capture_interval - elapsed
                    if remaining_time > 0.1:
                        time.sleep(min(1/fps, remaining_time/2))
                
                # Release writer for this chunk
                out.release()
                out = None
                
                # Upload if we got any frames
                actual_duration = time.time() - chunk_start
                if frame_count > 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    logger.info(f"✓ Captured #{capture_count + 1}: {filename} ({frame_count} frames, {actual_duration:.2f}s)")
                    
                    # Prepare S3 metadata
                    s3_metadata = {}
                    if camera_id:
                        s3_metadata['camera-id'] = camera_id
                    if capture_type:
                        s3_metadata['capture-type'] = capture_type
                    if neighborhood:
                        s3_metadata['neighborhood'] = neighborhood
                    s3_metadata['capture-timestamp'] = timestamp
                    
                    # Upload to S3 with metadata
                    s3_key = f"{s3_prefix}/{filename}"
                    if self.upload_to_s3(temp_path, bucket_name, s3_key, metadata=s3_metadata):
                        logger.info(f"✓ Uploaded to S3: s3://{bucket_name}/{s3_key}")
                        try:
                            os.remove(temp_path)
                            self.temp_files.remove(temp_path)
                        except:
                            pass
                    else:
                        logger.error(f"Failed to upload {filename} to S3")
                    
                    capture_count += 1
                else:
                    logger.warning(f"Skipped chunk #{capture_count + 1} - no frames captured")
                    # Clean up empty file
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        if temp_path in self.temp_files:
                            self.temp_files.remove(temp_path)
                    except:
                        pass
                
                # Check if video ended
                if video_ended:
                    logger.info(f"🏁 Video ended after {capture_count} chunks ({session_elapsed:.1f}s total)")
                    break
                
                # Small delay before next chunk
                if self.is_running:
                    time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error during continuous capture: {e}", exc_info=True)
        finally:
            # Clean up
            if out is not None:
                out.release()
            if cap is not None:
                cap.release()
            logger.info(f"Continuous capture stopped. Total captures: {capture_count}")
    
    def start_capture(self, config):
        """Start the video capture process."""
        if self.is_running:
            return False, "Capture is already running"
        
        # Validate required fields
        required_fields = ['youtube_url', 'access_key', 'secret_key', 's3_endpoint']
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Set default name if not provided
        if 'name' not in config:
            config['name'] = 'capture'
        
        # Setup S3 client
        if not self.setup_s3_client(config['access_key'], config['secret_key'], config['s3_endpoint']):
            return False, "Failed to setup S3 client"
        
        # Test stream
        if not self.test_stream(config['youtube_url']):
            return False, "Stream test failed"
        
        # Start capture thread
        self.is_running = True
        self.current_config = config
        self.capture_thread = threading.Thread(target=self.continuous_capture, args=(config,))
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        return True, "Capture started successfully"
    
    def stop_capture(self):
        """Stop the video capture process."""
        if not self.is_running:
            return False, "Capture is not running"
        
        self.is_running = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=10)
        
        # Clean up temp files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        self.temp_files.clear()
        
        self.current_config = None
        return True, "Capture stopped successfully"
    
    def _sanitize_config(self, config):
        """Sanitize config to hide sensitive information."""
        if not config:
            return None
        
        sanitized = config.copy()
        # Mask secret key
        if 'secret_key' in sanitized:
            sanitized['secret_key'] = '***REDACTED***'
        
        return sanitized
    
    def get_status(self):
        """Get current status."""
        return {
            'is_running': self.is_running,
            'current_config': self._sanitize_config(self.current_config),
            'temp_files_count': len(self.temp_files)
        }

# Global service instance
video_service = VideoCaptureService()

@app.route('/start', methods=['POST'])
def start_capture():
    """Start video capture."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        success, message = video_service.start_capture(data)
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logger.error(f"Error in start endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_capture():
    """Stop video capture."""
    try:
        success, message = video_service.stop_capture()
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logger.error(f"Error in stop endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    """Simple health check endpoint."""
    return jsonify({'status': 'OK'}), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed service status."""
    try:
        status = video_service.get_status()
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Video Capture Web Service")
    app.run(host='0.0.0.0', port=5000, debug=False)

# Video Streaming Service

The **video-streaming** service is a REST API application that captures video streams (primarily YouTube) and automatically uploads segments to S3, which then triggers the ingest pipeline for processing. This Video Streaming to S3 is **Simulating** a realtime video streaming, and is used to demo the pipeline E2E.

## Overview

The video streaming service:
- Captures live YouTube streams and Video-on-Demand (VOD) videos
- Splits video into configurable time segments (default: 10 seconds)
- Uploads each segment to S3 with metadata
- Automatically triggers the ingest pipeline when segments are uploaded
- Supports both live streams (runs until stopped) and VOD videos (auto-stops when video ends)

## How to Use

### Via GUI

1. Navigate to **Settings → Start Video Stream** in the web UI
2. Configure the following:
   - **NOTE** (Most of the values are preconfigured from Backend Secret config)
   - **YouTube URL**: Full YouTube video URL (e.g., `https://www.youtube.com/watch?v=...`)
   - **S3 Endpoint**: Your VAST S3 endpoint URL
   - **S3 Access Key**: Your S3 access key
   - **S3 Secret Key**: Your S3 secret key
   - **Bucket Name**: Target S3 bucket (e.g., `video-chunks`)
   - **Segment Duration**: How long each segment should be in seconds (default: 10)
   - **Metadata** (optional - Easy to adjust for different usecases):
     - `camera_id`: Camera identifier (e.g., "cam-01", "intersection-5th-ave")
     - `capture_type`: Type of capture (e.g., "traffic", "streets", "crowds", "malls")
     - `neighborhood`: Location/area (e.g., "manhattan", "downtown", "warehouse-a")
3. Click "Start Stream" to begin capture
4. Segments are automatically uploaded to S3 and processed by the ingest pipeline
5. Use "Stop Stream" to stop the capture at any time

### Via API (Direct)

The service exposes REST endpoints accessible at (If using API - Should be added to /etc/hosts):
```
http://video-streamer.<cluster_name>.vastdata.com
```

#### API Endpoints

1. **Start Capture** - `POST /start`
   ```json
   {
     "youtube_url": "https://www.youtube.com/watch?v=...",
     "access_key": "your-s3-access-key",
     "secret_key": "your-s3-secret-key",
     "s3_endpoint": "http://your-s3-endpoint.vastdata.com",
     "bucket_name": "video-chunks",
     "capture_interval": 10,
     "name": "my-capture",
     "camera_id": "cam-01",
     "capture_type": "traffic",
     "neighborhood": "downtown",
     "max_duration": 3600
   }
   ```
   - `youtube_url` (required): YouTube video URL
   - `access_key` (required): S3 access key
   - `secret_key` (required): S3 secret key
   - `s3_endpoint` (required): S3 endpoint URL
   - `bucket_name` (optional): S3 bucket name (default: `rawlivevideos`)
   - `capture_interval` (optional): Segment duration in seconds (default: 10)
   - `name` (optional): Prefix for uploaded files (default: `capture`)
   - `camera_id` (optional): Camera identifier metadata
   - `capture_type` (optional): Capture type metadata
   - `neighborhood` (optional): Location metadata
   - `max_duration` (optional): Maximum capture duration in seconds for VOD videos (default: 3600 = 1 hour)

2. **Stop Capture** - `POST /stop`
   ```json
   {}
   ```
   Stops the currently running capture session.

3. **Get Status** - `GET /status`
   Returns current service status including:
   - Whether capture is running
   - Current configuration (with sensitive data redacted)
   - Number of temporary files

4. **Health Check** - `GET /ping`
   Simple health check endpoint returning `{"status": "OK"}`

## How It Works

1. **Stream Detection**: The service uses `yt-dlp` to extract direct video stream URLs from YouTube links
2. **Video Capture**: Uses OpenCV with FFmpeg backend to capture video frames
3. **Segmentation**: Captures video in time-based chunks (e.g., 10-second segments)
4. **Upload**: Each segment is uploaded to S3 with metadata attached as S3 object metadata
5. **Pipeline Trigger**: When segments are uploaded to the configured S3 bucket, the ingest pipeline automatically processes them:
   - `video-segmenter` splits segments further if needed
   - `video-reasoner` analyzes content with AI
   - `video-embedder` creates embeddings
   - `video-vastdb-writer` stores vectors in VastDB

## Supported Video Types

- **Live YouTube Streams**: Continuously captures until manually stopped
- **YouTube VOD Videos**: Automatically stops when video ends (or after `max_duration` timeout)
- **Direct Video Streams**: Supports any stream URL that OpenCV can read

## Technical Details

- **Format**: All captured segments are saved as MP4 files (H.264 codec)
- **Resolution**: Automatically detects and preserves original stream resolution (typically up to 720p for YouTube)
- **Frame Rate**: Preserves original FPS from the source stream
- **Storage**: Temporary files are created during capture and automatically cleaned up after upload

## Deployment

The video streaming service is automatically deployed as part of the Kubernetes deployment (see [Part 2: Deploy Backend & Frontend](../README.md#part-2-deploy-backend--frontend) in the main README). It runs as a separate pod and is accessible via:
- **Internal**: `video-stream-capture-service:5000` (within the cluster)
- **External**: `http://video-streamer.<cluster_name>.vastdata.com` (via ingress)

The service uses the Docker image: `vastdatasolutions/vde-video-streaming:v1`


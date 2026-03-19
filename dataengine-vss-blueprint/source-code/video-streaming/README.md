# Video Streaming Service

REST API service that captures YouTube videos and uploads segments to S3, triggering the ingest pipeline. Used to simulate realtime video streaming for demos.

## Features

- Captures YouTube streams and VOD videos
- Splits into configurable segments (default: 10 seconds)
- Uploads to S3 with metadata
- Auto-triggers ingest pipeline
- VOD auto-stops when video ends; live streams run until stopped

## Usage via GUI

1. Navigate to **Settings → Start Video Stream**
2. Enter YouTube URL (S3 credentials are pre-filled from backend config)
3. Configure segment duration and metadata (camera_id, capture_type, location)
4. Click "Start Stream"
5. Use "Stop Stream" to stop capture

## API Endpoints

**Base URL**: `http://video-streamer.<cluster_name>.vastdata.com`

### POST /start

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "access_key": "...",
  "secret_key": "...",
  "s3_endpoint": "http://...",
  "bucket_name": "video-chunks",
  "capture_interval": 10,
  "camera_id": "cam-01",
  "capture_type": "traffic",
  "location": "downtown",
  "scenario": "surveillance",
  "custom_prompt": "Analyze safety...",
  "max_duration": 3600
}
```

### POST /stop

Stops the running capture.

### GET /status

Returns capture status and configuration.

### GET /ping

Health check.

## Technical Details

- **Format**: MP4 (H.264)
- **Resolution**: Up to 720p
- **Image**: `vastdatasolutions/vde-video-streaming:v1`
- **Internal**: `video-stream-capture-service:5000`

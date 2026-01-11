# Video Segmenter

A VAST DataEngine serverless function that splits uploaded videos into smaller segments for processing.

## What It Does

- Downloads video files from S3 when they are uploaded to the `video-chunks` bucket
- Splits videos into time-based segments (default: 5 seconds each)
- Converts videos to MP4 format (H.264 codec) if needed
- Uploads segments to the `video-chunks-segments` bucket
- Preserves metadata (camera_id, capture_type, neighborhood, etc.) from the original video

## Easy to Adjust

Configure in `ingest/vde-video-ingest-secret-template.yaml`:

- **`segment_duration`**: Length of each segment in seconds (default: `5`)
- **`output_codec`**: Video codec (default: `libx264`)
- **`output_format`**: Output format (default: `mp4`)
- **`output_bucket_suffix`**: Suffix for output bucket (default: `-segments`)

## About the Function

- **Trigger**: S3 bucket event when video is uploaded to `video-chunks`
- **Input**: Video file from S3
- **Output**: Multiple video segments uploaded to `video-chunks-segments`
- **Processing**: Uses FFmpeg for video segmentation and format conversion
- **Idempotency**: Skips processing if segments already exist

## What Runs It

- **Runtime**: VAST DataEngine serverless runtime
- **Image**: `vastdatasolutions/vde-video-segmenter:v1`
- **Resources**: Configure CPU/Memory in DataEngine UI pipeline settings
- **Dependencies**: FFmpeg, Python 3.11, boto3 for S3 access


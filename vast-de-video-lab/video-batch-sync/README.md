# Video Batch Sync Service

REST API service for batch copying MP4 video files from a source S3 bucket to a destination S3 bucket. Files are automatically processed by the ingest pipeline after copying.

## Features

- Copies MP4 files from source S3 to destination S3 using server-side operations
- Supports rate limiting (delay between files)
- Applies metadata (tags, privacy, streaming metadata) to all copied files
- Tracks progress in real-time
- Handles errors gracefully (continues with remaining files on failure)

## Usage

Access via **Settings → S3 Batch Video Sync** in the web UI:

1. Configure source S3 credentials and bucket/path
2. Optionally use default backend S3 credentials
3. Click "Check Videos" to verify MP4 files are found
4. Configure batch settings (delay between files) and metadata
5. Click "Start Batch Sync" to begin
6. Monitor progress via the sync icon in the toolbar

## How It Works

1. Lists all MP4 files in the source bucket/prefix
2. Copies files to destination bucket using server-side copy (same endpoint) or streaming copy (different endpoints)
3. Applies metadata to all copied files
4. Files are automatically processed by the ingest pipeline after copying

## Technical Notes

- Only MP4 files are copied
- Destination files: `{username}/{timestamp}_{original_name}.mp4`
- Uses streaming copy (8MB chunks) for memory efficiency
- No temporary files on disk
- Supports cross-endpoint copying

## Deployment

Deployed as a Kubernetes pod accessible at:
- **Internal**: `video-batch-sync-service:5000`
- **External**: `http://video-batch-sync.<cluster_name>.vastdata.com`

Docker image: `vastdatasolutions/vde-video-batch-sync:v1`

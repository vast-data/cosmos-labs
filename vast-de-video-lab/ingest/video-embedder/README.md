# Video Embedder

A VAST DataEngine serverless function that converts video reasoning text into vector embeddings for semantic search.

## What It Does

- Receives reasoning text from the `video-reasoner` function
- Converts reasoning text into vector embeddings using NVIDIA NIM embedding models
- Passes embeddings and metadata to the next function in the pipeline
- Preserves all metadata (camera_id, capture_type, neighborhood, etc.)

## Easy to Adjust

Configure in `ingest/vde-video-ingest-secret-template.yaml`:

- **`embeddinghost`**: NVIDIA NIM embedding endpoint host
- **`embeddingport`**: NVIDIA NIM embedding endpoint port
- **`embeddingmodel`**: Embedding model name (e.g., `nvidia/nv-embedqa-e5-v5`)
- **`embeddingdimensions`**: Vector dimensions (must match model output)
- **`nvidia_api_key`**: Optional NVIDIA Cloud API key (if using cloud endpoints)

## About the Function

- **Trigger**: Receives events from `video-reasoner` function
- **Input**: Reasoning text and metadata from video analysis
- **Output**: Vector embeddings and metadata
- **Processing**: Calls NVIDIA NIM embedding API to generate vectors
- **Validation**: Skips if reasoning content is empty or invalid

## What Runs It

- **Runtime**: VAST DataEngine serverless runtime
- **Image**: `vastdatasolutions/vde-video-embedder:v1`
- **Resources**: Configure CPU/Memory in DataEngine UI pipeline settings
- **Dependencies**: Python 3.11, NVIDIA NIM embedding API access


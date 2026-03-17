# Video Embedder

A VAST DataEngine serverless function that converts video reasoning text into vector embeddings for semantic search.

## What It Does

- Receives reasoning text from the `video-reasoner` function
- Converts reasoning text into vector embeddings using NVIDIA NIM embedding models
- Passes embeddings and metadata to the next function in the pipeline
- Preserves all metadata (camera_id, capture_type, location, etc.)

## Easy to Adjust

Configure in `ingest/vde-video-ingest-secret-template.yaml`:

| Setting | Description |
|---------|-------------|
| **`embedding_local_nim`** | `true` = local NIM (no API key), `false` = NVIDIA Cloud (sends API key) |
| **`embeddinghost`** / **`embeddingport`** / **`embeddinghttpscheme`** | Endpoint to use (always required) |
| **`embeddingmodel`** | Embedding model name (e.g., `nvidia/nv-embedqa-e5-v5`) |
| **`embeddingdimensions`** | Vector dimensions (must match model output) |
| **`nvidia_api_key`** | Required when `embedding_local_nim: false` (NVIDIA Cloud) |

For NVIDIA Cloud, set: `embeddinghost: integrate.api.nvidia.com`, `embeddingport: 443`, `embeddinghttpscheme: https`

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


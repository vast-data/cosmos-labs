# VastDB Writer

A VAST DataEngine serverless function that stores video embeddings and metadata in VastDB for vector search.

## What It Does

- Receives vector embeddings and metadata from the `video-embedder` function
- Stores embeddings in VastDB as vector columns
- Stores metadata (camera_id, capture_type, neighborhood, etc.) as regular columns
- Stores reasoning text for display in search results
- Creates database records for each video segment

## Easy to Adjust

Configure in `ingest/vde-video-ingest-secret-template.yaml`:

- **`vdbendpoint`**: VastDB endpoint URL (from QueryEngine VIP pool)
- **`vdbbucket`**: Database bucket name (e.g., `processed-videos-db`)
- **`vdbschema`**: Database schema name (e.g., `processed-videos-schema`)
- **`vdbcollection`**: Table/collection name (e.g., `processed-videos-collection`)
- **`vdbaccesskey`**: VastDB access key
- **`vdbsecretkey`**: VastDB secret key
- **`embeddingdimensions`**: Must match embedding model dimensions
- **`embeddingmodel`**: Embedding model name (for reference)

**To add custom metadata fields**, see [Dynamic Metadata Filters](../README.md#adding-custom-metadata-fields).

## About the Function

- **Trigger**: Receives events from `video-embedder` function
- **Input**: Vector embeddings, reasoning text, and metadata
- **Output**: Database records in VastDB
- **Processing**: Inserts data into VastDB using ADBC driver
- **Schema**: Automatically creates/updates table schema if needed
- **Validation**: Skips if embedding is invalid or empty

## What Runs It

- **Runtime**: VAST DataEngine serverless runtime
- **Image**: `vastdatasolutions/vde-vastdb-writer:v1`
- **Resources**: Configure CPU/Memory in DataEngine UI pipeline settings
- **Dependencies**: Python 3.11, ADBC driver for VastDB, libadbc_driver_vastdb.so


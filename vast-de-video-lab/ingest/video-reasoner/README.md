# Video Reasoner

A VAST DataEngine serverless function that analyzes video segments using NVIDIA Vision Language Models (VLM) to generate text descriptions.

## What It Does

- Downloads video segments from S3 when they are created in the `video-chunks-segments` bucket
- Analyzes video content using NVIDIA VLM (Cosmos or Nemotron)
- Generates text descriptions based on configurable prompts/scenarios
- Extracts metadata (camera_id, capture_type, neighborhood, etc.) from S3 object metadata
- Passes reasoning text and metadata to the next function in the pipeline

## Provider Selection

The function supports two reasoning providers:

- **`cosmos`**: Uses local Cosmos VLM server (uploads video via SFTP)
- **`nemotron`**: Uses NVIDIA Build Cloud API (extracts frames, sends as images)

Configure the provider in `ingest/vde-video-ingest-secret-template.yaml`:

```yaml
reasoning_provider: "nemotron"  # or "cosmos"
```

## Easy to Adjust

Configure in `ingest/vde-video-ingest-secret-template.yaml`:

### Common Settings

- **`reasoning_provider`**: Provider selection - `"cosmos"` or `"nemotron"` (default: `"cosmos"`)
- **`scenario`**: Analysis prompt scenario (default: `surveillance`)
  - Available scenarios: `surveillance`, `traffic`, `nhl`, `sports`, `retail`, `warehouse`, `nyc_control`, `general`
  - See [Available Scenarios](#available-scenarios) below for details
- **`max_video_size_mb`**: Maximum video size in MB (default: `100`)

### Cosmos Settings (when `reasoning_provider == "cosmos"`)

- **`cosmos_host`**: Cosmos VLM server IP address
- **`cosmos_port`**: Cosmos VLM server port
- **`cosmos_username`**: Cosmos VLM authentication username
- **`cosmos_password`**: Cosmos VLM authentication password
- **`cosmos_model`**: Cosmos VLM model name
- **`cosmos_upload_path`**: SFTP upload path on Cosmos server
- **`cosmos_video_port`**: Port for video URL access

### Nemotron Settings (when `reasoning_provider == "nemotron"`)

- **`nvidia_api_key`**: NVIDIA API key from build.nvidia.com (required)
- **`nemotron_model`**: Model identifier (default: `"nvidia/nemotron-nano-12b-v2-vl"`)
- **`nemotron_endpoint`**: API endpoint (default: `"https://integrate.api.nvidia.com/v1"`)
- **`nemotron_num_frames`**: Number of frames to extract (default: `5` for 5-second videos)
- **`nemotron_frame_interval`**: Interval in seconds between frames (default: `0.5` = evenly spaced)
- **`nemotron_max_tokens`**: Maximum tokens in response (default: `4096`)
- **`nemotron_temperature`**: Sampling temperature (default: `0.6`)
- **`nemotron_top_p`**: Top-p sampling parameter (default: `0.7`)

## About the Function

- **Trigger**: S3 bucket event when segment is created in `video-chunks-segments`
- **Input**: Video segment file from S3
- **Output**: Reasoning text, metadata, and analysis results
- **Processing**: 
  - **Cosmos**: Uploads video to Cosmos VLM server via SFTP, receives text analysis
  - **Nemotron**: Extracts frames from video, sends to NVIDIA Build Cloud API as images
- **Validation**: Skips non-MP4 files and invalid events

## What Runs It

- **Runtime**: VAST DataEngine serverless runtime
- **Image**: `vastdatasolutions/vde-video-reasoner:v1`
- **Resources**: Configure CPU/Memory in DataEngine UI pipeline settings
- **Dependencies**: 
  - Python 3.11
  - boto3 for S3 access
  - For Cosmos: Cosmos VLM server access, paramiko for SFTP
  - For Nemotron: opencv-python for frame extraction, NVIDIA API key

---

# Configurable Video Analysis Prompts

The analysis prompt can be configured per use case by setting the `scenario` key in the ingest secret, it is defaulted to `surveillance` for now. Works with both Cosmos and Nemotron providers.

## Available Scenarios

The system comes with pre-configured prompts optimized for different use cases:

| Scenario | Use Case |
|----------|----------|
| `surveillance` | Security cameras, safety monitoring (default) |
| `traffic` | Traffic cameras, vehicle detection, violations |
| `nhl` | Hockey game analysis, plays, penalties |
| `sports` | General sports footage analysis |
| `retail` | Store cameras, customer behavior, theft detection |
| `warehouse` | Industrial safety, forklift operations, PPE compliance |
| `nyc_control` | Urban command & control, license plates, anomalies |
| `general` | Generic video description |

## How to Change the Scenario

### Method 1: Edit the Ingest Secret

Edit `ingest/vde-video-ingest-secret-template.yaml` and set the `scenario` field:

```yaml
scenario: traffic  # Change to your use case
```

After updating the secret in the DataEngine UI, the pipeline will use the new scenario for all subsequent video processing.

### Method 2: Add a Custom Scenario

To create a custom scenario with your own prompt:

1. **Edit the prompts file**: `ingest/video-reasoner/common/prompts.py`

2. **Add your prompt to `SCENARIO_PROMPTS` dictionary**:
   ```python
   SCENARIO_PROMPTS = {
       # ... existing scenarios ...
       
       "my_custom_scenario": """Analyze this video and describe:
   1) Specific aspect you want to focus on
   2) Another important detail
   3) Additional observations
   Be specific about locations, timing, and severity.
   IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",
   }
   ```

3. **Update the ingest secret** to use your new scenario:
   ```yaml
   scenario: my_custom_scenario
   ```

4. **Redeploy the secret** in the DataEngine UI pipeline configuration

## Prompt Guidelines

When creating custom prompts, follow these guidelines:

- **Be specific**: Clearly define what aspects of the video should be analyzed
- **Keep it concise**: The model response should be under 150 words
- **Use structured format**: Numbered lists help organize the analysis
- **Include context**: Mention timing, locations, and severity when relevant
- **Write complete sentences**: Avoid bullet points or fragments

## How It Works

1. The `scenario` value from the ingest secret is passed to the `video-reasoner` function
2. The function looks up the corresponding prompt in `SCENARIO_PROMPTS`
3. Based on `reasoning_provider`:
   - **Cosmos**: Video is uploaded to Cosmos VLM server via SFTP, prompt is sent with video URL
   - **Nemotron**: Frames are extracted from video, prompt and frames are sent to NVIDIA Build Cloud API
4. The VLM analyzes the video/frames and returns a text description based on the prompt
5. The description is then embedded and stored in VastDB for search

## Provider Comparison

| Feature | Cosmos | Nemotron |
|---------|--------|----------|
| **Video Support** | Full video files | Frame extraction (images only) |
| **Deployment** | Local server required | Cloud API (no server needed) |
| **Authentication** | SSH/SFTP credentials | NVIDIA API key |
| **Frame Extraction** | Not needed | Automatic (configurable) |
| **Best For** | Self-hosted, full video analysis | Cloud-based, quick setup |

## Model Selection

- **Cosmos**: Configure `cosmos_model` in the ingest secret
- **Nemotron**: Configure `nemotron_model` in the ingest secret (default: `nvidia/nemotron-nano-12b-v2-vl`)

For more information, see [Part 1: Configuration - Step 1.3: Review Ingest Secret](../README.md#step-13-review-ingest-secret) in the main README.


# Video Reasoner

A VAST DataEngine serverless function that analyzes video segments using NVIDIA Cosmos VLM to generate text descriptions.

## What It Does

- Downloads video segments from S3 when they are created in the `video-chunks-segments` bucket
- Analyzes video content using NVIDIA Cosmos VLM (Vision Language Model)
- Generates text descriptions based on configurable prompts/scenarios
- Extracts metadata (camera_id, capture_type, neighborhood, etc.) from S3 object metadata
- Passes reasoning text and metadata to the next function in the pipeline

## Easy to Adjust

Configure in `ingest/vde-video-ingest-secret-template.yaml`:

- **`scenario`**: Analysis prompt scenario (default: `surveillance`)
  - Available scenarios: `surveillance`, `traffic`, `nhl`, `sports`, `retail`, `warehouse`, `nyc_control`, `general`
  - See [Available Scenarios](#available-scenarios) below for details
- **`cosmos_host`**: Cosmos VLM server IP address
- **`cosmos_port`**: Cosmos VLM server port
- **`cosmos_username`**: Cosmos VLM authentication username
- **`cosmos_password`**: Cosmos VLM authentication password
- **`cosmos_model`**: Cosmos VLM model name
- **`max_video_size_mb`**: Maximum video size in MB (default: `100`)

## About the Function

- **Trigger**: S3 bucket event when segment is created in `video-chunks-segments`
- **Input**: Video segment file from S3
- **Output**: Reasoning text, metadata, and analysis results
- **Processing**: Uploads video to Cosmos VLM server, receives text analysis
- **Validation**: Skips non-MP4 files and invalid events

## What Runs It

- **Runtime**: VAST DataEngine serverless runtime
- **Image**: `vastdatasolutions/vde-video-reasoner:v1`
- **Resources**: Configure CPU/Memory in DataEngine UI pipeline settings
- **Dependencies**: Python 3.11, Cosmos VLM server access, boto3 for S3 access

---

# Configurable Video Analysis Prompts (Cosmos VLM)

The analysis prompt can be configured per use case by setting the `scenario` key in the ingest secret, it is defaulted to `surveillance` for now.

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
3. The prompt is sent to NVIDIA Cosmos VLM along with the video segment
4. Cosmos analyzes the video and returns a text description based on the prompt
5. The description is then embedded and stored in VastDB for search

## Model Selection

For information on selecting and configuring the Cosmos VLM model, see [Part 1: Configuration - Step 1.3: Review Ingest Secret](../README.md#step-13-review-ingest-secret) in the main README.


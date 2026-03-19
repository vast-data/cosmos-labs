# Video Reasoner

DataEngine function that analyzes video segments using NVIDIA VLM (Cosmos or Nemotron) to generate text descriptions.

## What It Does

- Triggered when segments land in `video-chunks-segments` bucket
- Analyzes video content and generates text descriptions
- Extracts metadata from S3 object metadata
- Passes results to the next function in pipeline

## Configuration

Configure in `deployments/dataengine-vss-ingest-pipeline/vss-gui-secret-file-template.yaml.yaml` (GUI) or `vss-cli-secret-file-template.yaml` (CLI):

### Provider Selection

```yaml
reasoning_provider: "nemotron"  # or "cosmos"
```

| Provider | Description |
|----------|-------------|
| `cosmos` | Hosted Reason API (sends base64-encoded video) |
| `nemotron` | NVIDIA Cloud API (extracts frames, sends as images) |

### Cosmos Settings

| Setting | Default |
|---------|---------|
| `cosmos_host` | (required) |
| `cosmos_port` | (required) |
| `cosmos_model` | ./Cosmos-Reason2-8B |

### Nemotron Settings

| Setting | Default |
|---------|---------|
| `nvidia_api_key` | (required) |
| `nemotron_model` | nvidia/nemotron-nano-12b-v2-vl |
| `nemotron_num_frames` | 5 |

---

## Analysis Scenarios

Set `scenario` in ingest secret or per-video via S3 metadata:

| Scenario | Use Case |
|----------|----------|
| `surveillance` | Security cameras, safety monitoring |
| `traffic` | Traffic cameras, vehicle detection |
| `nhl` | Hockey game analysis |
| `sports` | General sports footage |
| `retail` | Store cameras, customer behavior |
| `warehouse` | Industrial safety, PPE compliance |
| `egocentric` | First-person perspective |
| `general` | Generic video description (default) |

### Per-Video Override

Set `scenario` in S3 object metadata when uploading:

```python
s3_client.put_object(
    Bucket=bucket, Key=key, Body=video_content,
    Metadata={"scenario": "traffic"}
)
```

---

## Custom Prompts

For full control, provide a custom prompt via S3 metadata (overrides scenario):

```python
Metadata={"custom-prompt": "Analyze safety violations..."}
```

Or use the GUI:
- **Manual Upload / Streaming / Batch Sync**: Check "Use custom prompt"

Max 800 characters. URL-encoded automatically.

### Adding New Scenarios

1. Edit `source-code/ingest/video-reasoner/common/prompts.py`
2. Add to `SCENARIO_PROMPTS` dictionary
3. Update ingest secret with new scenario name
4. Redeploy in DataEngine UI

---

## Runtime

- **Image**: `vastdatasolutions/vde-video-reasoner:v1`
- **Trigger**: S3 bucket event on `video-chunks-segments`

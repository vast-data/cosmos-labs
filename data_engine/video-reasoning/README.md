# VAST DataEngine - Video Reasoning Lab

Full overview: How to Deploy and Manage the Video Reasoning Lab system powered by VAST DataEngine.  

###### This is **NOT** an AI generated README. All steps here are mandatory to deploy the entire Demo.  

## Overview

The system has two main parts:
1. **Backend/Frontend** (Kubernetes) - User interface and API
2. **Ingest Pipeline** (VAST DataEngine) - Serverless video processing functions

## Pipeline Flow Diagram

![Video Reasoning Lab Architecture](video-demo-diagram.png)

---

## Prerequisites

- `kubectl` configured for your cluster
- Access to VAST DataEngine UI / CLI
- Cluster name (Any name you pick - e.g., `v1234`) 
- S3 buckets: `video-chunks` and `video-chunks-segments` created
- VastDB database bucket: `processed-videos-db` created
- NVIDIA COSMOS Modelo Endpoint & NIM Endpoints with API key for embeddings and LLM models
- **Optional (for Video Alerts)**: Twilio account with phone number and SMS enabled

---

## Deployment Flow

Follow these steps in order:

1. **Part 1: Configuration** - Review and configure all secrets, configmaps, and images
2. **Part 2: Deploy Backend & Frontend** - Deploy Kubernetes services
3. **Part 3: Deploy Ingest Pipeline** - Create DataEngine pipeline using UI / CLI
4. **Part 4: Testing** - Test the complete system

---

## Part 1: Configuration

### Step 1.1: Review and Configure Backend Secret

**Location:** `retrieval/k8s/backend-secret.yaml`

**Required configuration:**
- **VastDB**: Database credentials and connection info
  - `vdb_endpoint` - VastDB endpoint URL [ From QueryEngine Vippool ]
  - `vdb_bucket`, `vdb_schema`, `vdb_collection` - Database path
  - `vdb_access_key`, `vdb_secret_key` - Credentials
- **S3**: Object storage credentials and buckets
  - `s3_endpoint` - S3 endpoint URL
  - `s3_upload_bucket`, `s3_segments_bucket` - Bucket names
  - `s3_access_key`, `s3_secret_key` - Credentials
- **NVIDIA API**: NIM embeddings and LLM API keys
  - `nvidia_api_key` - NVIDIA API key
  - `embedding_model` - Embedding model name - [ Tested with `nvidia/nv-embedqa-e5-v5` ]
  - `llm_model_name` - LLM model - [ Tested with `meta/llama-3.1-8b-instruct` ]
- **LLM Settings**: Model name, timeouts, parameters
- **VASTDB ADBC Driver**:
   - Download the latest release from https://github.com/vast-data/vastdb-adbc-driver/releases
   - Add the extracted driver to /tmp/libadbc_driver_vastdb.so

**Edit the file with your credentials:**
```bash
cd retrieval/k8s
# Edit backend-secret.yaml with your configuration
vim backend-secret.yaml
```

### Step 1.2: Review Backend ConfigMap

**Location:** `retrieval/k8s/backend-configmap.yaml`

Contains:
- **LLM System Prompt**: Instructions for AI-powered search synthesis

#### Customizing System Prompts for Your Use Case

The system prompt guides the LLM on how to analyze and synthesize video content. You can customize it based on your specific video use case:

**Default Configuration:** Surveillance/Security monitoring

**To customize:**
1. Edit `retrieval/k8s/backend-configmap.yaml`
2. Apply changes after deployment (see "Update Configuration" section)


### Step 1.3: Verify Docker Images

**Backend/Frontend images are prebuilt:**
- `simongolan/vde-video-backend:v1`
- `simongolan/vde-video-frontend:v1`
- `simongolan/vde-video-streaming:v1`

**If you need to rebuild and push to a different registry:**  
**NOTE: these images are static docker servers, not a 'vast dataengine' functions**
```bash
# Backend
cd retrieval/< video-backend / frontend >
docker build -t <your-registry>/vde-video-backend:<tag> . --platform linux/amd64
docker push <your-registry>/vde-video-backend:<tag>
```
Then update the image references in `backend-deployment.yaml` and `frontend-deployment.yaml`.

### Step 1.4: Review Ingest Secret

**Location:** `ingest/vde-video-ingest-secret-template.yaml`

**Required configuration:**
- **S3**: Upload bucket credentials
- **Cosmos**: AI model server credentials (host, port, username, password)
- **NVIDIA NIM**: Embedding model API keys
- **VastDB**: Database credentials
- **Video Processing**: Segment duration, codec, format

**Edit the file with your credentials:**
```bash
# Edit ingest secret
vim ingest/vde-video-ingest-secret-template.yaml
```

### Step 1.5: Review Video Alerts Secret (Optional - Seperate Pipeline)

**Location:** `ingest/video-alerts/video-alerts-secret-template.yaml`

**Prerequisites for Video Alerts:**
- **Twilio Account** (for SMS alerts)
  - Sign up at: https://www.twilio.com
  - Get a Twilio phone number (for sending SMS)
  - Note your Account SID and Auth Token from the Twilio Console
  - Set up a Messaging Service SID
  - Have a destination phone number (where alerts will be sent)

**Required configuration:**
- **Twilio SMS Settings**:
  - `twilio_account_sid` - Your Twilio account SID
  - `twilio_auth_token` - Your Twilio authentication token
  - `twilio_messaging_service_sid` - Messaging service SID from Twilio
  - `twilio_to_phone` - Destination phone number (format: +1234567890)
- **NVIDIA NIM**: Same embedding model API key as ingest pipeline
- **VastDB**: Same database credentials as ingest pipeline
- **Alert Configuration**:
  - `alert_queries` - List of safety queries with thresholds (JSON format)
  - `alert_top_k` - Number of results to check per query (default: 5)
  - `default_threshold` - Default similarity threshold (0.0-1.0, default: 0.5)
  - `cooldown_minutes` - Time between alerts for same incident (default: 5)
  - `alert_lookback_minutes` - Time window to search for new videos (default: 6)
  - `alerts_table` - VastDB table name for storing alerts (e.g., "safety-alerts-collection")

**Example alert queries configuration:**
```json
[
  {"query": "fire flames or smoke visible", "threshold": 0.50},
  {"query": "person fallen on ground lying down motionless", "threshold": 0.60},
  {"query": "physical fight altercation people hitting", "threshold": 0.58},
  {"query": "medical emergency injury bleeding unconscious", "threshold": 0.65}
]
```

**Edit the file with your credentials:**
```bash
# Edit video alerts secret
vim ingest/video-alerts/video-alerts-secret-template.yaml
```

---

## Part 2: Deploy Backend & Frontend

Now that all configuration is ready, deploy the backend and frontend services.

### Deployment Steps

1. **Navigate to the k8s directory:**
```bash
cd retrieval/k8s
```

2. **Run the deployment script with your CLUSTER_NAME:**
Example:
```bash
./QUICK_DEPLOY.sh v1234
```

3. **What the script does:**
   - Creates `vastvideo` namespace
   - Deploys backend secret (credentials & config)
   - Deploys backend configmap (LLM system prompt)
   - Deploys backend service (FastAPI)
   - Deploys frontend service (Angular)
   - Deploys video streaming service
   - Creates ingress rules

4. **Wait for pods to be ready:**
```bash
kubectl get pods -n vastvideo -w
```

5. **Add to `/etc/hosts` the ingress dns:**
```
<k8s_node_ip> video-lab.<cluster_name>.vastdata.com video-streamer.<cluster_name>.vastdata.com
```

6. **Access the UI:**
```
http://video-lab.<cluster_name>.vastdata.com
```

---

## Part 3: Deploy Ingest Pipeline Using DataEngine UI

Now that you've configured the ingest secrets (Step 1.4 and 1.5), deploy the serverless video processing pipeline using the **VAST DataEngine UI**.

### Pipeline Overview (Just an Overview - Read It - NOT a deployment yet.)

**Pipeline Name:** `video-realtime-processing-pipeline`

The pipeline has 3 trigger-to-function flows:

#### Flow 1: Video Segmentation
```
video-chunk-land-trigger → video-segmenter
```
- **Trigger**: S3 bucket - `video-chunks` (when video is uploaded)
- **Function Purpose**: Splits video into 5-second segments

#### Flow 2: Video Analysis & Storage
```
video-segment-land-trigger → video-reasoner → video-embedder → video-vastdb-writer
```
- **Trigger**: S3 bucket `video-chunks-segments` (when segment is created)
- **Functions Purpose**: 
  - `video-reasoner` - AI analysis using Cosmos VLM
  - `video-embedder` - Convert reasoning to embeddings
  - `video-vastdb-writer` - Store vectors and metadata in VastDB

#### Flow 3: Safety Monitoring (Optional)
```
video-safety-trigger → video-alerts
```
- **Trigger**: Schedule (every 5 minutes)
- **Function Purpose**: Scan VastDB for safety incidents and send SMS alerts

---

### Step 3.1: Upload Secrets to a New Pipeline

Upload the secrets you configured in Part 1:

1. Navigate to **DataEngine UI** → **Create Pipeline**
2. Upload **ingest secret**: `ingest/vde-video-ingest-secret-template.yaml`
3. Upload **video alerts secret** (Optional - Seperate Pipeline): `ingest/video-alerts/video-alerts-secret-template.yaml`

---

### Step 3.2: Create Triggers

Navigate to **DataEngine UI** → **Triggers** and create:

| Trigger Name | Type | Configuration |
|--------------|------|---------------|
| `video-chunk-land-trigger` | S3 Bucket | Bucket: `video-chunks` |
| `video-segment-land-trigger` | S3 Bucket | Bucket: `video-chunks-segments` |
| `video-safety-trigger` | Schedule | Cron: `*/5 * * * *` (every 5 minutes) |

---

### Step 3.3: Create Functions

Navigate to **DataEngine UI** → **Functions** and create:

| Function Name | Public Image |
|---------------|-----------------|
| `video-segmenter` | `simongolan/vde-video-segmenter:v1`|
| `video-reasoner` | `simongolan/vde-video-reasoner:v1` |
| `video-embedder` | `simongolan/vde-video-embedder:v1` |
| `video-vastdb-writer` | `simongolan/vde-vdb-writer:v1` |
| `video-safety-alerts` | `simongolan/vde-video-alerts:v1` |

**Note:** Docker images are prebuilt and available on Docker Hub. If you need to push to a different registry, rebuild the images:
```bash
cd ingest/<function-folder>
vastde build -t <your-registry>/<image-name>:<tag> . --platform linux/amd64
docker push <your-registry>/<image-name>:<tag>
```
Then use your custom image in the DataEngine UI function creation.

---

### Step 3.4: Create Pipeline

Navigate to **DataEngine UI** → **Pipelines** → **Create New Pipeline**

**Pipeline Name:** `video-realtime-processing-pipeline`

**Add the following connections:**

1. **Segmentation Flow:**
   - Connect: `video-chunk-land-trigger` → `video-segmenter`

2. **Analysis Flow:**
   - Connect: `video-segment-land-trigger` → `video-reasoner`
   - Connect: `video-reasoner` → `video-embedder`
   - Connect: `video-embedder` → `video-vastdb-writer`

3. **Safety Flow (Optional - Seperate Pipeline):**
   - Connect: `video-safety-trigger` → `video-alerts`

4. **Raise CPU / MEM Resources to All functions:**
   - CPU: `1000m - 5000m`
   - Memory: `1280Mi - 2560Mi`

**Save and activate the pipeline.**

---

## Part 4: Testing the Deployment

Now that everything is deployed, test the complete system end-to-end.

### Testing Steps

1. **Login to the GUI:**
   - Open `http://video-lab.<cluster_name>.vastdata.com`
   - Enter VAST VMS IP and credentials
   - Click "Log in"

2. **Upload a test video:**
   - Click "Upload Video"
   - Drag & drop a video file
   - Video is uploaded to S3 bucket `video-chunks`

3. **Monitor the pipeline (DataEngine UI):**
   - Open **DataEngine UI** → **Pipelines** - Status should be **Running**
   - Watch the pipeline process your video through all functions
   - Click on any execution to see detailed logs
   - Verify all functions complete successfully

4. **Verify data in VastDB:**
   - Check that vectors and metadata are stored in the `processed-videos-collection` table

5. **Search for content:**
   - Return to the Video Lab GUI
   - Use the search bar
   - Try example queries like "person walking"
   - Enable "LLM Reasoning" toggle
   - View video segments with AI-generated summaries

---

## Troubleshooting


### View Logs

**Backend/Frontend:**
```bash
kubectl logs -f -n vastvideo -l app=video-backend
kubectl logs -f -n vastvideo -l app=video-frontend
```

**Ingest Functions (DataEngine UI):**
- Navigate to **DataEngine UI** → **Pipeline Management** → **Logs & Traces** 

---

## Environment Variables Summary

### Backend Secret Contains:
- `vdb_endpoint` - VastDB endpoint URL
- `vdb_bucket` - Database bucket name
- `vdb_schema` - Database schema name
- `vdb_collection` - Table name for video segments
- `s3_endpoint` - S3 endpoint URL
- `s3_upload_bucket` - Bucket for video uploads
- `s3_segments_bucket` - Bucket for processed segments
- `nvidia_api_key` - NVIDIA NIM API key
- `embedding_model` - Embedding model name
- `llm_model_name` - LLM model for synthesis

### Ingest Secret Contains:
- `s3accesskey` / `s3secretkey` - S3 credentials
- `cosmos_host` - Cosmos VLM server IP
- `cosmos_username` / `cosmos_password` - Cosmos credentials
- `embeddinghost` - NVIDIA NIM endpoint
- `vdbendpoint` - VastDB endpoint
- `vdbcollection` - Target collection for storage
- `segment_duration` - Video segment length (seconds)

---

### Architecture Summary

```
                           ┌──────────────────────────────────────────────────────────────┐
                           │                    Kubernetes Cluster                        │
                           │                                                              │
                           │  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐   │
                           │  │   Frontend   │◄───┤   Ingress    │───►│   Backend     │   │
                           │  │   (Angular)  │    │              │    │   (FastAPI)   │   │
                           │  └──────────────┘    └──────────────┘    └───────┬───────┘   │
                           │                                                    │         │
                           │                                                    ▼         │
                           │                                          ┌──────────────────┐│
                           │                                          │  VastDB / S3     ││
                           │                                          └──────────────────┘│
                           └──────────────────────────────────────────────────────────────┘

                           ┌──────────────────────────────────────────────────────────────┐
                           │              VAST DataEngine (Serverless)                    │
                           │                                                              │
                           │  S3 Upload  →  video-segmenter  →  video-reasoner            │
                           │                       ↓                    ↓                 │
                           │                 CloudEvent          CloudEvent               │
                           │                       ↓                    ↓                 │
                           │              reasoning-embedder  →  vastdb-writer            │
                           │                                            ↓                 │
                           │                                       VastDB (vectors)       │
                           │                                                              │
                           │  Schedule (5min)  →  video-alerts  →  SMS Alerts             │
                           └──────────────────────────────────────────────────────────────┘
```

---

## Need Help?

- **Backend/Frontend issues**: Check Kubernetes pod logs
- **Pipeline issues**: Use DataEngine UI → Executions to see where pipeline fails
- **Function errors**: Check function logs in DataEngine UI
- **Database issues**: Verify VastDB connectivity and credentials in secrets
- **Search not working**: Check NVIDIA API key in backend secret
- **Videos not processing**: Verify pipeline is Active in DataEngine UI and S3 buckets are correct


# VAST DataEngine - Video Reasoning Lab

Full overview: How to Deploy and Manage the Video Reasoning Lab system powered by VAST DataEngine.  

###### This is **NOT** an AI generated README. All steps here are mandatory to deploy the entire Demo.  

## Overview

The system has two main parts:
1. **Backend/Frontend** (Kubernetes) - User interface and API
2. **Ingest Pipeline** (VAST DataEngine) - Serverless video processing functions

---

## Key Features

### 1. Configurable Video Analysis Prompts (Cosmos VLM)

The `video-reasoner` function uses NVIDIA Cosmos VLM for video understanding. The analysis prompt can be configured per use case by setting the `scenario` key in the ingest secret.

**Available scenarios:**
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

**To change the scenario**, edit `ingest/vde-video-ingest-secret-template.yaml`:
```yaml
scenario: traffic  # Change to your use case
```

**To add a custom scenario**, edit `ingest/video-reasoner/common/prompts.py` and add your prompt to `SCENARIO_PROMPTS`.

---

### 2. Dynamic Metadata Filters

The system supports customizable metadata fields that flow through the entire pipeline:

**Current metadata fields:**
- `camera_id` - Camera identifier (e.g., "cam-01", "intersection-5th-ave")
- `capture_type` - Type of capture (e.g., "traffic", "streets", "crowds", "malls")
- `neighborhood` - Location/area (e.g., "manhattan", "downtown", "warehouse-a")

**How it works:**
1. **Ingest**: Metadata is set when uploading videos (via GUI upload or streaming service)
2. **Pipeline**: Metadata propagates through all functions (segmenter → reasoner → embedder → writer)
3. **VastDB**: Stored as columns alongside vectors and reasoning content
4. **Backend**: Auto-discovers available metadata columns dynamically from VastDB schema
5. **Frontend**: Displays discovered filters as dropdowns with actual values from the database

**To add custom metadata fields:**
1. Add the field to `ingest/*/common/models.py` (all functions)
2. Pass the field through each function's handler
3. Add to VastDB schema in `vastdb-writer/common/vastdb_client.py`
4. Backend will auto-discover the new column on next restart

---

### 3. Advanced LLM & Search Settings (GUI)

The GUI provides fine-grained control over search and LLM behavior via **Settings → Advanced LLM Settings**:

| Setting | Description | Options | Default |
|---------|-------------|---------|---------|
| **LLM Analysis Count** | Number of top results sent to LLM for synthesis | 3, 5, 10 | 3 |
| **Max Search Results** | Maximum video segments returned from search | 5, 10, 15 | 15 |
| **Minimum Similarity** | Threshold for vector similarity (lower = broader) | 0.1 - 0.8 slider | 0.1 |

Settings are persisted in browser localStorage and apply to all subsequent searches.

---

### 4. Custom LLM System Prompt (GUI)

The LLM system prompt (used for synthesizing search results) can be customized via **Settings → System Prompt**:

- **Default prompt**: Built into the frontend, used when no custom prompt is set
- **Custom prompt**: Override via the settings dialog - persisted in localStorage
- **Reset**: Return to default at any time

This allows tailoring the LLM response style without backend redeployment.

---

### 5. Time-Based Filtering

Search results can be filtered by time:
- **Presets**: Last 5 min, 15 min, 1 hour, 24 hours, 1 week
- **Custom Date**: Select specific date/time range with picker

Time filter applies to `upload_timestamp` column in VastDB.

---

### 6. Live Video Streaming Capture

The **video-streaming** service captures live YouTube streams and uploads segments to S3:
- Access via GUI → Settings → "Start Video Stream"
- Configure: YouTube URL, S3 credentials, segment duration
- Set metadata: `camera_id`, `capture_type`, `neighborhood` (optional)
- Segments automatically trigger the ingest pipeline

---

### 7. MP4 Video Format Requirement

**Important:** NVIDIA Cosmos Reason VLM requires MP4 (H.264) format. The system:
- Restricts GUI uploads to MP4 only
- Automatically converts non-MP4 formats during segmentation (if uploaded via CLI/tools)

---

### 8. User Authentication

The system authenticates users against VAST cluster credentials with support for multiple tenants.

**Steps to make Authentication work**
1. VMS > Administrators > Administrative Roles
2. Create New Role > Provide Name 'read-only' > Choose Read-only (View) Permissions > Create
3. VMS > Administrators > Managers > Create
4. Create 'vssadmin' manager > Provide Password > Uncheck 'Password is temporary' Attach to 'read-only' Role

**Add these credentials to the Backend Secret:**
**Location:** `retrieval/k8s/backend-secret.yaml`
```yaml
# vssadmin Credentials (for authenticating users via VAST API)
vast_admin_username: "vssadmin"       # vssadmin user (readonly)
vast_admin_password: "password"

# S3 Settings - IMPORTANT: Must match the tenant you want to support
s3_endpoint: "http://tenant-specific-endpoint.vastdata.com"  # S3 endpoint for the tenant
s3_access_key: "YOUR_ACCESS_KEY"
s3_secret_key: "YOUR_SECRET_KEY" 
```
- The admin credentials are only used server-side for user lookups, never exposed to clients
- **CRITICAL**: The `s3_endpoint` must be configured for the tenant you want users to authenticate with. Access keys are tenant-scoped and will only validate against their tenant's S3 endpoint.

**How it works:**
1. User enters: **Username**, **S3 Secret Key**, **VAST Host** (VMS IP), and **Tenant Name** in the login screen
2. Backend queries user in the specified tenant context
3. Backend validates S3 credentials using the configured `s3_endpoint` (must match the tenant)
4. On success, an internal JWT token is issued for the session

**Supported user providers:**
- Local VAST users
- Active Directory (AD)
- LDAP
- NIS

**Tenant Support:**
- Supports both default and non-default tenants
- Users must specify their tenant name during login (default: "default")
- The backend's `s3_endpoint` configuration must match the tenant's S3 endpoint
- If users from multiple tenants need to authenticate, deploy separate backend instances with tenant-specific `s3_endpoint` configurations

**Important Notes:**
- Users authenticate with their **username + S3 secret key** (not their password)
- The S3 secret key is obtained from VAST user management
- Access keys are tenant-scoped - they only work with their tenant's S3 endpoint
- If authentication fails, check that `s3_endpoint` in backend-secret.yaml matches the tenant's S3 endpoint

---

## Pipeline Flow Diagram

![Video Reasoning Lab Architecture](video-demo-diagram.png)

---

## Prerequisites

Before starting, ensure you have:

- **Kubernetes access:**
  - `kubectl` installed and configured for your cluster
  - `KUBECONFIG` environment variable set (or default config at `~/.kube/config`)
  - Ability to create namespaces and deploy resources

- **VAST cluster access:**
  - Access to VAST DataEngine UI / CLI
  - Cluster name (Any name you pick - e.g., `v1234`)
  - Admin credentials for creating VMS manager user (see Authentication section)

- **Storage resources:**
  - S3 buckets created: `video-chunks` and `video-chunks-segments`
  - VastDB database bucket created: `processed-videos-db` (or your custom name)

- **AI/ML services:**
  - NVIDIA COSMOS Modelo Endpoint (for video reasoning)
  - NVIDIA NIM Endpoints with API key (for embeddings and LLM models)

- **Network access:**
  - Your laptop/computer must be able to reach the Kubernetes cluster
  - Ability to modify `/etc/hosts` (or Windows hosts file) on your local machine

---

## Deployment Flow

Follow these steps in order:

1. **Part 1: Configuration** - Review and configure all secrets and images
2. **Part 2: Deploy Backend & Frontend** - Deploy Kubernetes services
3. **Part 3: Deploy Ingest Pipeline** - Create DataEngine pipeline using UI / CLI
4. **Part 4: Testing** - Test the complete system

---

## Part 1: Configuration

Before deploying, you need to configure secrets with your credentials. These secrets store sensitive information like API keys, database credentials, and S3 access keys.

### Step 1.1: Review and Configure Backend Secret

**Location:** `retrieval/k8s/backend-secret.yaml`

This file contains all the configuration needed for the backend service to connect to VastDB, S3, and NVIDIA services.

**Required configuration sections:**

1. **VastDB** (Database for storing video vectors):
   - `vdb_endpoint` - VastDB endpoint URL (from QueryEngine VIP pool)
   - `vdb_bucket` - Database bucket name (e.g., `processed-videos-db`)
   - `vdb_schema` - Database schema name (e.g., `processed-videos-schema`)
   - `vdb_collection` - Table/collection name (e.g., `processed-videos-collection`)
   - `vdb_access_key` - VastDB access key
   - `vdb_secret_key` - VastDB secret key

2. **S3** (Object storage for videos):
   - `s3_endpoint` - **CRITICAL**: S3 endpoint URL for your tenant (must match tenant users will authenticate with)
   - `s3_upload_bucket` - Bucket for uploaded videos (e.g., `video-chunks`)
   - `s3_segments_bucket` - Bucket for processed segments (e.g., `video-chunks-segments`)
   - `s3_access_key` - S3 access key
   - `s3_secret_key` - S3 secret key

3. **NVIDIA API** (AI/ML services):
   - `nvidia_api_key` - NVIDIA API key for NIM endpoints
   - `embedding_model` - Embedding model name (tested with `nvidia/nv-embedqa-e5-v5`)
   - `llm_model_name` - LLM model for synthesis (tested with `meta/llama-3.1-8b-instruct`)

4. **VAST Admin** (For user authentication):
   - `vast_admin_username` - VMS manager username (e.g., `vssadmin`)
   - `vast_admin_password` - VMS manager password

**Edit the file with your credentials:**
```bash
cd retrieval/k8s
# Edit backend-secret.yaml with your configuration
vim backend-secret.yaml
# or use your preferred editor
```

### Step 1.2: Verify Docker Images

**Pre-built images (ready to use):**
- `vastdatasolutions/vde-video-backend:v1` - Backend API service
- `vastdatasolutions/vde-video-frontend:v1` - Frontend web UI
- `vastdatasolutions/vde-video-streaming:v1` - Video streaming capture service

These images are available on Docker Hub and ready to use. The deployment YAML files reference these images by default.

**If you need to use a different registry or rebuild images:**

**NOTE:** These are standard Docker containers (not VAST DataEngine functions). They run as Kubernetes deployments.

```bash
# Example: Rebuild backend image
cd retrieval/video-backend
docker build -t <your-registry>/vde-video-backend:<tag> . --platform linux/amd64
docker push <your-registry>/vde-video-backend:<tag>
```

Then update the image references in:
- `backend-deployment.yaml` - Change `image:` field
- `frontend-deployment.yaml` - Change `image:` field  
- `videostreamer-deployment.yaml` - Change `image:` field

### Step 1.3: Review Ingest Secret

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

---

## Part 2: Deploy Backend & Frontend

Now that all configuration is ready, deploy the backend and frontend services to Kubernetes.

### What Gets Deployed

The deployment creates:
- **Backend Service** (FastAPI) - REST API for search, authentication, video management
- **Frontend Service** (Angular) - Web UI for video search and upload
- **Video Streaming Service** - Service for capturing live video streams
- **Ingress Resources** - Exposes services via HTTP with custom domain names
- **Secrets & ConfigMaps** - Stores credentials and configuration

### Deployment Steps

1. **Navigate to the k8s directory:**
```bash
cd retrieval/k8s
```

2. **Run the deployment script with your CLUSTER_NAME:**
```bash
./QUICK_DEPLOY.sh v1234
```
Replace `v1234` with your actual cluster name.

**What the script does:**
   - Checks prerequisites (kubectl, cluster connectivity)
   - Creates `vastvideo` namespace
   - Deploys backend secret (credentials & config from `backend-secret.yaml`)
   - Deploys backend service (FastAPI)
   - Deploys frontend service (Angular)
   - Deploys video streaming service
   - Creates ingress rules for external access

**Note:** LLM system prompt is now configured via the GUI settings (no ConfigMap needed).

4. **Wait for pods to be ready:**
```bash
kubectl get pods -n vastvideo -w
```

5. **Configure DNS on your local machine:**

Get the Ingress IP and add it to your `/etc/hosts` file (on your laptop, not the cluster):

```bash
# Get the Ingress IP
kubectl get ingress -n vastvideo
# Look for EXTERNAL-IP or ADDRESS (may show "pending" initially - wait a few minutes)
```

Add to `/etc/hosts` (macOS/Linux) or `C:\Windows\System32\drivers\etc\hosts` (Windows):
```
<INGRESS_IP> video-lab.<cluster_name>.vastdata.com
```

**Note:** Each user needs to add this entry on their own machine to access the UI.

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

---

### Step 3.1: Create Triggers

##### Prerequisites:
- This step assumes you have a running Vast DataEngine cluster
- You have a user with the right permissions and roles to setup DataEngine Pipelines (Including the Vector QueryEngine Identity-Policy.)
- You have a pre-created Topic in Vast Event Broker (e.g. video-topic) for creating triggers

Navigate to **DataEngine UI** → **Triggers** and create:

| Trigger Name | Type | Configuration |
|--------------|------|---------------|
| `video-chunk-land-trigger` | S3 Bucket | Bucket: `video-chunks` |
| `video-segment-land-trigger` | S3 Bucket | Bucket: `video-chunks-segments` |

---

### Step 3.2: Create Functions

Navigate to **DataEngine UI** → **Functions** and create:

| Function Name | Public Image |
|---------------|-----------------|
| `video-segmenter` | `vastdatasolutions/vde-video-segmenter:v1`|
| `video-reasoner` | `vastdatasolutions/vde-video-reasoner:v1` |
| `video-embedder` | `vastdatasolutions/vde-video-embedder:v1` |
| `video-vastdb-writer` | `vastdatasolutions/vde-vastdb-writer:v1` |

**Note:** Docker images are prebuilt and available on Docker Hub. If you need to push to a different registry, rebuild the images:
```bash
cd ingest/<function-folder>
vastde build -t <your-registry>/<image-name>:<tag> . --platform linux/amd64
docker push <your-registry>/<image-name>:<tag>
```
Then use your custom image in the DataEngine UI function creation.

---

### Step 3.3: Create Pipeline

Navigate to **DataEngine UI** → **Pipelines** → **Create New Pipeline**

**Pipeline Name:** `video-realtime-processing-pipeline`

Upload **ingest secret** configured in Part 1: `ingest/vde-video-ingest-secret-template.yaml`

**Add the following connections:**

1. **Segmentation Flow:**
   - Connect: `video-chunk-land-trigger` → `video-segmenter`

2. **Analysis Flow:**
   - Connect: `video-segment-land-trigger` → `video-reasoner`
   - Connect: `video-reasoner` → `video-embedder`
   - Connect: `video-embedder` → `video-vastdb-writer`

3. **Raise CPU / MEM Resources to All functions:**
   - CPU: `1000m - 5000m`
   - Memory: `1280Mi - 2560Mi`

**Save and activate the pipelines.**

---

## Part 4: Testing the Deployment

Now that everything is deployed, test the complete system end-to-end.

### Testing Steps

1. **Login to the GUI:**
   - Open `http://video-lab.<cluster_name>.vastdata.com` in your browser
   - Enter:
     - **Username**: Your VAST username
     - **S3 Secret Key**: Your S3 secret key (from VAST user management)
     - **VAST Host**: Your VAST VMS IP address
     - **Tenant Name**: Your tenant name (default: "default")
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

### Common Issues

**1. Cannot access the web UI:**
- Verify pods are running: `kubectl get pods -n vastvideo`
- Check ingress IP: `kubectl get ingress -n vastvideo`
- Verify `/etc/hosts` entry on your local machine (not on cluster)
- Try accessing by IP directly: `http://<INGRESS_IP>`

**2. Authentication fails:**
- Verify `s3_endpoint` in `backend-secret.yaml` matches your tenant's S3 endpoint
- Check backend logs for S3 validation errors
- Ensure tenant name is correct (case-sensitive)
- Verify user has S3 access keys enabled in VAST

**3. Search returns no results:**
- Check if videos have been processed (DataEngine UI → Executions)
- Verify VastDB connection in backend secret
- Check NVIDIA API key is valid
- Review backend logs for embedding/search errors

**4. Videos not processing:**
- Verify pipeline is Active in DataEngine UI
- Check S3 bucket names match in ingest secret
- Review function logs in DataEngine UI → Executions
- Verify Cosmos VLM endpoint is accessible

### View Logs

**Backend/Frontend:**
```bash
# Backend logs
kubectl logs -f -n vastvideo -l app=video-backend

# Frontend logs
kubectl logs -f -n vastvideo -l app=video-frontend

# Video streaming service logs
kubectl logs -f -n vastvideo -l app=video-stream-capture
```

**Ingest Functions (DataEngine UI):**
- Navigate to **DataEngine UI** → **Pipelines** → Click on pipeline → **Pipeline Logs** → View logs for each function 

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
                           │                                                  │           │
                           │                                                  ▼           │
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


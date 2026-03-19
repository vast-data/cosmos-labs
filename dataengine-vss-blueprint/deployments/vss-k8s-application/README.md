# Deploy K8s Application (Backend/Frontend)

Deploy the VSS Blueprint web application to Kubernetes.

## Prerequisites

- **Kubernetes access:**
  - `kubectl` installed and configured for your cluster
  - Ability to create namespaces and deploy resources

- **VAST cluster access:**
  - Cluster name (e.g., `v1234`) - used as part of the URL
  - Admin credentials for creating VMS manager user (see [User Authentication](../../source-code/retrieval/video-backend/README.md))

- **Storage resources:**
  - S3 buckets: `video-chunks` and `video-chunks-segments`
  - VastDB bucket: `processed-videos-db`

- **AI/ML services:**
  - NVIDIA NIM Endpoints or API key (for embeddings and LLM)

- **Network access:**
  - Ability to modify `/etc/hosts` on your local machine

---

## Step 1: Configure Backend Secret

Edit `backend-secret.yaml` with your credentials:

```bash
vim backend-secret.yaml
```

| Section | Key Settings |
|---------|--------------|
| **VastDB** | `vdb_endpoint`, `vdb_bucket`, `vdb_schema`, `vdb_collection`, credentials |
| **S3** | `s3_endpoint` (must match tenant), `s3_upload_bucket`, `s3_segments_bucket`, credentials |
| **NVIDIA** | `nvidia_api_key`, `embedding_model`, `llm_model_name`, `embedding_local_nim`, `llm_local_nim` |
| **VAST Admin** | `vast_admin_username`, `vast_admin_password` (for auth - see [setup](../../source-code/retrieval/video-backend/README.md#setup)) |

---

## Step 2: Docker Images

Pre-built images (ready to use):
- `vastdatasolutions/vde-video-backend:v1`
- `vastdatasolutions/vde-video-frontend:v1`
- `vastdatasolutions/vde-video-streaming:v1`
- `vastdatasolutions/vde-video-batch-sync:v1`

Add Docker Hub registry to your DataEngine tenant in VMS.

---

## Step 3: Deploy

```bash
./QUICK_DEPLOY.sh <namespace> <cluster_name>

# Example:
./QUICK_DEPLOY.sh vastvideo v1234
```

**What gets deployed:**
- Backend Service (FastAPI) - REST API
- Frontend Service (Angular) - Web UI
- Video Streaming Service - YouTube capture
- Video Batch Sync Service - S3 copy
- Ingress Resources - External access

---

## Step 4: Wait for Pods

```bash
kubectl get pods -n <namespace> -w
```

---

## Step 5: Configure DNS

Get ingress IP:
```bash
kubectl get ingress -n <namespace>
```

Add to `/etc/hosts` (on your local machine):
```
<INGRESS_IP> video-lab.<cluster_name>.vastdata.com
```

---

## Step 6: Access UI

```
http://video-lab.<cluster_name>.vastdata.com
```

---

## Troubleshooting

### Cannot access web UI
- Check pods: `kubectl get pods -n <namespace>`
- Check ingress: `kubectl get ingress -n <namespace>`
- Verify `/etc/hosts` entry

### Authentication fails
- Verify `s3_endpoint` matches tenant
- See [Auth Troubleshooting](../../source-code/retrieval/video-backend/README.md#troubleshooting)

### View Logs

```bash
# Backend
kubectl logs -f -n <namespace> -l app=video-backend

# Frontend  
kubectl logs -f -n <namespace> -l app=video-frontend

# Streaming
kubectl logs -f -n <namespace> -l app=video-stream-capture

# Batch Sync
kubectl logs -f -n <namespace> -l app=video-batch-sync
```

# VAST Research Assistant - Complete Deployment Guide

## Overview

The Research Assistant Agent system is a comprehensive RAG (Retrieval Augmented Generation) solution powered by VAST DataEngine. The system has two main parts:

1. **Backend (Agent) / Frontend (Kubernetes)** - User interface and API
2. **Ingest Pipeline (VAST DataEngine)** - Serverless document ingest functions



### Architecture

![Architecture Diagram](docs/architecture.png)

### System Components

- **Backend API**: FastAPI-based service powered by LLMs and RAG service (InsightEngine)
- **Frontend GUI**: Angular-based chat UI for prompting, and creating collections
- **Insight Engine**: Backend RAG service for document processing and retrieval
- **Serverless Pipeline**: VAST DataEngine pipeline for document ingestion
- **Storage**: VastDB for session and document management
- **Kubernetes**: Production-ready deployment configurations

The Backend RAG Service and Serverless Pipeline are powered by [InsightEngine](https://www.vastdata.com/platform/insightengine), checkout a [video overview of InsightEngine](https://www.youtube.com/watch?v=MD5q6x0wfXg).


## Prerequisites

Before starting, ensure you have:

### Kubernetes Access
- `kubectl` installed and configured for your remote cluster
- `KUBECONFIG` environment variable set (or default config at `~/.kube/config`)
- Ability to create namespaces and deploy resources

### VAST Cluster Access
- Enabled DataEngine on your k8s cluster
- Access to VAST DataEngine UI / CLI
- Cluster name (Any name you pick - e.g., `v3121`)
 - The cluster name can be application specific or arbitrary and will be used as part of the URL for accessing the application
 - So cluster name of `v209` will be used as part of the application URL (so `https://vast-researchv209.vastdata.com`)
- Admin credentials for creating VMS manager user
- (Optional) AzureAD connected to your cluster to use AzureAD identities (see Appendix A: Azure AD Configuration)

### AI/ML Services
- Preferred, NVIDIA Model Endpoint on local GPU
- Alternatively, NVIDIA NIM Endpoints with API key (for embeddings and LLM models)

### Network Access
- Your laptop/computer must be able to reach the Kubernetes cluster
- Ability to modify `/etc/hosts` (or Windows hosts file) on your local machine (or dns)

---

## Deployment Flow

Follow these steps in order:

1. **Part 1: Configuration** - Review and configure all secrets and images
2. **Part 2: Deploy InsightEngine & Serverless Pipeline** - Deploy Kubernetes services
3. **Part 3: Deploy Backend (Agent) & Frontend** - Deploy Kubernetes services
4. **Part 4: Testing** - Test the complete system

Note: For deploying the entire application, all deployment (steps 2, 3) will be done via scripts, and no DataEngine UI is required for creating triggers/pipelines.

---

## Part 1: Configuration

Before deploying, you need to configure secrets with your credentials. These secrets store sensitive information like API keys, database credentials, and S3 access keys.

**Configuration Files Location:**
- `configs/config.yaml` - InsightEngine and Serverless Pipeline configuration

### Step 1.1: Configure InsightEngine & Serverless Pipeline

Create or update `configs/config.yaml` with your environment-specific values :


```yaml
# InsightEngine Deployment Configuration
# ==========================================
# GLOBAL CONFIGURATION
# ==========================================
pipeline_name: "research-assistant"
kubernetes_cluster: "" #the `Name` of the Kubernetes Cluster for your specific tenant
vippool_host: ""
qe_vippool_host: "" #For querying vectors, you will need a different endpoint

# VAST Management System (VMS)
vms:
  host: "" # VMS IP address or hostname
  username: "" # VMS admin username
  password: "" # Override with VMS__PASSWORD env var
  dns_suffix: "" # DNS suffix for VIP pools

# DataEngine Configuration (used for serverless deployment)
dataengine:
  username: "" # User for deploying functions/pipelines
  password: "" # Override with DATAENGINE__PASSWORD env var
  tenant: "" # Tenant for DataEngine resources

# Deployment Settings (Shared between Backend and Serverless)
# These settings define the common infrastructure and naming for your deployment

# S3 Storage Configuration
- [ ] Add a optional fields
s3:
  user: "" # S3 user for deployment (will be created if not exists)
  bucket_name: "${pipeline_name}-bucket"
  vdb_schema: "${pipeline_name}-schema"
  view_policy: "s3_default_policy" # View policy for buckets
  access_key: "" # Set at runtime from credential generation
  secret_key: "" # Set at runtime from credential generation

deployment:
  name: "${pipeline_name}" # Deployment name (used for naming resources like VDB, Bucket)
  namespace: "${pipeline_name}" # Kubernetes Namespace
  cluster_name: "" # Cluster name for ingress (i.e. `research-assistant`)
  rotate_keys: false # Automatically rotate S3 keys if limit reached

# Database Migration Configuration
dbMigration:
  enabled: false  # Disable automatic database migration on deployment

# ==========================================
# MODELS CONFIGURATIONs
# ==========================================
models:
  # Shared DGX/GPU host for AI model services
  # This is the primary host where NVIDIA NIMs and AI models are deployement
  # host can be local ip for your GPU server or can be set to nvidia.api.cloud for remote NIMs
  dgx_host: ""

  llm:
    - model_name: "meta/llama-3.1-8b-instruct"
      host: ""
      port: 
      http_scheme: "http"
      default: true

  embedding:
    - model_name: "nvidia/llama-3.2-nv-embedqa-1b-v2"
      host: ""
      port: 
      http_scheme: "http"
      dimensions: 2048
      default: true

  reranker:
    - model_name: "nvidia/llama-3.2-nv-rerankqa-1b-v2"
      host: ""
      port: 
      http_scheme: "http"
      default: true

# ==========================================
# BACKEND CONFIGURATION
# ==========================================
backend:
  image:
    repository: "docker.io/vastdataorg/insight-engine"
    tag: "backend-efd662aa"
    pullPolicy: "IfNotPresent"


  # OAuth2 Configuration
  oauth2:
    sam_account_domain: "aad-vasteng.lab" # SAM account domain for Active Directory

  # OpenTelemetry Configuration (Observability)
  monitoring:
    otel:
      endpoint: "http://otel-collector.monitoring.svc.cluster.local:4317"
      insecure: "true"
      service_name: "backend-webserver"

# ==========================================
# COLLECTIONUI CONFIGURATION
# ==========================================
collectionsui:
  image:
    repository: "docker.io/vastdataorg/insight-engine"
    tag: "collections-ui-efd662aa"
    pullPolicy: "IfNotPresent"

# ==========================================
# SERVERLESS CONFIGURATION
# ==========================================
serverless:
  with_media: false # Include media ingestion function (set to false to deploy only document ingestion)

  image:
    repository: "vastdataorg/insight-engine"
    tag: "serverless-ingest-efd662aa"
    registry: "dockerio"

  # Ingestion Settings
  ingestion:
    chunk_size: "500"
    chunk_overlap: "25"
    max_tokens: "8192"

  # NVIDIA Ingest Service (for Media Mode)
  nvingest:
    host: "nv-ingest.nv-ingest.svc.cluster.local"
    port: "7670"
    scheme: "https"

  # OpenTelemetry Configuration (Observability)
  monitoring:
    otel:
      endpoint: "http://otel-collector.monitoring.svc.cluster.local:4317"
      insecure: "true"
      service_name: "serverless-ingestion"
```

Additionally, create a secrets file with sensitive values (optional):
```bash
# ==========================================
# GLOBAL SETTINGS
# ==========================================
VMS__PASSWORD= "<VMS_ADMIN_PASSWORD>"

DATAENGINE__PASSWORD= "<APP_USER_PASSWORD>"

NV_USERNAME= # for nv-ingest - optional
NV_PASSWORD= # for nv-ingest - optional

```
### Step 1.2: Configure Backend (Agent) and Frontend

AzureAD fields relevant only if you want to use AzureAD for authentication (if you are using it add your https certificate to the cluster and link it to the service)
```bash


# Agent Configuration
AGENT_TEMPERATURE=0.15
AGENT_MARKDOWN=true
AGENT_NAME=ResearchAssistant

# RAG Backend Configuration
# Using research-assistant namespace for all components
RAG_BASE_URL=http://backend-webserver.research-assistant:8080
RAG_SSL_VERIFY=false
RAG_TIMEOUT=60.0

# VastDB Configuration
VASTDB_ENDPOINT=
VASTDB_ACCESS_KEY=
VASTDB_SECRET_KEY=

- [ ] Make a note to test out S3 bucket created with s3cmd commands

# API Configuration
API_TITLE=Research Assistant API
API_DESCRIPTION=API for research assistant with RAG backend integration
API_VERSION=1.0.0

# LLM Configuration
AGENT_OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1 # or local NIM
AGENT_OPENAI_MODEL_ID=meta/llama-3.3-70b-instruct
AGENT_OPENAI_API_KEY=
AUTH__AZURE__CLIENTID= # Optional
AUTH__AZURE__CLIENTSECRET= # Optional
AUTH__AZURE__NEXTAUTHSECRET= # Optional
AUTH__AZURE__AUTHORIZATIONENDPOINT= # Optional
AUTH__AZURE__TOKENENDPOINT= # Optional
AUTH__AZURE__ISSUERENDPOINT= # Optional
AUTH__AZURE__JWKSENDPOINT= # Optional
AUTH__AZURE__REDIRECTURI= # Optional
AUTH__AZURE__NEXTAUTHURL= # Optional
```

---

## Part 2: Deploy InsightEngine & Serverless Pipeline

### Step 2.0: Prepare Cluster
```bash
docker run --rm --network host \
  -v <YOUR_KUBECONFIG_PATH>:/root/.kube/config:ro \
  -v ./configs/config.yaml:/workspace/config.yaml:ro \
  -e IE_CONFIG_FILE=/workspace/config.yaml \
  -e ENV=default \
  vastdataorg/insight-engine-deploy:724b4600 task setup-cluster
```

### Step 2.1: Install InsightEngine

```bash
docker run --rm --network host \
  -v <YOUR_KUBECONFIG_PATH>:/root/.kube/config:ro \
  -v ./configs/config.yaml:/workspace/config.yaml:ro \
  -e IE_CONFIG_FILE=/workspace/config.yaml \
  -e ENV=default \
  vastdataorg/insight-engine-deploy:724b4600 task deploy:backend
```

#### Sanity Check — `deploy:backend`

After running the command above, verify that the backend pods are running:

```bash
kubectl get pods -n research-assistant
```

Expected output:

```
NAME                                      READY   STATUS    RESTARTS   AGE
backend-collections-ui-7875d7d7b4-kc4cl   1/1     Running   0          8d
backend-webserver-85999c6d5f-m7mcb        1/1     Running   0          43h
```

> Both `backend-collections-ui` and `backend-webserver` pods should be in **Running** status with **1/1** ready.

### Step 2.2: Install Serverless Pipeline

```bash
docker run --rm --network host \
  -v <YOUR_KUBECONFIG_PATH>:/root/.kube/config:ro \
  -v ./configs/config.yaml:/workspace/config.yaml:ro \
  -e IE_CONFIG_FILE=/workspace/config.yaml \
  -e ENV=default \
  vastdataorg/insight-engine-deploy:724b4600 task deploy:serverless
```

#### Sanity Check — `deploy:serverless`

After running the command above, verify that triggers, functions, and the pipeline were created:

```bash
vastde triggers list
```

Expected output:

```
Trigger Name               Status        Type        Description              GUID                                    Updated at
--------------------------------------------------------------------------------------------------------------------------------------
src-cpy-trigger            Ready         Element                              d106c562-48d7-401e-a416-0a3d353675af    2026-01-26 07:28
update-vector-db-resea...  Ready         Element                              a4ab25b7-b2cf-467e-8b8b-d5c50ac4df31    2026-02-09 13:30
```

```bash
vastde functions list
```

Expected output:

```
Function Name              Description                          Guid                                    Updated at
---------------------------------------------------------------------------------------------------------------------------
copy-function                                                   791d2d93-1104-451f-9d89-30c447668050    2026-01-26 07:29
ingest-research-assistant                                       ce932505-5ca1-4e27-bb7e-5b7e1d1faabf    2026-02-09 13:30
```

```bash
vastde pipelines list
```

Expected output:

```
Pipeline Name              Status        Description                     Guid                                    Updated at
------------------------------------------------------------------------------------------------------------------------------------
research-assistant         Ready                                         f1ff23f0-1cae-4eed-9bfc-29f447807837    2026-02-10 10:09
```

> All triggers should be **Ready**, both functions should be listed, and the pipeline status should be **Ready**.

---

## Part 3: Deploy Backend (Agent) & Frontend

### Step 3.1: Build and Push Docker Images (Optional)

```bash
# From project root
cd backend
docker buildx build --platform linux/amd64 -t <YOUR_REGISTRY>/research-assistant:your-tag --push .

cd ../gui
docker buildx build --platform linux/amd64 -t <YOUR_REGISTRY>/research-assistant-gui:your-tag --push .
```


### Step 3.2: Generate Kubernetes Manifests

```bash
cd k8s/
./generate-from-env.sh -e ../.env

# This creates:
#   - configmap.yaml (non-sensitive config)
#   - secret.yaml (sensitive credentials, base64 encoded)
```

### Step 3.3: Install the Deployment

```bash
./install.sh \
  -n research-assistant \
  -r <YOUR_REGISTRY> \
  -t <YOUR_TAG> \
  -s secret.yaml \
  -c <YOUR_CLUSTER_NAME> \
  -g <YOUR_GUI_HOSTNAME> \
  --tls-secret <YOUR_TLS_SECRET> \
  -i
```

- [ ] brew install gettext, brew link --force gettext on macs

**Example (with secret file):**
```bash
./install.sh \
  -n research-assistant \
  -r docker.io/vastdatasolutions \
  -t v1 \
  -s secret.yaml \
  -c v151 \
  -g vast-research151.vastdata.com \
  --tls-secret research-assistant-wildcard \
  -i
```

**Example (without secret file - uses existing secret):**
```bash
./install.sh \
  -n research-assistant \
  -r docker.io/vastdatasolutions \
  -t v1 \
  -c v151 \
  -g vast-research151.vastdata.com \
  -i
```

#### Sanity Check — `install.sh`

After running the install script, verify that all pods are running:

```bash
kubectl get pods -n research-assistant
```

Expected output:

```
NAME                                      READY   STATUS    RESTARTS   AGE
backend-collections-ui-7875d7d7b4-kc4cl   1/1     Running   0          8d
backend-webserver-85999c6d5f-m7mcb        1/1     Running   0          43h
research-assistant-7cf7fb8f8b-2pllw       1/1     Running   0          4h14m
research-assistant-gui-78598467bc-rbt8w   1/1     Running   0          3h9m
```

> In addition to the backend pods, you should now see `research-assistant` (the agent) and `research-assistant-gui` (the frontend) pods in **Running** status.

Verify that the configmaps and secrets were created:

```bash
kubectl get configmap -n research-assistant
```

Expected output:

```
NAME                        DATA   AGE
kube-root-ca.crt            1      8d
llms-config                 1      8d
research-assistant-config   17     8d
```

```bash
kubectl get secret -n research-assistant
```

Expected output:

```
NAME                            TYPE                             DATA   AGE
ecr-pull-secret                 kubernetes.io/dockerconfigjson   1      19h
research-assistant-secrets      Opaque                           7      8d
research-assistant-wildcard     kubernetes.io/tls                2      8d
sh.helm.release.v1.backend.v1   helm.sh/release.v1               1      8d
vast-mgmt                       Opaque                           1      8d
```

> The `research-assistant-config` configmap and `research-assistant-secrets` secret must be present. The `research-assistant-wildcard` TLS secret is required for HTTPS ingress.

### Install Script Options

```bash
./install.sh [OPTIONS]

Options:
  -n, --namespace <namespace>    Kubernetes namespace (default: research-assistant)
  -r, --registry <registry>      Docker registry URL (required)
  -t, --tag <tag>                Image tag (default: latest)
  -s, --secret-file <file>       Path to secret.yaml file (optional, skips if not provided)
  -c, --cluster <cluster_name>   Cluster name for agent ingress (e.g., v151)
  -g, --gui-host <hostname>      GUI hostname for HTTPS (e.g., vast-research151.vastdata.com)
  --tls-secret <secret>          TLS secret name (default: research-assistant-wildcard)
  -i, --ingress                  Enable ingress (requires --cluster and --gui-host)
  -d, --dry-run                  Show what would be applied without applying
  -u, --uninstall                Uninstall the deployment
  -h, --help                     Show help message
```


### Step 3.4: Configure DNS/Hosts

Add the following to `/etc/hosts`:
```
<ingress-controller-ip> agent.<YOUR_CLUSTER_NAME> vast-research<YOUR_CLUSTER_NAME>.vastdata.com
```

---

## Part 4: Testing

### Step 4.1: Verify Pods are Running

```bash
# Check all pods in research-assistant namespace
# (Both Research Assistant and InsightEngine are deployed here)
kubectl get pods -n research-assistant

# All pods should be in "Running" state
```

### Step 4.2: Verify Services and Ingress

```bash
kubectl get svc -n research-assistant
kubectl get ingress -n research-assistant
```

### Step 4.3: Test Backend API

```bash
# Test health endpoint
curl http://agent.v3121/health

# Test API documentation
curl http://agent.v3121/docs
```

### Step 4.4: Test Frontend GUI

Open browser: `https://<YOUR_GUI_HOSTNAME>` (e.g., `https://vast-research151.vastdata.com`)

### Step 4.5: View Logs

```bash
# Backend logs
kubectl logs -f deployment/research-assistant -n research-assistant

# Frontend logs
kubectl logs -f deployment/research-assistant-gui -n research-assistant
```

---

## Configuration Reference

### Kubernetes Files

| File | Description |
|------|-------------|
| `k8s/configmap.yaml` | Non-sensitive configuration (templated) |
| `k8s/secret.yaml` | Sensitive credentials (base64 encoded) |
| `k8s/deployment.yaml` | Backend deployment specification |
- [ ] File does not exist, is this `service-gui`
| `k8s/gui-deployment.yaml` | GUI deployment specification |
- [ ] File does not exist, is this `deployment-gui`
| `k8s/service.yaml` | Kubernetes services |
| `k8s/ingress.yaml` | Ingress for agent and GUI |
| `k8s/install.sh` | Installation script |

### ConfigMap Variables (Templated)

All components use `research-assistant` as the default namespace.

| Variable | Description | Example |
|----------|-------------|---------|
| `RAG_BASE_URL` | RAG backend URL | `http://backend-webserver.research-assistant:8080` |
| `VASTDB_BUCKET` | VastDB bucket name | `research-assistant-bucket` |
| `VASTDB_SCHEMA` | VastDB schema name | `research-assistant-schema` |
| `AUTH__AZURE__REDIRECTURI` | Azure AD callback URL | `https://${GUI_HOST}/api/auth/callback/nvlogin` |
| `AUTH__AZURE__NEXTAUTHURL` | Frontend URL | `https://${GUI_HOST}` |

### Secret Keys

| Key | Description |
|-----|-------------|
| `AGENT_OPENAI_API_KEY` | NVIDIA/OpenAI API key for LLM |
| `VASTDB_ENDPOINT` | VastDB endpoint URL |
| `VASTDB_ACCESS_KEY` | VastDB access key |
| `VASTDB_SECRET_KEY` | VastDB secret key |
| `AUTH__AZURE__CLIENTID` | Azure AD application client ID (optional) |
| `AUTH__AZURE__CLIENTSECRET` | Azure AD client secret (optional) |
| `AUTH__AZURE__NEXTAUTHSECRET` | NextAuth session secret (optional) |


### Encoding Secrets

```bash
# Encode a value
echo -n "your-value" | base64

# Decode to verify
echo "eW91ci12YWx1ZQ==" | base64 -d
```

---

## Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod -l app=research-assistant -n research-assistant
   kubectl get events -n research-assistant --sort-by='.lastTimestamp'
   ```

2. **Secret values are empty**
   ```bash
   cd k8s && ./generate-from-env.sh -e ../.env
   kubectl get secret research-assistant-secrets -n research-assistant -o yaml
   ```

3. **Connection issues between services**
   ```bash
   kubectl get svc -n research-assistant
   kubectl run test --rm -it --image=curlimages/curl -- curl http://research-assistant:8000/health
   ```

4. **VastDB connection issues**
   - Verify `VASTDB_ENDPOINT` is correct
   - Check VastDB credentials in secret
   - Test connectivity from pod

5. **Azure AD login issues**
   - Verify `AUTH__AZURE__CLIENTID` and `AUTH__AZURE__CLIENTSECRET` are set
   - Check `AUTH__AZURE__REDIRECTURI` matches your GUI host
   - Ensure deployment has Azure env vars referenced from secret

---

## Uninstall

```bash
./install.sh -n research-assistant -u
```

---

## Appendix A: Azure AD Configuration

If you want to use Azure AD for user authentication, follow these additional steps in the VAST Management Console.

### A.1: Add Azure AD as Identity Provider for Tenant

1. Navigate to **Configuration** → **Tenants**
2. Select your tenant (e.g., `default`)
3. Click **Edit** or open tenant settings
4. In the **Identity Providers** section, add **Azure AD** as a provider
5. Save the tenant configuration

### A.2: Create Identity Policy for Azure AD Users

1. Navigate to **Configuration** → **Identity Policies**
2. Click **Create New Policy**
3. Configure the policy:
   - **Name**: `AllowS3All`
   - **Provider**: Azure AD
   - **Users/Groups**: Add the Azure AD groups or users that need access
   - **Permissions**: Grant S3 access permissions
4. Save the policy

> **Note**: The `AllowS3All` identity policy allows Azure AD authenticated users to access S3 buckets. Make sure to assign the appropriate Azure AD groups/users that should have access to the Research Assistant data.

---

## Appendix B: SyncEngine Collections

If you want to use SyncEngine collections (e.g., Confluence sync), you need to manually create the collection via the InsightEngine backend API.

### B.1: Create SyncEngine Collection

Send a POST request to the backend API to create the collection:

```bash
curl -X POST "http://<BACKEND_INGRESS>/api/v1/collections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <SUPER_ADMIN_JWT_TOKEN>" \
  -d '{
    "collection_names": ["syncengine.<YOUR_SYNC_NAME>"],
    "is_public": true,
    "allowed_groups": ["*"],
    "allowed_users": ["*"]
  }'
```

**Parameters:**
- `<BACKEND_INGRESS>`: The InsightEngine backend ingress URL (e.g., `backend-webserver.research-assistant.svc.cluster.local:8080` or external ingress)
- `<SUPER_ADMIN_JWT_TOKEN>`: A valid JWT token with SUPER_ADMIN privileges
- `syncengine.<YOUR_SYNC_NAME>`: The collection name matching your SyncEngine configuration (e.g., `syncengine.solutions` for Confluence)
- `is_public`: Set to `true` for public access or `false` for restricted access
- `allowed_groups` / `allowed_users`: Use `["*"]` for all users or specify specific groups/users

**Example for Confluence Solutions:**
```bash
curl -X POST "http://backend-webserver.research-assistant:8080/api/v1/collections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "collection_names": ["syncengine.solutions"],
    "is_public": true,
    "allowed_groups": ["*"],
    "allowed_users": ["*"]
  }'
```

> **Note**: The SyncEngine must be configured separately in VAST to sync data from external sources (e.g., Confluence, SharePoint) into the collection.

# Deploy InsightEngine & Serverless Pipeline

Deploy the InsightEngine RAG backend and serverless document ingestion pipeline.

## Prerequisites

- **Kubernetes access:**
  - `kubectl` installed and configured for your cluster
  - VAST DataEngine enabled on your k8s cluster

- **VAST cluster access:**
  - VMS admin credentials
  - Access to VAST DataEngine UI / CLI

- **AI/ML services:**
  - NVIDIA NIM Endpoints (embedding, reranker, LLM)

---

## Step 1: Configure

Edit `config.yaml` with your environment-specific values (use `config.template` as a starting point):

| Section | Key Settings |
|---------|--------------|
| **VMS** | `host`, `username`, `password`, `dns_suffix` |
| **DataEngine** | `username`, `password`, `tenant` |
| **S3** | `s3_user`, `vip_pool`, `access_key`, `secret_key` |
| **Models** | `dgx_host`, LLM/embedding/reranker model configs |
| **Deployment** | `name`, `namespace`, `cluster_name` |

---

## Step 2: Prepare Cluster

```bash
docker run --rm --network host \
  -v <YOUR_KUBECONFIG_PATH>:/root/.kube/config:ro \
  -v ./config.yaml:/workspace/config.yaml:ro \
  -e IE_CONFIG_FILE=/workspace/config.yaml \
  -e ENV=default \
  vastdataorg/insight-engine-deploy:724b4600 task setup-cluster
```

---

## Step 3: Deploy InsightEngine Backend

```bash
docker run --rm --network host \
  -v <YOUR_KUBECONFIG_PATH>:/root/.kube/config:ro \
  -v ./config.yaml:/workspace/config.yaml:ro \
  -e IE_CONFIG_FILE=/workspace/config.yaml \
  -e ENV=default \
  vastdataorg/insight-engine-deploy:724b4600 task deploy:backend
```

Verify:
```bash
kubectl get pods -n research-assistant
# Expected: backend-collections-ui and backend-webserver in Running status
```

---

## Step 4: Deploy Serverless Pipeline

```bash
docker run --rm --network host \
  -v <YOUR_KUBECONFIG_PATH>:/root/.kube/config:ro \
  -v ./config.yaml:/workspace/config.yaml:ro \
  -e IE_CONFIG_FILE=/workspace/config.yaml \
  -e ENV=default \
  vastdataorg/insight-engine-deploy:724b4600 task deploy:serverless
```

Verify:
```bash
vastde triggers list    # Should show triggers in Ready status
vastde functions list   # Should show ingest function
vastde pipelines list   # Should show pipeline in Ready status
```

---

## What Gets Deployed

- **Backend Webserver**: InsightEngine REST API for document retrieval and collection management
- **Collections UI**: Web UI for managing collections
- **Serverless Pipeline**: Document ingestion functions (chunking, embedding, storage)
- **Triggers**: Automatic ingestion on document upload to S3

---

## Troubleshooting

### Backend pods not starting
```bash
kubectl describe pod -l app=backend-webserver -n research-assistant
```

### Pipeline not triggering
```bash
vastde triggers list
vastde pipelines list
```

### View Logs
```bash
kubectl logs -f -l app=backend-webserver -n research-assistant
kubectl logs -f -l app=backend-collections-ui -n research-assistant
```

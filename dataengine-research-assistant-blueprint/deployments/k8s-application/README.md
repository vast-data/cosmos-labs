# Deploy K8s Application (Backend/Frontend)

Deploy the Research Assistant web application to Kubernetes.

## Prerequisites

- **Kubernetes access:**
  - `kubectl` installed and configured for your cluster
  - Ability to create namespaces and deploy resources

- **VAST cluster access:**
  - Cluster name (e.g., `v151`) - used as part of the URL
  - InsightEngine backend already deployed (see [insight-engine-pipeline](../insight-engine-pipeline/README.md))

- **AI/ML services:**
  - NVIDIA NIM Endpoints or API key (for LLM inference)

- **Network access:**
  - Ability to modify `/etc/hosts` on your local machine

---

## Step 1: Configure Secrets

Edit `.env` with your credentials (or use `.env.template` as a starting point):

| Section | Key Settings |
|---------|--------------|
| **VastDB** | `VASTDB_ENDPOINT`, `VASTDB_ACCESS_KEY`, `VASTDB_SECRET_KEY` |
| **RAG** | `RAG_BASE_URL` (InsightEngine backend) |
| **NVIDIA** | `AGENT_OPENAI_API_KEY`, `AGENT_OPENAI_BASE_URL`, `AGENT_OPENAI_MODEL_ID` |
| **Azure AD** | `AUTH__AZURE__*` keys (optional, for SSO) |

---

## Step 2: Generate Kubernetes Manifests

```bash
# From deployments/k8s-application/
./generate-from-env.sh -e .env

# This creates (in the same directory):
#   - configmap.yaml (non-sensitive config)
#   - secret.yaml (sensitive credentials, base64 encoded)
```

---

## Step 3: Deploy

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

**Example:**
```bash
./install.sh \
  -n research-assistant \
  -r docker.io/vastdatasolutions \
  -t v2 \
  -s secret.yaml \
  -c v151 \
  -g vast-research151.vastdata.com \
  --tls-secret research-assistant-wildcard \
  -i
```

**What gets deployed:**
- Backend Service (FastAPI) - Agent API
- Frontend Service (Angular) - Chat UI
- Ingress Resources - External access

---

## Step 4: Wait for Pods

```bash
kubectl get pods -n research-assistant -w
```

Expected:
```
NAME                                      READY   STATUS    RESTARTS   AGE
backend-collections-ui-xxx                1/1     Running   0          8d
backend-webserver-xxx                     1/1     Running   0          8d
research-assistant-xxx                    1/1     Running   0          5m
research-assistant-gui-xxx                1/1     Running   0          5m
```

---

## Step 5: Configure DNS

Get ingress IP:
```bash
kubectl get ingress -n research-assistant
```

Add to `/etc/hosts`:
```
<INGRESS_IP> agent.<cluster_name> vast-research<cluster_name>.vastdata.com
```

---

## Step 6: Access UI

```
https://<YOUR_GUI_HOSTNAME>
```

---

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod -l app=research-assistant -n research-assistant
kubectl get events -n research-assistant --sort-by='.lastTimestamp'
```

### View Logs
```bash
# Backend
kubectl logs -f deployment/research-assistant -n research-assistant

# Frontend
kubectl logs -f deployment/research-assistant-gui -n research-assistant
```

### Uninstall
```bash
./install.sh -n research-assistant -u
```

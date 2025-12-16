#!/bin/bash
# Quick Deployment Script for Video Reasoning Lab
# Usage: cd k8s && ./QUICK_DEPLOY.sh <cluster_name>

set -e

echo "🚀 Video Reasoning Lab - Quick Deploy"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if cluster name is provided
if [ -z "$1" ]; then
  echo -e "${RED}Error: Cluster name is required${NC}"
  echo ""
  echo "Usage: ./QUICK_DEPLOY.sh <cluster_name>"
  echo "Example: ./QUICK_DEPLOY.sh v1234"
  echo ""
  exit 1
fi

# Configuration
NAMESPACE="vastvideo"
CLUSTER_NAME="$1"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl not found${NC}"; exit 1; }
echo -e "${GREEN}✓ All prerequisites found${NC}"
echo ""

echo -e "${YELLOW}Cluster Configuration:${NC}"
echo "  Cluster Name: $CLUSTER_NAME"
echo "  Namespace:    $NAMESPACE"
echo ""

# Step 1: Create Namespace
echo -e "${YELLOW}Step 1/7: Creating namespace...${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl label ns $NAMESPACE zarf.dev/agent=ignore
echo -e "${GREEN}✓ Namespace ready${NC}"
echo ""

# Step 2: Create Secret
echo -e "${YELLOW}Step 2/7: Creating backend secret...${NC}"
kubectl apply -f backend-secret.yaml
echo -e "${GREEN}✓ Secret created${NC}"
echo ""

# Step 3: Create ConfigMaps
echo -e "${YELLOW}Step 3/7: Creating configmaps...${NC}"
kubectl apply -f frontend-config.yaml
echo -e "${GREEN}✓ ConfigMaps created${NC}"
echo ""

# Step 4: Deploy Backend (includes backend ingress)
echo -e "${YELLOW}Step 4/7: Deploying backend...${NC}"
sed "s/CLUSTER_NAME/$CLUSTER_NAME/g" backend-deployment.yaml | kubectl apply -f -
echo -e "${GREEN}✓ Backend deployed${NC}"
echo ""

# Step 5: Deploy Frontend (includes frontend ingress)
echo -e "${YELLOW}Step 5/7: Deploying frontend...${NC}"
sed "s/CLUSTER_NAME/$CLUSTER_NAME/g" frontend-deployment.yaml | kubectl apply -f -
echo -e "${GREEN}✓ Frontend deployed${NC}"
echo ""

# Step 6: Deploy Video Streaming
echo -e "${YELLOW}Step 6/7: Deploying video streaming service...${NC}"
sed "s/CLUSTER_NAME/$CLUSTER_NAME/g" videostreamer-deployment.yaml | kubectl apply -f -
echo -e "${GREEN}✓ Video streaming service deployed${NC}"
echo ""

# Step 7: Verify ConfigMaps
echo -e "${YELLOW}Step 7/7: Verifying configuration...${NC}"
kubectl get configmap -n $NAMESPACE
echo -e "${GREEN}✓ Configuration verified${NC}"
echo ""

# Get Ingress IP
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Deployment Status:"
kubectl get all -n $NAMESPACE
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access Information:"
echo ""
INGRESS_IP=$(kubectl get ingress video-frontend-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "$INGRESS_IP" == "pending" ] || [ -z "$INGRESS_IP" ]; then
  echo -e "${YELLOW}⏳ Ingress IP is still pending...${NC}"
  echo "   Run this to check: kubectl get ingress -n $NAMESPACE"
else
  echo -e "${GREEN}Ingress IP: $INGRESS_IP${NC}"
fi
echo ""
echo "Add to /etc/hosts:"
echo -e "${YELLOW}  $INGRESS_IP video-lab.$CLUSTER_NAME.vastdata.com${NC}"
echo -e "${YELLOW}  $INGRESS_IP video-streamer.$CLUSTER_NAME.vastdata.com${NC}"
echo ""
echo "Then access:"
echo -e "${GREEN}  http://video-lab.$CLUSTER_NAME.vastdata.com${NC} (Main Video Lab)"
echo -e "${GREEN}  http://video-streamer.$CLUSTER_NAME.vastdata.com${NC} (Video Streaming Service)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next Steps:"
echo "  1. Wait for pods to be ready:"
echo "     kubectl get pods -n $NAMESPACE -w"
echo "  2. Add Ingress IP to /etc/hosts"
echo "     X.X.X.X video-streamer.$CLUSTER_NAME.vastdata.com"
echo "  3. Open http://video-lab.$CLUSTER_NAME.vastdata.com"
echo "  4. Login with VAST credentials"
echo "  5. Access video streaming at http://video-streamer.$CLUSTER_NAME.vastdata.com"
echo ""
echo "🔍 View Logs:"
echo "  Backend:         kubectl logs -f -n $NAMESPACE -l app=video-backend"
echo "  Frontend:        kubectl logs -f -n $NAMESPACE -l app=video-frontend"
echo "  Video Streaming: kubectl logs -f -n $NAMESPACE -l app=video-stream-capture"
echo ""


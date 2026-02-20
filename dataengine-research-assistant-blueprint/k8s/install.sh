#!/bin/bash
#
# Research Assistant - Kubernetes Installation Script
#
# Usage:
#   ./install.sh [OPTIONS]
#
# Options:
#   -n, --namespace <namespace>    Kubernetes namespace (default: research-assistant)
#   -r, --registry <registry>      Docker registry URL (required)
#   -t, --tag <tag>                Image tag (default: latest)
#   -s, --secret-file <file>       Path to secret.yaml file (optional, skips if not provided)
#   -c, --cluster <cluster_name>   Cluster name for ingress (e.g., v151)
#   -g, --gui-host <hostname>      GUI hostname (e.g., vast-research151.vastdata.com)
#   --tls-secret <secret>          TLS secret name for HTTPS (default: research-assistant-wildcard)
#   -i, --ingress                  Enable ingress (requires --cluster)
#   -d, --dry-run                  Show what would be applied without applying
#   -u, --uninstall                Uninstall the deployment
#   -h, --help                     Show this help message
#
# Example:
#   ./install.sh -n research-assistant -r myregistry.azurecr.io -t v1.0.0 -s secret.yaml -c v151 -g vast-research151.vastdata.com --tls-secret research-assistant-wildcard -i

set -e

# Default values
NAMESPACE="research-assistant"
IMAGE_TAG="latest"
DOCKER_REGISTRY=""
SECRET_FILE=""
CLUSTER_NAME=""
GUI_HOST=""
TLS_SECRET="research-assistant-wildcard"
ENABLE_INGRESS=false
DRY_RUN=""
UNINSTALL=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Help function
show_help() {
    head -26 "$0" | tail -23 | sed 's/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -s|--secret-file)
            SECRET_FILE="$2"
            shift 2
            ;;
        -c|--cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        -g|--gui-host)
            GUI_HOST="$2"
            shift 2
            ;;
        --tls-secret)
            TLS_SECRET="$2"
            shift 2
            ;;
        -i|--ingress)
            ENABLE_INGRESS=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN="--dry-run=client"
            shift
            ;;
        -u|--uninstall)
            UNINSTALL=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            error "Unknown option: $1. Use -h for help."
            ;;
    esac
done

# Uninstall mode
if [ "$UNINSTALL" = true ]; then
    info "Uninstalling Research Assistant from namespace: $NAMESPACE"
    
    # Delete ingresses
    kubectl delete ingress research-assistant-ingress -n "$NAMESPACE" --ignore-not-found
    kubectl delete ingress research-assistant-gui-ingress -n "$NAMESPACE" --ignore-not-found
    
    # Delete deployments
    kubectl delete deployment research-assistant -n "$NAMESPACE" --ignore-not-found
    kubectl delete deployment research-assistant-gui -n "$NAMESPACE" --ignore-not-found
    
    # Delete services
    kubectl delete service research-assistant -n "$NAMESPACE" --ignore-not-found
    kubectl delete service research-assistant-gui -n "$NAMESPACE" --ignore-not-found
    
    # Delete config and secrets
    kubectl delete configmap research-assistant-config -n "$NAMESPACE" --ignore-not-found
    kubectl delete secret research-assistant-secrets -n "$NAMESPACE" --ignore-not-found
    
    info "Deleting namespace: $NAMESPACE"
    kubectl delete namespace "$NAMESPACE" --ignore-not-found
    
    info "Uninstallation complete!"
    exit 0
fi

# Validate required arguments
if [ -z "$DOCKER_REGISTRY" ]; then
    error "Docker registry is required. Use -r or --registry."
fi

# Secret file is optional - if provided, validate it exists
if [ -n "$SECRET_FILE" ] && [ ! -f "$SECRET_FILE" ]; then
    error "Secret file not found: $SECRET_FILE"
fi

# Validate ingress requirements
if [ "$ENABLE_INGRESS" = true ] && [ -z "$CLUSTER_NAME" ]; then
    error "Cluster name is required when ingress is enabled. Use -c or --cluster."
fi

# Check for kubectl
if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed or not in PATH"
fi

# Check kubectl connection
info "Checking Kubernetes connection..."
if ! kubectl cluster-info &> /dev/null; then
    error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
fi

info "=========================================="
info "Research Assistant - Kubernetes Installer"
info "=========================================="
info "Namespace:  $NAMESPACE"
info "Registry:   $DOCKER_REGISTRY"
info "Image Tag:  $IMAGE_TAG"
if [ -n "$SECRET_FILE" ]; then
    info "Secret:     $SECRET_FILE"
else
    info "Secret:     (not provided - using existing)"
fi
if [ "$ENABLE_INGRESS" = true ]; then
    info "API Ingress:  agent.$CLUSTER_NAME"
    if [ -n "$GUI_HOST" ]; then
        info "GUI Ingress:  https://$GUI_HOST"
        info "TLS Secret:   $TLS_SECRET"
    fi
fi
info "=========================================="

# Create namespace if it doesn't exist
info "Creating namespace: $NAMESPACE"
kubectl create namespace "$NAMESPACE" $DRY_RUN --dry-run=client -o yaml | kubectl apply -f - $DRY_RUN

# Apply ConfigMap
info "Applying ConfigMap..."
kubectl apply -f "$SCRIPT_DIR/configmap.yaml" -n "$NAMESPACE" $DRY_RUN

# Apply Secret (if provided)
if [ -n "$SECRET_FILE" ]; then
    info "Applying Secret..."
    kubectl apply -f "$SECRET_FILE" -n "$NAMESPACE" $DRY_RUN
else
    warn "No secret file provided. Skipping secret creation."
    warn "Make sure 'research-assistant-secrets' already exists in namespace '$NAMESPACE'."
fi

# Export variables for envsubst
export DOCKER_REGISTRY
export IMAGE_TAG
export CLUSTER_NAME
export GUI_HOST
export TLS_SECRET

# Apply Backend Deployment (with variable substitution)
info "Applying Backend Deployment..."
envsubst '${DOCKER_REGISTRY} ${IMAGE_TAG}' < "$SCRIPT_DIR/deployment.yaml" | kubectl apply -f - -n "$NAMESPACE" $DRY_RUN

# Apply Backend Service
info "Applying Backend Service..."
kubectl apply -f "$SCRIPT_DIR/service.yaml" -n "$NAMESPACE" $DRY_RUN

# Apply GUI Deployment (with variable substitution)
info "Applying GUI Deployment..."
envsubst '${DOCKER_REGISTRY} ${IMAGE_TAG}' < "$SCRIPT_DIR/deployment-gui.yaml" | kubectl apply -f - -n "$NAMESPACE" $DRY_RUN

# Apply GUI Service
info "Applying GUI Service..."
kubectl apply -f "$SCRIPT_DIR/service-gui.yaml" -n "$NAMESPACE" $DRY_RUN

# Apply Ingress if enabled
if [ "$ENABLE_INGRESS" = true ]; then
    info "Applying Ingress..."
    envsubst '${CLUSTER_NAME} ${GUI_HOST} ${TLS_SECRET}' < "$SCRIPT_DIR/ingress.yaml" | kubectl apply -f - -n "$NAMESPACE" $DRY_RUN
fi

# Wait for deployments
if [ -z "$DRY_RUN" ]; then
    info "Waiting for backend deployment to be ready..."
    kubectl rollout status deployment/research-assistant -n "$NAMESPACE" --timeout=120s
    
    info "Waiting for GUI deployment to be ready..."
    kubectl rollout status deployment/research-assistant-gui -n "$NAMESPACE" --timeout=120s
    
    # Show status
    info ""
    info "Deployment status:"
    kubectl get pods -n "$NAMESPACE"
    
    if [ "$ENABLE_INGRESS" = true ]; then
        info ""
        info "Ingress status:"
        kubectl get ingress -n "$NAMESPACE"
    fi
    
    info ""
    info "=========================================="
    info "Installation complete!"
    info "=========================================="
    info ""
    if [ "$ENABLE_INGRESS" = true ]; then
        info "API URL: http://agent.$CLUSTER_NAME"
        if [ -n "$GUI_HOST" ]; then
            info "GUI URL: https://$GUI_HOST"
        fi
        info ""
        info "Make sure your DNS resolves these hostnames to your ingress controller."
        info "Ensure the TLS secret '$TLS_SECRET' exists in namespace '$NAMESPACE'."
    else
        info "To access the API via port-forward:"
        info "  kubectl port-forward svc/research-assistant 8000:8000 -n $NAMESPACE"
        info "  curl http://localhost:8000/health"
        info ""
        info "To access the GUI via port-forward:"
        info "  kubectl port-forward svc/research-assistant-gui 8080:80 -n $NAMESPACE"
        info "  Open http://localhost:8080 in browser"
    fi
    info ""
    info "To view logs:"
    info "  kubectl logs -f deployment/research-assistant -n $NAMESPACE"
    info "  kubectl logs -f deployment/research-assistant-gui -n $NAMESPACE"
    info ""
    info "To uninstall:"
    info "  ./install.sh -n $NAMESPACE -u"
else
    info ""
    info "Dry run complete. No changes were made."
fi

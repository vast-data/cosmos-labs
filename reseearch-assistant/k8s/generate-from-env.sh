#!/usr/bin/env bash
#
# Generate Kubernetes ConfigMap and Secret from .env file
#
# Usage:
#   ./generate-from-env.sh [OPTIONS]
#
# Options:
#   -e, --env-file <file>     Path to .env file (default: ../.env)
#   -o, --output-dir <dir>    Output directory (default: current directory)
#   -h, --help                Show this help message
#
# Example:
#   ./generate-from-env.sh -e ../.env -o ./generated

set -e

# Default values
ENV_FILE="../.env"
OUTPUT_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Help function
show_help() {
    head -18 "$0" | tail -15 | sed 's/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            error "Unknown option: $1. Use -h for help."
            ;;
    esac
done

# Validate .env file exists
if [ ! -f "$ENV_FILE" ]; then
    error ".env file not found: $ENV_FILE"
fi

# Create output directory if needed
mkdir -p "$OUTPUT_DIR"

info "Reading .env file: $ENV_FILE"
info "Output directory: $OUTPUT_DIR"

# Define which variables are secrets (sensitive)
# Note: Any variable containing passwords, keys, or secrets should be listed here
SECRETS="RAG_USERNAME RAG_PASSWORD RAG_DEFAULT_COLLECTION VASTDB_ENDPOINT VASTDB_ACCESS_KEY VASTDB_SECRET_KEY AGENT_OPENAI_API_KEY AUTH__AZURE__CLIENTID AUTH__AZURE__CLIENTSECRET AUTH__AZURE__NEXTAUTHSECRET"

# Function to check if a variable is a secret
is_secret() {
    local var_name="$1"
    echo "$SECRETS" | grep -qw "$var_name"
}

# Function to base64 encode
b64encode() {
    echo -n "$1" | base64
}

# Temporary files for collecting vars
CONFIG_TEMP=$(mktemp)
SECRET_TEMP=$(mktemp)
trap "rm -f $CONFIG_TEMP $SECRET_TEMP" EXIT

config_count=0
secret_count=0

# Parse .env file
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    # Parse KEY=VALUE (handle values with = in them)
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        # Remove surrounding quotes if present
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        
        if is_secret "$key"; then
            echo "$key=$value" >> "$SECRET_TEMP"
            secret_count=$((secret_count + 1))
        else
            echo "$key=$value" >> "$CONFIG_TEMP"
            config_count=$((config_count + 1))
        fi
    fi
done < "$ENV_FILE"

info "Found $config_count config variables and $secret_count secret variables"

# Generate ConfigMap
CONFIGMAP_FILE="$OUTPUT_DIR/configmap.yaml"
info "Generating ConfigMap: $CONFIGMAP_FILE"

cat > "$CONFIGMAP_FILE" << 'HEADER'
# Research Assistant - ConfigMap
# Generated from .env file
# Apply with: kubectl apply -f configmap.yaml -n <namespace>

apiVersion: v1
kind: ConfigMap
metadata:
  name: research-assistant-config
  labels:
    app: research-assistant
    component: api
data:
HEADER

# Add config variables
while IFS='=' read -r key value; do
    [[ -z "$key" ]] && continue
    # Escape special characters in YAML
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    echo "  $key: \"$value\"" >> "$CONFIGMAP_FILE"
done < "$CONFIG_TEMP"

# Generate Secret
SECRET_FILE="$OUTPUT_DIR/secret.yaml"
info "Generating Secret: $SECRET_FILE"

cat > "$SECRET_FILE" << 'HEADER'
# Research Assistant - Secret
# Generated from .env file
# Apply with: kubectl apply -f secret.yaml -n <namespace>
# WARNING: This file contains sensitive data. DO NOT commit to git!

apiVersion: v1
kind: Secret
metadata:
  name: research-assistant-secrets
  labels:
    app: research-assistant
    component: api
type: Opaque
data:
HEADER

# Add secret variables (base64 encoded)
while IFS='=' read -r key value; do
    [[ -z "$key" ]] && continue
    encoded=$(b64encode "$value")
    echo "  $key: $encoded" >> "$SECRET_FILE"
done < "$SECRET_TEMP"

echo ""
info "=========================================="
info "Generation complete!"
info "=========================================="
echo ""
info "Generated files:"
info "  - ConfigMap: $CONFIGMAP_FILE"
info "  - Secret:    $SECRET_FILE"
echo ""
warn "⚠️  WARNING: secret.yaml contains sensitive data!"
warn "   DO NOT commit it to git!"
echo ""
info "To apply to Kubernetes:"
info "  kubectl apply -f $CONFIGMAP_FILE -n <namespace>"
info "  kubectl apply -f $SECRET_FILE -n <namespace>"
echo ""

# Show summary
echo -e "${BLUE}ConfigMap variables:${NC}"
while IFS='=' read -r key value; do
    [[ -z "$key" ]] && continue
    echo "  - $key"
done < "$CONFIG_TEMP"

echo ""
echo -e "${BLUE}Secret variables:${NC}"
while IFS='=' read -r key value; do
    [[ -z "$key" ]] && continue
    echo "  - $key (base64 encoded)"
done < "$SECRET_TEMP"

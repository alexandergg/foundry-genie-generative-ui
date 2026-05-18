#!/usr/bin/env bash
set -euo pipefail

LOCATION="${LOCATION:-westeurope}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-risk-exposure-genui-demo}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-risk-exposure-genui}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --tags workload=risk-exposure-generative-ui environment=demo costControl=manual-stop-compute

az deployment group what-if \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --template-file "$ROOT_DIR/infra/main.bicep" \
  --parameters "$ROOT_DIR/infra/main.demo.bicepparam" \
  --parameters location="$LOCATION"

read -r -p "Apply this deployment? Type 'yes' to continue: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Deployment cancelled."
  exit 0
fi

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --template-file "$ROOT_DIR/infra/main.bicep" \
  --parameters "$ROOT_DIR/infra/main.demo.bicepparam" \
  --parameters location="$LOCATION" \
  --query properties.outputs

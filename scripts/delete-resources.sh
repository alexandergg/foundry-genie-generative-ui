#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-risk-exposure-genui-demo}"
read -r -p "This deletes resource group '$RESOURCE_GROUP' and the Databricks workspace. Type 'delete' to continue: " CONFIRM
if [[ "$CONFIRM" != "delete" ]]; then
  echo "Delete cancelled."
  exit 0
fi
az group delete --name "$RESOURCE_GROUP" --yes --no-wait

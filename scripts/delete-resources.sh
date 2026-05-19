#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-risk-exposure-genui-foundry-demo}"
read -r -p "This deletes resource group '$RESOURCE_GROUP'. Reused Databricks workspaces in other resource groups are not deleted. Type 'delete' to continue: " CONFIRM
if [[ "$CONFIRM" != "delete" ]]; then
  echo "Delete cancelled."
  exit 0
fi
az group delete --name "$RESOURCE_GROUP" --yes --no-wait

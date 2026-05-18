#!/usr/bin/env bash
set -euo pipefail

LOCATION="${LOCATION:-westeurope}"

az account show --query '{subscription:id,name:name,tenant:tenantId}' -o table
az provider show --namespace Microsoft.Databricks --query registrationState -o tsv
az provider show --namespace Microsoft.Databricks --query "resourceTypes[?resourceType=='workspaces'].locations[]" -o tsv | grep -i "${LOCATION// /}" >/dev/null || \
  az provider show --namespace Microsoft.Databricks --query "resourceTypes[?resourceType=='workspaces'].locations[]" -o tsv | grep -i "$LOCATION" >/dev/null
az vm list-usage --location "$LOCATION" --query "[?name.value=='cores' || name.localizedValue=='Total Regional vCPUs'].{name:name.localizedValue,current:currentValue,limit:limit}" -o table
az vm list-usage --location "$LOCATION" --query "[?contains(name.localizedValue, 'EDSv4') || contains(name.localizedValue, 'E8') || contains(name.localizedValue, 'E')].{name:name.localizedValue,current:currentValue,limit:limit}" -o table | head -40

echo "Preflight complete. Review quota before creating Pro SQL warehouses. Serverless SQL reduces Azure VM quota dependency."

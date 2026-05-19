#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

load_local_env
require_env AZURE_CONTAINER_REGISTRY_LOGIN_SERVER

image_repository="${FOUNDRY_HOSTED_AGENT_IMAGE_REPOSITORY:-risk-exposure-ag-ui-hosted}"
image_tag="${FOUNDRY_HOSTED_AGENT_IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
registry_name="${AZURE_CONTAINER_REGISTRY_NAME:-${AZURE_CONTAINER_REGISTRY_LOGIN_SERVER%%.*}}"
image_ref="${AZURE_CONTAINER_REGISTRY_LOGIN_SERVER}/${image_repository}:${image_tag}"

if [[ "$image_tag" == "latest" ]]; then
  echo "Refusing to publish the mutable 'latest' tag. Set FOUNDRY_HOSTED_AGENT_IMAGE_TAG to a timestamp or version." >&2
  exit 2
fi

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI (az) is required." >&2
  exit 2
fi

echo "Building Foundry Hosted Agent image for linux/amd64 with Azure Container Registry..."
echo "Registry: $registry_name"
echo "Image:    $image_ref"

az acr build \
  --registry "$registry_name" \
  --image "${image_repository}:${image_tag}" \
  --platform linux/amd64 \
  --source-acr-auth-id "[caller]" \
  --file "$DEMO_ROOT/apps/agent/Dockerfile" \
  "$DEMO_ROOT/apps/agent"

cat <<EOF

Built hosted-agent image:
$image_ref

Use this immutable image reference when creating or updating the Foundry Hosted Agent from apps/agent/agent.yaml.
EOF

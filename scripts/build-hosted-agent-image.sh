#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

# Usage: build-hosted-agent-image.sh [agent-dir]
# agent-dir is relative to the repo root and defaults to the controlled (Genie)
# agent. Each band's agent ships its own Dockerfile + agent.yaml:
#   apps/controlled/agent | apps/declarative/agent | apps/open-ended/agent
AGENT_SUBDIR="${1:-apps/controlled/agent}"
AGENT_DIR="$DEMO_ROOT/$AGENT_SUBDIR"

if [[ ! -f "$AGENT_DIR/Dockerfile" || ! -f "$AGENT_DIR/agent.yaml" ]]; then
  echo "No Dockerfile/agent.yaml under $AGENT_SUBDIR — is this a hosted-ready agent directory?" >&2
  exit 2
fi

# Capture an explicit caller override BEFORE sourcing .risk.env.local, which may
# pin FOUNDRY_HOSTED_AGENT_IMAGE_REPOSITORY for the controlled agent.
caller_repository="${FOUNDRY_HOSTED_AGENT_IMAGE_REPOSITORY:-}"

load_local_env
require_env AZURE_CONTAINER_REGISTRY_LOGIN_SERVER

# Repository precedence: explicit caller override > agent.yaml name.
default_repository="$(sed -n 's/^name:[[:space:]]*//p' "$AGENT_DIR/agent.yaml" | head -1)"
image_repository="${caller_repository:-$default_repository}"
image_tag="${FOUNDRY_HOSTED_AGENT_IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
registry_name="${AZURE_CONTAINER_REGISTRY_NAME:-${AZURE_CONTAINER_REGISTRY_LOGIN_SERVER%%.*}}"
image_ref="${AZURE_CONTAINER_REGISTRY_LOGIN_SERVER}/${image_repository}:${image_tag}"

if [[ -z "$image_repository" ]]; then
  echo "Could not derive an image repository (agent.yaml has no name and FOUNDRY_HOSTED_AGENT_IMAGE_REPOSITORY is unset)." >&2
  exit 2
fi

if [[ "$image_tag" == "latest" ]]; then
  echo "Refusing to publish the mutable 'latest' tag. Set FOUNDRY_HOSTED_AGENT_IMAGE_TAG to a timestamp or version." >&2
  exit 2
fi

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI (az) is required." >&2
  exit 2
fi

echo "Building Foundry Hosted Agent image for linux/amd64 with Azure Container Registry..."
echo "Agent:    $AGENT_SUBDIR"
echo "Registry: $registry_name"
echo "Image:    $image_ref"

az acr build \
  --registry "$registry_name" \
  --image "${image_repository}:${image_tag}" \
  --platform linux/amd64 \
  --source-acr-auth-id "[caller]" \
  --file "$AGENT_DIR/Dockerfile" \
  "$AGENT_DIR"

cat <<EOF

Built hosted-agent image:
$image_ref

Use this immutable image reference when creating or updating the Foundry Hosted Agent from $AGENT_SUBDIR/agent.yaml.
EOF

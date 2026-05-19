---
applyTo: "scripts/**/*.sh,docs/**/*.md,README.md"
---

# Scripts and docs instructions

- Scripts are descriptive, not numbered; document ordering in prose instead of filename prefixes.
- Keep shell scripts safe with `set -euo pipefail`, quoted variables, and shared helpers from `scripts/lib/common.sh`.
- Live Azure/Databricks actions must require explicit user intent and clear cost-control guidance.
- When script names or environment variables change, update README and every affected doc.

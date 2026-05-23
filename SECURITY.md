# Security Policy

This repository is a demo of Generative UI on Microsoft Foundry + Databricks Genie. It is not a production product, but if you find a security issue we still want to know.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Use GitHub's [Private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) on this repo:

1. Go to the **Security** tab.
2. Click **Report a vulnerability**.
3. Describe the issue, the affected commit/branch, and a reproduction if you have one.

We aim to acknowledge reports within **5 business days** and to publish a fix or mitigation within **30 days** when the issue is confirmed and in scope.

## Scope

In scope:

- Code under `apps/`, `infra/`, `scripts/`, and `databricks/` in this repository.
- Documentation that could cause users to deploy insecure configurations (e.g. instructing them to commit secrets).
- The default Bicep templates and RBAC role assignments.

Out of scope (please report upstream):

- Microsoft Foundry, Azure AI Projects SDK, Azure Identity, or other Azure platform bugs → [Microsoft Security Response Center (MSRC)](https://msrc.microsoft.com/).
- Databricks Genie, Databricks SQL, or Databricks SDKs → [Databricks Security](https://www.databricks.com/legal/security).
- CopilotKit, AG-UI, LangGraph, or other third-party libraries → their respective maintainers.

## Hardening notes for users of this demo

- This demo is designed to be deployed into a sandbox Azure subscription. It is **not** hardened for production.
- The provided Bicep grants the demo identity broad roles (`Cognitive Services User`, etc.). Audit and tighten before any production reuse.
- Keep `.risk.env.local`, `apps/web/.env.local`, `.foundry/agent-metadata.yaml`, and any other local environment files out of version control. They are gitignored by default — do not unignore them.
- The hosted agent assumes Foundry-managed identity for ACR and downstream tools. If you fork into a different topology, re-validate the trust boundary.

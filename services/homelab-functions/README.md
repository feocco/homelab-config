# homelab-functions

This service deploys the public `ghcr.io/feocco/homelab-functions:latest`
image on the Mac mini.

Runtime-only files stay outside the public app repo:

- `.env` contains Home Assistant connection details and the local function API token.
- `config/service-catalog.json` and `config/smoke-signal-targets.json` are
  generated during deploy from `homelab-config` service metadata.

Changes under this directory trigger the homelab deploy workflow for this service
when the service is enabled in the target host services file.

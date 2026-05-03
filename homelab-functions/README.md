# homelab-functions

This service deploys the public `ghcr.io/feocco/homelab-functions:latest`
image on the NAS.

Runtime-only files stay outside the public app repo:

- `.env` contains Home Assistant connection details and the local function API token.
- `data/` is reserved for future function state.

Changes under this directory trigger the homelab deploy workflow for this service
when the service is enabled in `services.yaml`.

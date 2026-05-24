# hass-janitor

This service deploys the private `ghcr.io/feocco/hass-janitor:latest` image on
the NAS.

Runtime-only files stay outside the app repo:

- `.env` contains Home Assistant credentials and the local service API token.
- `hass_janitor_logs` is a named Docker volume containing the Markdown audit log.

Changes under this directory trigger the homelab deploy workflow for this
service when it is enabled in `services.yaml`.

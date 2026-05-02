# Plant Monitor

This service deploys the public `ghcr.io/feocco/plant-monitor:latest` image on the NAS.

Runtime-only files stay outside the public app repo:

- `.env` contains Home Assistant connection details.
- `plants.yaml` contains the reviewed local plant/entity mapping.
- `data/` contains notification and monitor state.

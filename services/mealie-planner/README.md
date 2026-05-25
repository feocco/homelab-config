# Mealie Planner

Internal-only dinner planner service for Mealie.

- App repo: `/Users/feocco/code/mealie-planner`
- Image: `ghcr.io/feocco/mealie-planner:latest`
- Local health: `http://127.0.0.1:8096/health`
- Public route: none in V1
- Persistent data: `./data/planner.sqlite3`

The service reads Mealie recipes from `MEALIE_BASE_URL`, asks OpenAI for a structured draft, sends Joe an actionable phone notification through `homelab-functions`, and writes Mealie dinner planner entries only after Accept.

Required secrets are tracked in `service-secrets.yaml`: `OPENAI_API_KEY`, `MEALIE_API_TOKEN`, `HA_URL`, `HA_LONG_LIVED_TOKEN`, and `HOMELAB_FUNCTIONS_TOKEN`.


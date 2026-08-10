# Instacart History Service

Internal Instacart order-history and ingredient recommendation service.

- App repo: `/Users/feocco/code/instacart-history-service`
- Image: `ghcr.io/feocco/instacart-history-service:latest`
- Local health on Mac mini: `http://127.0.0.1:8100/health`
- Tailnet route: `http://maclabs-mac-mini.taildf3445.ts.net:8100/`
- Persistent data: `./data/instacart_history.sqlite3`

The service stores imported Instacart order-history exports, maps Mealie
ingredients to historically purchased Instacart products, and can call
`mealie-planner` through `MEALIE_PLANNER_BASE_URL`.

Required secrets are tracked in `service-secrets.yaml`: `OPENAI_API_KEY`.

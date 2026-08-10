# Service API Conventions

Backend services that appear on Homepage should provide a browser-friendly
entrypoint without turning health checks into user documentation.

## Target Convention

- `GET /health` stays machine-oriented JSON for Homepage status dots,
  Prometheus blackbox checks, and rollout validation.
- `GET /docs` is the human service page. It should explain what the service
  does, how health is determined, which API endpoints external services may
  call, and which endpoints require auth.
- `GET /openapi.json` returns an OpenAPI 3.1 JSON document for externally
  callable endpoints.
- Protected endpoints should document the bearer token or credential they
  require, but the browser docs should not store tokens or execute protected
  calls.
- Services do not need to migrate frameworks just to adopt this convention.
  The current framework is part of the rollout metadata so divergence remains
  visible.

## Manifest Fields

Services that adopt the convention declare these flat fields in
`services/<service>/ops.yaml`:

```yaml
docs_path: /docs
openapi_path: /openapi.json
api_framework: aiohttp
```

Valid `api_framework` values are:

- `aiohttp`
- `fastapi`
- `node-http-server`
- `python-http-server`
- `other`
- `none`

When `docs_path` is present, Homepage links the service card to the service
docs URL. The generated `siteMonitor` still checks `health_path`.

## Current Divergence

Initial local inspection found these API framework differences:

| Service | Current API framework | Notes |
| --- | --- | --- |
| `hello-nas` | Python `http.server` | Pilot service. |
| `homelab-functions` | `aiohttp` | Pilot service with protected APIs. |
| `laundry-monitor` | Python `http.server` | Health/status service. |
| `instacart-history-service` | `FastAPI` | Purchase history and recommendation API. |
| `hass-janitor` | Python `http.server` | Protected mutation API. |
| `bedtime` | `aiohttp` | Health endpoint only. |
| `plant-monitor` | `aiohttp` | Health/status-style backend. |
| `dog-bowl-monitor` | `aiohttp` | Health/status-style backend. |

Sampled services did not already expose OpenAPI or Swagger endpoints before
the first pilot migration.

## Migration Checklist

For the agent-oriented task flow and staged pass/fail command, see
[Service Docs Migration](service-docs-migration.md).

1. Inspect the app repo and record the actual framework.
2. Add `/docs` and `/openapi.json` in the app repo without changing unrelated
   behavior.
3. Add focused app tests for docs HTML, OpenAPI JSON, and unchanged health/API
   behavior.
4. Update `services/<service>/ops.yaml` with `docs_path`, `openapi_path`, and
   `api_framework`.
5. Run config validation:

   ```bash
   LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check config --mode strict
   ```

6. After the app image is published and deployed, run live validation:

   ```bash
   LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check live --mode strict
   ```

7. Report any framework, auth, route, or endpoint-shape divergence before
   migrating the next service.

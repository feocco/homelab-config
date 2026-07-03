# Service Docs Migration

Use this when migrating one backend service to the homelab service-docs
pattern. The goal is to make the service page visible in Homelab Docs without
copying app-owned documentation into `homelab-config`.

## Done Function

The canonical validator is:

```bash
./scripts/check-service-docs-migration --service <service> --host <host> --stage <stage>
```

It returns exit code `0` only when the selected stage passes. Use
`--format json` when another tool, agent, badge, or generated quality page
needs machine-readable evidence.

Stages are:

- `app`: proves the app repo can serve or test its docs implementation.
- `manifest`: proves `homelab-config` declares the docs metadata and passes
  strict config rollout validation.
- `live`: proves the deployed service passes strict live rollout validation.
- `docs-site`: proves the generated central wrapper page exists and reports
  `Live docs available`.
- `all`: runs the stages in order and stops at the first failure.

The `app` stage requires an app repo plus at least one executable proof:

```bash
./scripts/check-service-docs-migration \
  --service <service> \
  --host <host> \
  --stage app \
  --app-repo /path/to/app-repo \
  --app-test-command 'python3 -m unittest'
```

If the app is already running locally, add `--local-base-url` to check
`/docs` and `/openapi.json` directly:

```bash
./scripts/check-service-docs-migration \
  --service <service> \
  --host <host> \
  --stage app \
  --app-repo /path/to/app-repo \
  --local-base-url http://127.0.0.1:8080
```

## Migration Task

For one service, do the work in this order:

1. Inspect the app repo and record the actual API framework.
2. Add `GET /docs` and `GET /openapi.json` in the app repo.
3. Add app-owned tests for docs HTML, OpenAPI JSON, and unchanged health/API
   behavior.
4. Run the `app` stage until it passes.
5. Publish the app image through the app repo workflow.
6. Update `services/<service>/ops.yaml` with `docs_path`, `openapi_path`, and
   `api_framework`.
7. Run the `manifest` stage until it passes.
8. Redeploy the service through the normal homelab deploy workflow.
9. Run the `live` stage until it passes.
10. Run the `docs-site` stage and confirm the central wrapper reports
    `Live docs available`.

Do not migrate every historical service in the same change. Treat the old
services as one-time backlog items and migrate them one at a time.

## Source Model

Application repos own their service-specific documentation and API behavior.
`homelab-config` owns deployment metadata, generated navigation, and validation
against the live service. Generated Homelab Docs pages are wrappers over those
sources, not a second documentation store.

The validator deliberately reuses existing checks:

- Manifest and live proof delegate to `scripts/validate-service-rollout`.
- Service page status comes from `scripts/generate-docs-service-index`.
- Service metadata comes from the existing service catalog inputs.

This keeps the current migration small while leaving a JSON output path for a
future service quality page or badge-style report.

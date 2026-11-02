# AGENTS.md

## Repository purpose

- This public repository owns private homelab runtime intent. App repositories
  own source code, Dockerfiles, tests, and GHCR publishing.
- Use Docker Compose and `hosts/<host>/services.yaml`. Do not add Kubernetes.
- `services/<service>/ops.yaml` is the source for catalog, route, dashboard,
  monitoring, and rollout metadata. Keep it flat. The parser rejects nested
  mappings.
- Default app and compute services to `macmini`. Keep storage-adjacent
  infrastructure, Portainer, Pi-hole, and the NAS runner on `nasfeo`.

## Inspect and run the repository

- This repository has no long-running development server and no language
  dependency manifest.
- Run `./scripts/list-homelab-services` before service discovery, deploy
  planning, or source-of-truth work.
- Run `./scripts/generate-service-catalog --format json` to inspect the
  generated catalog.
- Read `docs/operator-runbook.md` for owner commands and
  `docs/deployment-source-of-truth.md` for the deploy model.
- The workflow-policy check requires PyYAML from
  `scripts/requirements-workflow-policy.txt`. The full test suite requires the
  `docker` and `tailscale` CLIs on `PATH`. The Tailscale daemon is not required.

## Test changes

- Run the full suite with `LC_ALL=C ./scripts/test-deploy-tooling`.
- Run workflow policy checks with
  `./scripts/check-workflow-policy --repository feocco/homelab-config
  --deploy-workflow .github/workflows/deploy.yml` and
  `./scripts/tests/check-workflow-policy`.
- Run route auth policy with `./scripts/tests/check-route-auth`.
- For Caddy changes, render to a temporary path with
  `./scripts/generate-caddy-config --output <tmp>/Caddyfile`, then run
  `./scripts/tests/check-caddy-routes`.
- For secret schema or `.env.config` changes, also run
  `LC_ALL=C ./scripts/generate-service-secret-workflow-env` and
  `LC_ALL=C ./scripts/check-service-secrets`.
- For one service, run
  `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host
  <host> --check config --mode strict`.

## Conventions

- Never build custom auth; if auth is needed, reuse the homelab IdP (Authentik
  via Caddy `forward_auth`); bots use bearer tokens.
- Declare route auth in `route_auth`. Open tailnet routes and token APIs require
  explicit allowlist entries in `scripts/tests/check-route-auth`.
- Default user-facing services to `*.home.feocco.com` with
  `route_https: true` and `route_dns: unifi`. Put extra names in
  `route_extra_hostnames`. Follow `services/caddy/README.md` for documented
  exceptions.
- Change flat `route_*` fields instead of generated Caddy output. Change flat
  `dashboard_*` fields instead of generated Homepage output.
- Do not hand-edit or commit `services/caddy/Caddyfile` or files under
  `services/homepage/config/`.
- Declare generated-service deploy triggers in that service's `redeploy_on`
  list. Do not hardcode trigger paths in `scripts/homelab-deploy`.
- Put non-secret runtime values in tracked `.env.config` files. Put secret names
  in `service-secrets.yaml`. Put private identity values in
  `$HOME/homelab-private-config/<host>/<service>.env`.
- Never commit real `.env` files, runtime `data/`, tokens, personal addresses,
  account IDs, or private host values.

## Deployment safety

- Inspect `git status --short --branch` before deployment work.
- Do not deploy unless the user explicitly requests it. Prefer `--dry-run` for
  local inspection.
- Do not bypass deploy guards with `--allow-dirty`, `--canary`,
  `--allow-foreign-host`, or `--skip-config-validate` during verification.
- Commit and push before a durable deploy. `main` is the source of truth.
- Setting `enabled: false` does not stop an existing container.
- State what was committed, pushed, and deployed in every deploy handoff.

## pstack

- Use exactly one implementer and one reviewer.
- Do not use arena, swarm, or multi-judge fan-outs unless Joe explicitly asks.

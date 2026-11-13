# AGENTS.md

## Repo-specific decisions

- This repo owns private Docker runtime config. App repos own source,
  Dockerfiles, tests, and GHCR publishing. Use Docker Compose and
  `hosts/<host>/services.yaml`.
- Default app and compute services to `macmini`. Keep NAS infrastructure,
  storage-adjacent services, Portainer, Pi-hole, and the NAS runner on
  `nasfeo`. Run one `homelab-log-watcher` per Docker host. The central
  `homelab-sre-agent` runs on `macmini`.
- `services/<service>/ops.yaml` is flat catalog, route, dashboard, monitoring,
  and rollout metadata. Nested mappings are rejected.
- When a service needs auth, reuse Authentik: `route_auth:
  authentik_forward_auth` or `route_auth: authentik_oidc`. Nothing-sensitive
  tailnet routes use `tailnet_open`. Shared-function calls keep bearer tokens
  with `api_token`. Both allowlists live in `scripts/tests/check-route-auth`,
  which records the choice and does not force auth onto a service.
- User-facing routes use `*.home.feocco.com`, `route_https: true`, and
  `route_dns: unifi`. Extra names go in `route_extra_hostnames:`. See
  `services/caddy/README.md`. A public-internet exception keeps the Mealie
  split horizon: `route_public_dns: cloudflare-tunnel`, UniFi for LAN, and
  `route_dns_alias_target` when a public AAAA would leak locally.
- Friend-facing HTTPS uses `route_tailscale_service: svc:<name>` and a matching
  `hosts/<host>/tailscale-serve.yaml` `named_services` entry with its TailVIP.
  Raw TCP 443 stays on Caddy.
- Generated runtime config comes from flat `route_*` and `dashboard_*` fields.
  Homepage manual links live in `services/homepage/manual-links.yaml`. A
  generated service lists extra deploy triggers in its own `redeploy_on:`.
- Secrets a service can start without go under `optional_env:` in
  `service-secrets.yaml`. The generator wires them into deploy.yml and renders
  `.env` only when the Actions secret exists and is non-empty. Use `env:` only
  when the service cannot start without the value. Multi-line PEM values are
  one escaped double-quoted line that Compose expands.
- Identity fingerprints (personal emails, GitHub App IDs, diagnostic bucket
  names, HA notify entity IDs) belong in
  `$HOME/homelab-private-config/<host>/<service>.env`.
  `scripts/render-service-env` prefers that overlay over tracked `.env.config`.
- `scripts/tests/check-repo-prohibitions` rejects Kubernetes manifests,
  committed generated files and secrets, friend-path bypasses, hardcoded
  redeploy triggers, and a hand-edited secret block. Route auth, route
  convention, forward-auth isolation, and secret contracts have their own
  checks. The failure line names the fix.

## Workflows

- Before service discovery, deploy planning, or source-of-truth questions, run
  `./scripts/list-homelab-services`. Inspect the catalog with
  `./scripts/generate-service-catalog --format json`.
- Render routes with `./scripts/generate-caddy-config`,
  `./scripts/sync-unifi-dns`, and `./scripts/sync-cloudflare-dns`.
  Credentialed DNS changes go through
  `./scripts/dispatch-route-dns --mode check|apply --watch`.
- Identity architecture is `docs/authentication.md` and
  `docs/adr/0001-unified-homelab-identity.md`. Authentik operations are
  `services/authentik/README.md`. Use the
  `homelab-authentik-app-integration` skill for OIDC. Blueprint what you can.
  Settings that cannot be blueprint-managed go through
  `scripts/configure-authentik-settings`.
- Before declaring a new required secret, set it, then run
  `scripts/check-declared-secrets-set --names-file <(gh secret list -R feocco/homelab-config --json name -q '.[].name') --strict`
  (names only). A missing secret in a `--all` render skips that service
  (`.render-env-skipped`) and homelab-deploy refuses it.
- New Mac mini user-facing HTTP services get a `home.feocco.com` LAN HTTPS
  route unless the service is a worker, disabled, not user-facing, or has
  incompatible base URLs. Use `./scripts/list-https-route-candidates`, add
  `route_*` fields, sync DNS, and validate with
  `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check config`.
  Use `--check live` after deployment when the manifest declares live proof.
- Dashboard-visible Mac mini Runtime Services expose `GET /health` and declare
  `http_port`, `port_env`, `health_path`, `live_base_url`, `tailnet: true`,
  and `monitoring: true`. A health endpoint without a LAN route sets
  `route_exempt_reason`. Docs migration adds `docs_path`, `openapi_path`, and
  `api_framework`, and reports framework or API divergence first.
- App-only changes: publish the image, then run
  `./scripts/redeploy-image --host <host> <service>` from this repo. Edit this
  repo when the runtime shape changes (env, secrets, ports, volumes, host,
  image reference, command, monitoring, dashboard, links, or SRE metadata).
  Deploys pull `ghcr.io/feocco/*` Compose services. Third-party images are
  manual or image-reference updates. Third-party or config-only services are
  usually owned here.
- Do not deploy unless the user explicitly asks. Inspect
  `git status --short --branch` before deployment work. Validate with
  `LC_ALL=C ./scripts/test-deploy-tooling`. Every enabled service needs
  `services/<service>/ops.yaml`.
- Real deploys run strict config validation before `compose up`.
  `--skip-config-validate`, `--allow-dirty`, `--canary`, and
  `--allow-foreign-host` each skip one guard. Commit and push before a durable
  deploy. A branch deploy is a temporary canary on the production host: pass
  `--canary`, then merge and redeploy from `main`. Prefer
  `./scripts/homelab-deploy --host macmini <service> --dry-run`.
- When secrets or `.env.config` change, run
  `LC_ALL=C ./scripts/generate-service-secret-workflow-env`,
  `LC_ALL=C ./scripts/check-service-secrets`, and
  `LC_ALL=C ./scripts/test-deploy-tooling`.
- Deploy handoffs state what was committed, pushed, and deployed, and any
  temporary runtime state left behind.
- Mac services publish container ports on `127.0.0.1` and expose selected
  ports through `hosts/macmini/tailscale-serve.yaml`. Mac containers call
  other Mac services through `host.docker.internal`. NAS-to-Mac calls use the
  Mac mini Tailnet name. `enabled: false` does not stop a running container.
  Provenance under `.homelab-deploy-state/` is evidence only; `main` is the
  source of truth. See `docs/deployment-source-of-truth.md`.

## Cursor Cloud

- There is no long-running app and no language dependency manifest. Owner
  commands are in `docs/operator-runbook.md`.
- Secret-block sorting is C collation. Run the generators with `LC_ALL=C`
  so a bare `sort` under another locale does not mark the block stale. The
  `tailscale` CLI must be on `PATH`; the daemon is not required.
- Offline deploy exercises live in `scripts/tests/check-deploy-guards` and
  `scripts/test-deploy-tooling`. They use fake `docker` shims and a temp
  `--deploy-base-dir`.

## pstack

- Use exactly one implementer and one reviewer. Do not use arena, swarm, or
  multi-judge fan-outs unless Joe explicitly asks.

# AGENTS.md

## Repo-Specific Decisions

- This repo owns private Docker runtime config only. App repos own source,
  Dockerfiles, tests, and GHCR publishing.
- Use Docker Compose and host manifests, not Kubernetes.
- Default app/compute services to `macmini`; keep NAS infrastructure,
  storage-adjacent services, Portainer, Pi-hole, and the NAS runner on
  `nasfeo`.
- Run one `homelab-log-watcher` per Docker host. The central
  `homelab-sre-agent` runs on `macmini`.

## Agent Workflows

- Before service discovery, deploy planning, or source-of-truth questions, run
  `./scripts/list-homelab-services` to compare host manifests, Compose images,
  monitoring coverage, and SRE metadata.
- Service catalog output is generated from `services/*/ops.yaml`, host
  manifests, Compose, monitoring, and SRE metadata. Do not hand-maintain a
  parallel catalog file. Use `./scripts/generate-service-catalog --format json`
  to inspect the catalog. Homepage runtime config is generated during deploy;
  do not commit generated files under `services/homepage/config/`.
- Services whose runtime config is generated (Caddy, Homepage,
  homelab-functions, homelab-docs) declare their extra deploy triggers as a
  flat `redeploy_on:` regex list in their own `ops.yaml`; do not hardcode new
  trigger paths in `scripts/homelab-deploy`.
- Caddy routes are generated from flat `route_*` fields in service `ops.yaml`
  files. Use `./scripts/generate-caddy-config`, `./scripts/sync-unifi-dns`,
  and `./scripts/sync-cloudflare-dns`; do not hand-edit or commit
  `services/caddy/Caddyfile`.
- Use `./scripts/dispatch-route-dns --mode check|apply --watch` for credentialed
  UniFi and Cloudflare DNS operations. Do not ask the user to enter individual
  route records in either provider when the workflow is available.
- Friend-facing HTTPS routes use `route_tailscale_service: svc:<name>` and a
  matching `hosts/<host>/tailscale-serve.yaml` `named_services` entry with its
  actual TailVIP. Keep raw TCP 443 pointed at Caddy; never reintroduce a direct
  app-port friend path that bypasses TLS SNI or application authentication.
- Homelab identity architecture lives in `docs/authentication.md` and
  `docs/adr/0001-unified-homelab-identity.md`; Authentik operations live in
  `services/authentik/README.md`. Use the repo-local
  `homelab-authentik-app-integration` skill when adding OIDC to an application.
- Authentik blueprints are durable provider configuration. If a setting cannot
  be blueprint-managed, add a checked-in apply/check script like
  `scripts/configure-authentik-settings`; do not leave unexplained UI-only
  identity changes.
- When a service should be reachable from the public internet without
  Tailscale, use the Mealie-style split-horizon pattern only for that service:
  keep the Cloudflare Tunnel/Access public DNS path intact with
  `route_public_dns: cloudflare-tunnel`, use UniFi DNS for LAN access, and use
  `route_dns_alias_target` if public Cloudflare AAAA records would otherwise
  leak through locally.
- For new Mac mini user-facing HTTP services, default to a LAN HTTPS route
  under `home.feocco.com` unless the service is a worker, disabled, not
  user-facing, or has incompatible base-URL assumptions. Use
  `./scripts/list-https-route-candidates`, add only `route_*` fields, sync
  UniFi and Cloudflare DNS, deploy Caddy plus the service as a canary on the
  production host, then run strict config and live validation.
- Homepage display metadata belongs in optional flat `dashboard_*` fields in
  each service `ops.yaml`. External/manual links belong in
  `services/homepage/manual-links.yaml`.
- Dashboard-visible Mac mini `Runtime Services` should follow the backend app
  service card convention: expose `GET /health`, declare `http_port`,
  `port_env`, `health_path`, `live_base_url`, `tailnet: true`, and
  `monitoring: true`, and let Homepage add the generated status dot. If a
  service has a backend health endpoint but should not get a LAN HTTPS route,
  declare `route_exempt_reason` in `ops.yaml`.
- When migrating a backend service card to human docs, add `docs_path`,
  `openapi_path`, and `api_framework` in `ops.yaml`; report framework/API
  divergence before changing the service.
- Classify deployment work before editing runtime config:
  - App code changed only: commit/push the app repo, publish the image, then
    run `./scripts/redeploy-image --host <host> <service>` from this repo. Do
    not edit this repo unless the runtime shape changed. Deploys explicitly
    pull only `ghcr.io/feocco/*` Compose services; third-party images are
    manual or image-reference updates.
  - Runtime config changed: make the matching homelab-config change for env,
    secrets, ports, volumes, host placement, image references, commands,
    monitoring, dashboards, links, or SRE metadata.
  - Third-party or config-only service changed: this repo usually owns the
    durable change.
- Inspect `git status --short --branch` before deployment work.
- Validate deployment changes with `LC_ALL=C ./scripts/test-deploy-tooling`.
- Every enabled service must have `services/<service>/ops.yaml`;
  `test-deploy-tooling` fails otherwise. Validate the declared rollout outcome
  with
  `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check config`.
  Use `--check live` after deployment for manifests that declare live proof.
- Real (non-dry-run) deploys run strict config validation automatically before
  `compose up`; `--skip-config-validate` is an emergency-only escape. Each
  guard flag skips exactly one guard: `--allow-dirty` (dirty worktree),
  `--canary` (non-main branch), `--allow-foreign-host` (not the macmini
  production host).
- When secrets or `.env.config` files change, run:
  `LC_ALL=C ./scripts/generate-service-secret-workflow-env`,
  `LC_ALL=C ./scripts/check-service-secrets`, and
  `LC_ALL=C ./scripts/test-deploy-tooling`.
- Identity fingerprints that must not be public (personal emails, GitHub App
  IDs, diagnostic bucket names, HA notify entity IDs) belong in
  `$HOME/homelab-private-config/<host>/<service>.env` on each runner host.
  `scripts/render-service-env` prefers that private overlay over tracked
  `.env.config`. Do not add those values as new GitHub Actions secrets unless
  necessary; this repo is near the Actions secret count limit.
- Prefer host-aware commands, for example
  `./scripts/homelab-deploy --host macmini <service> --dry-run`.
- Do not treat a dirty or unpushed deploy as durable production state.
  Commit and push before a durable deploy.
- Treat branch deploys as temporary canaries on the target production host, not
  arbitrary local Docker contexts. Use `--canary`, then merge and redeploy from
  `main` when the canary should become production truth.
- If you must leave temporary runtime state behind, say so explicitly in the
  final answer.
- Final answers for deploy work must say what was committed, pushed, and
  deployed.

## Runtime And Deployment Notes

- Mac services bind Docker ports to `127.0.0.1` and expose selected ports
  through `hosts/macmini/tailscale-serve.yaml`.
- Mac containers should call other Mac-hosted services through
  `host.docker.internal`.
- NAS-to-Mac calls should use the Mac mini Tailnet name.
- Setting `enabled: false` in a host manifest does not stop an already-running
  container. Stop old containers manually after the new host is verified.
- `scripts/homelab-deploy` writes local deploy provenance to
  `.homelab-deploy-state/<host>/<service>.json` in the runtime tree. This is
  evidence only; `main` remains the source of truth.
- See `docs/deployment-source-of-truth.md` for the branch, dirty deploy, and
  emergency runtime edit model.

## Footguns

- Do not hand-edit generated secret blocks in `.github/workflows/deploy.yml`.
  Update `service-secrets.yaml` or host manifests, then run the generator.
- Never commit real `.env` files or runtime `data/` contents.

## Cursor Cloud specific instructions

- This repo is bash/python CLI tooling + deploy config; there is no
  long-running app to start and no language dependency manifests. Standard
  commands live in `docs/operator-runbook.md` (owner deploy) and the
  `## Agent Workflows` section above (validate/secrets).
- Secret-sort scripts export `LC_ALL=C` themselves via `lib-service-secrets`.
  The generated secret block in `.github/workflows/deploy.yml` is sorted under
  C collation (underscore sorts after letters). Under `en_US.UTF-8`, bare
  `sort` would reorder keys and make `./scripts/check-service-secrets` /
  `./scripts/generate-service-secret-workflow-env` falsely report the block as
  stale. Prefixing with `LC_ALL=C` is still fine and harmless.
- Prefer `LC_ALL=C ./scripts/test-deploy-tooling` in docs and agent workflows
  for consistency with older guidance.
- The `tailscale` CLI binary must be on `PATH` for the test suite to pass:
  `./scripts/test-deploy-tooling` runs `apply-tailscale-serve --dry-run`, which
  checks `command -v tailscale` before its dry-run branch. The startup update
  script installs the static `tailscale` CLI; the daemon is not needed.
- To exercise a real deploy offline (no Docker daemon, no GHCR access), put fake
  `docker`/`docker-compose` shims on `PATH` and deploy to a temp
  `--deploy-base-dir` with `--allow-dirty --canary` (needed off `main`). This is
  the same offline pattern `./scripts/test-deploy-tooling` uses; it renders the
  runtime `.env`, runs `compose up`, and writes the provenance JSON.

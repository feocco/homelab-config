# Operator Runbook (owner)

> Owner-operated notes for this homelab. Not a public install guide. Strangers
> cannot run this tree without host access, Actions secrets, and private
> overlays that are intentionally absent from git.

Former front-door deploy documentation lives here so `README.md` can stay a
showcase.

## Layout

```text
hosts/
  nasfeo/services.yaml
  macmini/services.yaml
services/
  <service>/
    docker-compose.yml
    .env.example
    .env.config
    ops.yaml
service-secrets.yaml
scripts/
  homelab-deploy
  render-service-env
docs/
```

## Standard Deploy Shape

1. Application repo builds an image.
2. Image is pushed to a registry such as GHCR.
3. `hosts/<host>/services.yaml` declares which host runs each service.
4. The target host pulls the image.
5. The target host runs the service with Docker Compose.

## Host Placement

- `nasfeo`: Portainer, NAS GitHub runner, Pi-hole (outside this repo), NAS
  `homelab-log-watcher`, Smoke Signal.
- `macmini`: Homepage, Caddy, Authentik, apps, monitoring, SRE agent, Mac
  `homelab-log-watcher`.
- Disabled for later: `netalertx`.

## Commands

```bash
./scripts/list-homelab-services
./scripts/list-homelab-services --host macmini
./scripts/generate-service-catalog --format json
./scripts/homelab-deploy --host macmini --list
./scripts/homelab-deploy --host macmini <service> --dry-run
./scripts/redeploy-image --host macmini <service>
```

Inventory and domain map: `docs/source-of-truth.md`.  
API card conventions: `docs/service-api-conventions.md`.  
HTTPS route rollout: `docs/https-route-rollout-goal.md`.

## Generated Config

Homepage and Caddy are generated at deploy time from `ops.yaml`. Do not commit
`services/homepage/config/` or `services/caddy/Caddyfile`.

```bash
./scripts/generate-homepage-config --output "$(mktemp -d)"
./scripts/generate-caddy-config
./scripts/sync-unifi-dns --host macmini --dry-run
./scripts/sync-cloudflare-dns --host macmini --dry-run
./scripts/dispatch-route-dns --mode check --watch
LC_ALL=C ./scripts/validate-service-rollout --service <service> --host macmini --check config --mode strict
```

## Runtime Environment

Tracked non-secret values live in `services/<service>/.env.config`. Host
overrides live in `hosts/<host>/<service>.env.config`. Sensitive tokens are
named in `service-secrets.yaml` and stored as GitHub Actions secrets.

Identity fingerprints that should not be public (personal emails, GitHub App
IDs, S3 bucket names, HA notify entity IDs) can live in a **private overlay**
outside git:

```text
$HOME/homelab-private-config/<host>/<service>.env
```

`scripts/render-service-env` merges, first hit wins:

1. private overlay
2. host `.env.config`
3. shared `.env.config`
4. then appends Actions secrets

Seed the overlays once (harvests real values from the live `.env` files, no
typing):

```bash
./scripts/install-private-config --host macmini
./scripts/install-private-config --print-template   # manual fallback
```

Inspect Tailscale identity/trust from the CLI instead of the admin console:

```bash
./scripts/tailscale-acl status                       # tags + serve (no key)
TAILSCALE_API_KEY=tskey-api-... ./scripts/tailscale-acl check
```

When adding keys:

```bash
./scripts/generate-service-secret-workflow-env
./scripts/check-service-secrets
LC_ALL=C ./scripts/test-deploy-tooling
```

## Manual Host Deploys

NAS:

```bash
cd /volume1/docker/homelab-config
./scripts/homelab-deploy --host nasfeo <service>
```

Mac mini:

```bash
cd "${HOME}/homelab-config-runtime"
./scripts/homelab-deploy --host macmini <service>
```

Runner setup: `docs/github-runner.md`.  
Bootstrap: `docs/macmini-bootstrap.md`.  
Dirty/canary model: `docs/deployment-source-of-truth.md`.

Disabling a service in the host manifest does not stop a running container.
Stop the old container manually after verifying the new host.

## Security Notes

- Publish ports on the narrowest useful interface.
- Mac services bind to `127.0.0.1` and use Tailscale Serve for selected ports.
- Friend-facing HTTPS uses Tailscale Services (`svc:`) plus Authentik.
- Containers with `docker.sock` are trusted infrastructure.

## SRE Metadata

Update `services/homelab-sre-agent/services.yaml` when adding or renaming a
repo-managed service. Enable `sre` / `autofix` only deliberately.

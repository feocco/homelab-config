# Homelab Config

Runtime configuration for a two-host Docker homelab. This repo is a **read-only
architecture showcase**: it records durable deploy intent in git. It is not a
template to clone and run, and it is not an invitation to contribute.

App source, Dockerfiles, tests, and GHCR publishing live in separate
repositories. Secrets and host-private identity overlays stay off this tree.

## Purpose

- Keep Compose, host placement, routing metadata, dashboards, and SRE intent
  versioned beside the machines that run them.
- Make `main` the deploy source of truth for what should be running.
- Generate operational views (Caddy routes, Homepage cards, service catalog)
  from the same declarative service manifests.

## Design Principles

1. **Intent in git, state on hosts.** Tracked files declare shape. Runtime
   `.env` files and data directories live on the NAS and Mac mini and are not
   committed.
2. **Two-host split.** NAS (`nasfeo`) holds storage-adjacent infrastructure.
   Mac mini (`macmini`) runs app and compute services.
3. **Declare once, generate the rest.** Flat `route_*` / `dashboard_*` fields in
   each service `ops.yaml` feed Caddy, DNS sync helpers, Homepage, and the
   catalog. Generated output is not hand-edited and is not the source of truth.
4. **Secrets stay secret.** `service-secrets.yaml` lists required secret
   *names*. Values live in GitHub Actions secrets and are rendered onto hosts
   at deploy time. Additional identity fingerprints can live in private host
   overlays outside git.
5. **Identity and trust are explicit.** LAN HTTPS under `home.feocco.com`,
   Authentik for app login, and Tailscale Services for friend-facing HTTPS.
   See `docs/adr/0001-unified-homelab-identity.md`.
6. **Proof before mutation.** Real deploys validate declared config before
   `compose up`. Branch deploys are temporary canaries, not durable production
   truth.

## Architecture

```text
GitHub (this repo, main)
        │
        ▼
Self-hosted runners ──► render env ──► docker compose up
        │
        ├── nasfeo   infrastructure, storage-adjacent services, Smoke Signal
        └── macmini  apps, monitoring, Caddy, Homepage, Authentik

ops.yaml ──► generate-caddy-config / generate-homepage-config / catalog
        ──► UniFi + Cloudflare DNS helpers
```

High-level map: [`docs/overview.md`](docs/overview.md).  
Deployment truth model: [`docs/deployment-source-of-truth.md`](docs/deployment-source-of-truth.md).  
Source inventory: [`docs/source-of-truth.md`](docs/source-of-truth.md).

## Workflow (conceptual)

1. An app repo builds and publishes an image to GHCR.
2. This repo declares where that image runs, which ports/routes/dashboard cards
   it gets, and which secret names it needs.
3. A push to `main` (or a manual workflow dispatch) deploys through self-hosted
   runners onto the target host.
4. Generators refresh derived config; Compose brings the service up; optional
   live validation checks the declared outcome.

## Non-goals

- Not a public install guide or reusable product.
- Not open for pull requests or issues (showcase / owner-operated).
- Not a place for live tokens, friend ACL emails, or console deep-links.
- Operator runbooks for the owner live under `docs/` and in agent skills; they
  assume access to the private hosts and Actions secrets.

## License

All rights reserved. See [`LICENSE`](LICENSE). Viewing is welcome; reuse is not
granted by default.

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

- Validate deployment changes with `./scripts/test-deploy-tooling`.
- When secrets or `.env.config` files change, run:
  `./scripts/generate-service-secret-workflow-env`,
  `./scripts/check-service-secrets`, and `./scripts/test-deploy-tooling`.
- Prefer host-aware commands, for example
  `./scripts/homelab-deploy --host macmini <service> --dry-run`.

## Runtime And Deployment Notes

- Mac services bind Docker ports to `127.0.0.1` and expose selected ports
  through `hosts/macmini/tailscale-serve.yaml`.
- Mac containers should call other Mac-hosted services through
  `host.docker.internal`.
- NAS-to-Mac calls should use the Mac mini Tailnet name.
- Setting `enabled: false` in a host manifest does not stop an already-running
  container. Stop old containers manually after the new host is verified.

## Footguns

- Do not hand-edit generated secret blocks in `.github/workflows/deploy.yml`.
  Update `service-secrets.yaml` or host manifests, then run the generator.
- Never commit real `.env` files or runtime `data/` contents.

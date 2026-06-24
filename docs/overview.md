# Homelab Overview

High-level map for understanding the deployed homelab quickly.

## Architecture

- Two Docker hosts split infrastructure and application workloads.
- NAS keeps storage-adjacent, lightweight, always-on infrastructure.
- Mac mini runs app, monitoring, automation workloads.
- Small Compose services follow a microservice-style pattern.

## Networking

- Tailscale exposes Mac services without LAN-wide binds.
- Cloudflare Tunnel publishes selected public services safely.
- Cloudflare Access gates public Mealie access.
- Caddy terminates HTTPS for routed `home.feocco.com` LAN names.
- UniFi DNS maps friendly names to Mac.
- Homepage is the generated local front door at `https://home.feocco.com`.
- Homarr remains available separately at `http://homarr.home.arpa`.

## Deployment

- `homelab-config/main` is deployment source of truth.
- GitHub runners deploy changes onto each host.
- Host manifests decide where services run.
- Shared service folders keep Compose definitions small.
- Secrets flow through GitHub Actions into runtime envs.

## Operations

- Grafana centralizes health, uptime, and cost monitoring.
- Prometheus scrapes containers, hosts, and HTTP endpoints.
- Homepage is the primary clickable service dashboard.
- Homarr remains a separate comparison/transition dashboard.
- Dashy is disabled legacy config.
- Portainer remains NAS Docker management.

## Alerting

- `homelab-functions` centralizes phone notification delivery.
- One log watcher runs per Docker host.
- SRE agent creates issues from serious logs.
- Autofix workflows draft PRs after approval.
- Cooldowns reduce repeated incident noise.

## Applications

- Plant Monitor tracks Home Assistant plant health.
- Bedtime handles nightly Home Assistant nudges.
- hass-janitor audits Home Assistant cleanup needs.
- Mealie manages recipes behind Cloudflare Access.
- Mealie Planner supports recipe planning workflows.
- Instacart history supports grocery/order analysis.

## Storage And Secrets

- Runtime data stays beside deployed services.
- Real secrets never belong in git.
- Persistent `.env` files stay on runtime hosts.
- `service-secrets.yaml` maps required secret names.

## Start Here

- Read this overview for the mental model.
- Open Homepage for clickable service entrypoints.
- Use Grafana to inspect service health.
- Use GitHub Actions to inspect deploy history.
- Use service READMEs for operational details.

## Later

- Revisit NetAlertX for network inventory.
- Add backups for stateful services.
- Keep docs paired with dashboards.

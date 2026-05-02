---
name: homelab-docker-deploy
description: "Use when Codex needs to add, update, or troubleshoot deployment of a Dockerized service to Joe Feocco's homelab NAS using the established workflow: app repo builds a GHCR image, private homelab-config repo stores Docker Compose runtime config, services.yaml whitelists deployable services, and the nasfeo self-hosted GitHub Actions runner deploys changes. Trigger for requests involving homelab deployment, Synology/NAS Docker deployment, GHCR images, homelab-config, services.yaml, remote Docker Compose rollout, or adding a future repo to the same deployment pattern."
---

# Homelab Docker Deploy

## Core Rule

Keep application code and runtime configuration separate.

- App repos own source code, Dockerfile, tests, and GHCR image publishing.
- `/Users/feocco/homelab-config` owns NAS runtime config, service folders, Compose files, and deploy orchestration.
- NAS runtime path is `/volume1/docker/homelab-config`.
- Never commit real secrets. Use `.env.example` in git and runtime `.env` files on the NAS.

## Workflow

1. Inspect the app repo.
   - Identify the service name, startup command, exposed port, persistent data path, required env vars, and required config files.
   - Prefer `ghcr.io/feocco/<service>:latest` unless the user asks for a different image name.
   - If the app repo already has Docker and GHCR publishing, update instead of replacing.

2. Prepare the app repo image.
   - Add or update `Dockerfile`.
   - Add or update `.github/workflows/container.yml`; use `assets/container-ghcr.yml` as the baseline.
   - Keep runtime secrets and local config out of the app repo with `.gitignore`.
   - Run app tests and a local Docker build when feasible.
   - Commit and push the app repo so GHCR receives a fresh image.

3. Register the service in homelab config.
   - Work in `/Users/feocco/homelab-config`.
   - Create one service folder per deployable service, for example `my-service/docker-compose.yml`.
   - Use `assets/docker-compose.service.yml` as the baseline.
   - Add `.env.example`; do not add real `.env`.
   - Add config files only when they belong in the private homelab-config repo.
   - Add `data/.gitkeep` for persistent state directories, not real runtime data.
   - Add the service to `services.yaml`:

```yaml
services:
  my-service:
    path: my-service
    enabled: true
```

4. Validate locally before pushing homelab config.
   - Run `./scripts/test-deploy-tooling`.
   - Run `./scripts/homelab-deploy --list`.
   - Run `./scripts/homelab-deploy <service> --dry-run --deploy-base-dir /Users/feocco/homelab-config`.

5. Push and verify the NAS deployment.
   - Push `homelab-config/main`.
   - Watch the deploy workflow: `gh run watch <run-id> --repo feocco/homelab-config --exit-status`.
   - Inspect the deploy log and confirm it says `Deploying <service> from /volume1/docker/homelab-config/<service>`.
   - If the service changed but the log says `No enabled services to deploy.`, debug `services.yaml`, service path matching, and runner shell portability.

## Deployment Facts

- Homelab repo: `https://github.com/feocco/homelab-config`
- Local homelab repo: `/Users/feocco/homelab-config`
- NAS host: `nasfeo`
- NAS config path: `/volume1/docker/homelab-config`
- Runner labels: `self-hosted`, `nasfeo`
- Compose on NAS is v1; use `docker-compose` compatibility.
- The deploy script supports `--list`, `--changed`, `--all`, `<service>`, `--dry-run`, `--base-dir`, and `--deploy-base-dir`.

## Guardrails

- Do not put service runtime config in the public app repo unless it is intentionally generic.
- Do not overwrite `.env` or `data/`; the workflow excludes `./*/.env` and `./*/data`.
- Do not make one giant Compose file unless services are tightly coupled.
- For public images, no NAS registry login is needed. For private GHCR images, confirm the NAS has a GHCR login with package read access.
- Keep deploy scripts portable across macOS, Synology shell, and the Dockerized runner. Avoid fragile shell features in `homelab-config/scripts`.
- When SSH access works, prefer non-interactive checks and avoid asking for passwords or tokens in chat.

## References

- Read `references/homelab-pattern.md` when exact commands, file layout, or troubleshooting details are needed.
- Copy and adapt `assets/container-ghcr.yml` for app repo GHCR publishing.
- Copy and adapt `assets/docker-compose.service.yml` for a new homelab service folder.
- Copy and adapt `assets/env.example` for service env documentation.

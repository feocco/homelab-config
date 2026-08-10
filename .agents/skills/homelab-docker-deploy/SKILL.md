---
name: homelab-docker-deploy
description: "Use when Codex needs to add, update, or troubleshoot deployment of a Dockerized service to Joe Feocco's multi-host homelab using the established workflow: app repo builds a GHCR image, private homelab-config repo stores Docker Compose runtime config, host service inventories whitelist deployable services, and self-hosted GitHub Actions runners deploy changes. Trigger for requests involving homelab deployment, Docker deployment, GHCR images, homelab-config, services.yaml, remote Docker Compose rollout, or adding a future repo to the same deployment pattern."
---

# Homelab Docker Deploy

## Core Rule

Keep application code and runtime configuration separate.

- App repos own source code, Dockerfile, tests, and GHCR image publishing.
- `$HOME/code/homelab-config` owns runtime config, service folders, Compose files, and deploy orchestration for all homelab Docker hosts.
- `homelab-config/main` is the durable production source of truth.
- Branch deploys are temporary canaries. Dirty deploys are emergency-only and
  require an explicit override.
- NAS runtime path is `/volume1/docker/homelab-config`.
- Mac mini runtime path is `${HOME}/homelab-config-runtime`.
- Never commit real secrets. Use `.env.example` and tracked `.env.config` for
  non-secret runtime config, with runtime `.env` files rendered on the NAS.

## Workflow

0. Classify the change before editing `homelab-config`.
   - App code changed only: commit and push the app repo, wait for or trigger
     the app repo GHCR image publish, then run an operational redeploy through
     the `homelab-config` workflow. Do not edit `homelab-config` unless the
     runtime shape also changed.
   - Runtime config changed: update the app repo if needed, then make the
     matching `homelab-config` change for env vars, secrets, ports, volumes,
     host placement, image names/tags, commands, health checks, dashboard
     links, monitoring, or SRE metadata.
   - Third-party or config-only service changed: make the durable change in
     `homelab-config`; there may be no app repo involved.
   - If the change is app-code-only, the expected deploy is operational:
     `compose pull` plus `compose up -d --force-recreate` through the
     `homelab-config` deploy workflow. A plain container restart is not enough
     to fetch a new remote image.

1. Inspect the app repo.
   - Identify the service name, startup command, exposed port, persistent data path, required env vars, and required config files.
   - Prefer `ghcr.io/feocco/<service>:latest` unless the user asks for a different image name.
   - If the app repo already has Docker and GHCR publishing, update instead of replacing.

2. Decide repo and image visibility.
   - Ask Joe whether the app repo and GHCR image should be public or private before publishing a new service.
   - Recommend public when the app repo contains only sanitized source code, Dockerfile, tests, docs, and `.env.example`.
   - Recommend private when the repo contains sensitive implementation details, private config, real identifiers that should not be public, or anything that makes anonymous image pulls inappropriate.
   - If anything looks sketchy or borderline, call it out explicitly before publishing.
   - Public GHCR images can be pulled by the NAS without registry auth. Private GHCR images require confirming the NAS has GHCR login/package read access before deploying.

3. Prepare the app repo image.
   - Add or update `Dockerfile`.
   - Add or update `.github/workflows/container.yml`; use `assets/container-ghcr.yml` as the baseline.
   - Keep runtime secrets and local config out of the app repo with `.gitignore`.
   - Run app tests and a local Docker build when feasible.
   - Commit and push the app repo so GHCR receives a fresh image.
   - After the first image publish, verify the GHCR package visibility matches the decision. If it should be public, confirm anonymous pull metadata works before NAS deployment.

4. Register the service in homelab config.
   - Work in `$HOME/code/homelab-config`.
   - Inspect `git status --short --branch` before editing or deploying.
   - Create one service folder per deployable service, for example `my-service/docker-compose.yml`.
   - Use `assets/docker-compose.service.yml` as the baseline.
   - Choose a host deliberately:
     - Default app/compute services to `macmini`.
     - Keep stable infrastructure, storage-adjacent services, Portainer, the NAS runner, and NAS-only utilities on `nasfeo`.
     - Leave experimental/heavy infra disabled until Joe explicitly asks to enable it.
   - Add the service to exactly the host inventories where it should run: `hosts/nasfeo/services.yaml` and/or `hosts/macmini/services.yaml`.
   - For Mac-hosted HTTP services, add a host override in `hosts/macmini/<service>.env.config` with `HOST_BIND_ADDR=127.0.0.1`. Legacy owner-only port mappings and isolated named Tailscale Services are both declared in `hosts/macmini/tailscale-serve.yaml`; friend-facing applications use a named service carrying raw TCP 443 to Caddy, never a direct application port.
   - For Mac-hosted user-facing HTTP services, use `$homelab-https-route` to
     add the Caddy/UniFi/Cloudflare route fields and validation. The default is
     a private `*.home.feocco.com` HTTPS route; use the Mealie-style
     split-horizon pattern only for services that should be reachable from the
     public internet without Tailscale.
   - When an application adopts Authentik, application sessions, member/admin
     groups, or friend-facing authenticated access, use
     `$homelab-authentik-app-integration` to coordinate the app repo, Authentik
     blueprint, secrets, route, and authorization validation.
   - For Mac containers calling other Mac-hosted services, use `host.docker.internal`. For NAS-to-Mac calls, use the Mac mini Tailnet name once NAS Tailscale is verified.
   - For user-facing HTTP services, add monitoring coverage in
     `services/homelab-monitor/prometheus/prometheus.yml` under
     `blackbox-http`, add the important service containers to the Grafana
     `homelab_container_restart` alert regex, and update
     `scripts/check-macmini-monitor-health` so validation fails if the probe
     or container metrics are missing. State explicitly if monitoring is
     intentionally deferred.
   - Add `.env.example`; do not add real `.env`.
   - If the service needs runtime environment values, use `$homelab-github-secrets` to add tracked non-secret values to `<service>/.env.config`, add only sensitive keys to `service-secrets.yaml`, upload ignored local `.env` secret values to GitHub Actions secrets, regenerate workflow secret mappings, and validate rendering.
   - Make an explicit SRE decision for every repo-managed app service:
     - Set `sre.enabled: true` when Joe should receive SRE issues/notifications for container errors.
     - Set `sre.enabled: false` or omit metadata only for infrastructure, intentionally unmanaged, noisy, experimental, or short-lived/dev containers.
   - Add or update `homelab-sre-agent/services.yaml` so the log SRE agent can map the container/image back to the source repo, issue repo, deploy path, runbook, labels, `sre.enabled`, and `sre.autofix` decision.
   - If `sre.enabled: true`, verify the `homelab-sre` GitHub App is installed on the source/issue repo before relying on SRE issue comments, labels, or dispatch. If it is not installed, either install it or leave SRE disabled until it is.
   - Default `sre.autofix` to `false`; set it to `true` only when the source repo has a `homelab-sre-investigate` workflow, an `OPENAI_API_KEY` GitHub Actions secret, an `SRE_GITHUB_TOKEN` or approved bot/app PR token for draft PR creation, the repo is installed for the SRE GitHub App, and Joe explicitly wants draft PR automation for that service.
   - Add config files only when they belong in the private homelab-config repo.
   - Add `data/.gitkeep` for persistent state directories, not real runtime data.
   - Add the service to the chosen host manifest:

```yaml
services:
  my-service:
    path: services/my-service
    enabled: true
```

5. Validate locally before pushing homelab config.
   - Every enabled service should have `services/<service>/ops.yaml`. Run
     `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check config`
     to verify the declared rollout outcome before deploy.
   - For Mac mini HTTPS routes, follow `$homelab-https-route` validation:
     UniFi DNS check before deploy, Caddy-first deploy, strict live validation,
     and public Cloudflare proof for split-horizon routes.
   - For friend-private routes, also prove the public record uses the service
     TailVIP, raw TLS reaches the intended Caddy virtual host, and a friend
     identity cannot connect to an unrelated service.
   - Run `./scripts/test-deploy-tooling`.
   - Run `./scripts/homelab-deploy --host nasfeo --list`.
   - Run `./scripts/homelab-deploy --host macmini --list`.
   - Run `./scripts/homelab-deploy --host <host> <service> --dry-run --deploy-base-dir $HOME/code/homelab-config`.

6. Push, deploy, and make runtime changes durable.
   - Do not perform a durable deploy from a dirty worktree. Commit and push
     first, or use `--allow-dirty` only for an explicit emergency runtime edit
     that will be documented and made durable immediately afterward.
   - For small, validated homelab fixes, prefer pushing or merging to
     `homelab-config/main` before the final deployment.
   - Use a manual `workflow_dispatch` deploy from a feature branch only as a
     canary, emergency validation path, or review step. The deploy script
     requires `--canary` for non-`main` deploys. Treat branch-deployed runtime
     config as temporary until the same change is merged to `main`.
   - If a branch deployment succeeds, promptly merge or push the validated
     change to `main`, then verify `origin/main` contains the exact runtime
     config that was deployed. If practical, redeploy the service from `main`.
   - Do not stop with "branch deployed" as the final state unless Joe explicitly
     wants a temporary branch-only rollout.
   - Open a PR when the change is broad, has meaningful review risk, or the
     working tree contains unrelated local changes. Otherwise, a direct
     validated push to `main` is acceptable for narrow operational fixes.
   - Watch the deploy workflow: `gh run watch <run-id> --repo feocco/homelab-config --exit-status`.
   - Inspect the deploy log and confirm it deploys the intended host and service path.
   - If the service changed but the log says `No enabled services to deploy.`, debug `services.yaml`, service path matching, and runner shell portability.
   - Check `.homelab-deploy-state/<host>/<service>.json` on the runtime host
     when you need evidence of what branch/SHA last deployed a service.
   - After deployment, run
     `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check live`
     to verify declared live health and monitoring proof.
   - For Mac mini HTTPS routes, canary deploy `caddy` first, then the service,
     both with `--canary`, before treating the route as live.
   - Remember that setting `enabled: false` does not stop an already-running container. After a migration, manually stop the old host's container only after the new host is healthy.
   - The final answer must state what was committed, pushed, and deployed. If
     the session ends with branch-only or dirty runtime state, call that out as
     temporary.

## Deployment Facts

- Homelab repo: `https://github.com/feocco/homelab-config`
- Local homelab repo: `$HOME/code/homelab-config`
- NAS host: `nasfeo`
- NAS config path: `/volume1/docker/homelab-config`
- NAS runner labels: `self-hosted`, `nasfeo`
- Mac mini host: `macmini`
- Mac mini runtime path: `${HOME}/homelab-config-runtime`
- Mac runner labels: `self-hosted`, `macmini`, `docker`, `homelab`
- Compose on NAS is v1; use `docker-compose` compatibility.
- Compose on Mac mini is Docker Compose v2 through OrbStack.
- The deploy script supports `--host`, `--list`, `--changed`, `--all`, `<service>`, `--dry-run`, `--force-recreate`, `--canary`, `--allow-dirty`, `--base-dir`, and `--deploy-base-dir`.
- Non-dry-run deploys are blocked from dirty worktrees by default.
- Non-`main` deploys require `--canary` unless `--allow-dirty` is used for an
  emergency.
- Normal Compose deploys include `--remove-orphans` so stale service shape is
  cleaned up during service-scoped deploys.
- Mac mini application ports should bind to `127.0.0.1`. Friend-private access
  uses a named Tailscale Service forwarding raw TCP 443 to Caddy; do not expose
  the direct application port to friends.
- One `homelab-log-watcher` should run on each Docker host. The central SRE agent runs on Mac mini.

## Guardrails

- Do not put service runtime config in the public app repo unless it is intentionally generic.
- Do not overwrite `.env` or `data/`; the workflow excludes `./*/.env` and `./*/data`.
- Do not end at "branch deployed" unless Joe explicitly wants temporary runtime
  state. Merge to `main` and redeploy from `main` when practical.
- Do not deploy a service that requires environment values until `$homelab-github-secrets` has tracked non-secret config, uploaded required secret values, and `./scripts/check-service-secrets` passes.
- Do not omit an SRE decision for repo-managed services. Either add explicit `homelab-sre-agent/services.yaml` metadata or state why the service should intentionally be unmanaged by the SRE agent.
- Do not set `sre.autofix: true` unless the source repo has the wrapper workflow, required GitHub Actions secrets, GitHub App installation, and Joe wants approved Codex draft PRs for that service.
- Do not make one giant Compose file unless services are tightly coupled.
- Do not assume GHCR package visibility from repo visibility. New container packages may start private; verify the package itself.
- For public images, no NAS registry login is needed. For private GHCR images, confirm the NAS has a GHCR login with package read access.
- Keep deploy scripts portable across macOS, Synology shell, and the Dockerized runner. Avoid fragile shell features in `homelab-config/scripts`.
- When SSH access works, prefer non-interactive checks and avoid asking for passwords or tokens in chat.

## References

- Read `references/homelab-pattern.md` when exact commands, file layout, or troubleshooting details are needed.
- Copy and adapt `assets/container-ghcr.yml` for app repo GHCR publishing.
- Copy and adapt `assets/docker-compose.service.yml` for a new homelab service folder.
- Copy and adapt `assets/env.example` for service env documentation.

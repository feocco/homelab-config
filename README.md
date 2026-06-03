# Homelab Config

Private runtime configuration for services deployed across homelab Docker hosts.

This repo is separate from public application repos. It should contain Compose
files, service-specific config, and deployment notes. Keep long-lived tokens and
passwords out of git unless explicitly intended.

## Layout

```text
hosts/
  nasfeo/services.yaml
  macmini/services.yaml
services/
  plant-monitor/
    docker-compose.yml
    .env.example
    .env.config
    plants.yaml
    data/
service-secrets.yaml
scripts/
  homelab-deploy
  install-deploy-script
docs/
  overview.md
  setup-status.md
```

## Standard Deploy Shape

1. Application repo builds an image.
2. Image is pushed to a registry such as GHCR.
3. `hosts/<host>/services.yaml` declares which host runs each service.
4. The target host pulls the image.
5. The target host runs the service with Docker Compose.

## Host Placement

Use the NAS for stable infrastructure and storage-adjacent services. Use the
Mac mini for app and compute services.

Current placement:

- `nasfeo`: `portainer`, the NAS GitHub runner, Pi-hole outside this repo,
  `dashy-redirect`, and `homelab-log-watcher` for NAS container logs.
- `macmini`: `hello-nas`, `bedtime`, `dashy`, `hass-janitor`,
  `homelab-functions`, `homarr`, `homelab-monitor`, `plant-monitor`,
  `homelab-log-watcher`, and `homelab-sre-agent`.
- Disabled for later: `netalertx`.

One log watcher should run on each Docker host. The central SRE agent runs on
the Mac mini, so the NAS must be able to reach the Mac mini over Tailscale for
incident webhooks.

## Service Pattern

Use one folder per service. Do not use one giant Compose file unless services
are tightly coupled.

```text
homelab-config/
  hosts/
    nasfeo/services.yaml
    macmini/services.yaml
  github-runner/
    docker-compose.yml
  services/
    plant-monitor/
      docker-compose.yml
      .env.config
      .env
      plants.yaml
      data/
  scripts/
    homelab-deploy
    install-deploy-script
```

Each host has its own deploy whitelist:

```yaml
host:
  name: macmini
  deploy_base_dir: ${HOME}/homelab-config-runtime

services:
  plant-monitor:
    path: services/plant-monitor
    enabled: true
```

Deploy commands:

```bash
homelab-deploy --host nasfeo --list
homelab-deploy --host nasfeo plant-monitor
homelab-deploy --host macmini hello-nas
homelab-deploy --host nasfeo --changed
homelab-deploy --host macmini --all
```

On the Synology NAS, Compose v1 is installed, so the deploy script uses
`docker-compose`. On the Mac mini, it can use the Docker Compose v2 plugin.

## Runtime Environment

Tracked non-secret runtime values live in each shared service `.env.config`.
Host-specific overrides can live in `hosts/<host>/<service>.env.config` and win
over shared values. Actual tokens, private external URLs, and credentials stay
out of git and are listed in `service-secrets.yaml`.

The deploy workflow renders each host runtime `.env` file from these sources:

1. tracked `services/<service>/.env.config`
2. optional tracked `hosts/<host>/<service>.env.config`
3. GitHub Actions secrets named `<SERVICE_PREFIX>__<ENV_KEY>`

When adding or changing runtime keys, update the service `.env.example`, add
non-secret values to `.env.config`, list only sensitive values in
`service-secrets.yaml`, then run:

```bash
./scripts/generate-service-secret-workflow-env
./scripts/check-service-secrets
./scripts/test-deploy-tooling
```

Manual deploy on the NAS:

```bash
cd /volume1/docker/homelab-config
git pull
./scripts/homelab-deploy --host nasfeo plant-monitor
```

Manual deploy on the Mac mini:

```bash
cd "${HOME}/homelab-config-runtime"
./scripts/homelab-deploy --host macmini hello-nas
```

Runner setup is documented in `docs/github-runner.md`.
For the high-level system map, start with `docs/overview.md`.
For deploy planning and source-of-truth rules around direct deploys, branch
canaries, restore-required changes, dirty deploys, and runtime drift, run
`./scripts/homelab-plan --service <service>` and read
`docs/deployment-source-of-truth.md`.

Disabling a service in `hosts/<host>/services.yaml` only removes it from future
deploys. It does not stop an already-running container. When migrating a
service between hosts, stop the old host container manually after the new host
is verified.

## Security Posture

Runtime `.env` files are persistent and are still the normal way to configure
services on each Docker host. Service `.env` files live beside their Compose
files in the host runtime tree and are excluded from git. Higher-impact NAS
infrastructure credentials, such as the GitHub runner registration token, live
outside the repo-mounted runtime tree under `/volume1/docker/homelab-secrets`.
The NAS GitHub runner registration cache and Actions workdir live outside the
repo-mounted tree under `/volume1/docker/homelab-runner`.

Published service ports should bind to the narrowest useful host interface. Use
the host LAN IP for normal LAN-only access on Linux/Synology instead of Docker's
default all-interface bind. The NAS uses `192.168.1.191`. Mac mini services
should bind containers to `127.0.0.1` and expose selected ports through
Tailscale Serve using `hosts/macmini/tailscale-serve.yaml`.

NAS-to-Mac service calls should use the Mac mini Tailnet name when they cross
hosts. Mac containers that need another Mac-hosted service should use
`host.docker.internal` so OrbStack can route back to the host-local published
port.

Containers with `/var/run/docker.sock` access can effectively control Docker on
the NAS even when the socket mount is marked read-only. Treat those services as
trusted infrastructure and keep their HTTP APIs bound narrowly and token-gated.

## SRE Metadata

`services/homelab-sre-agent/services.yaml` maps Docker containers and images
back to the source repo, deploy config, issue repo, and SRE behavior for log investigations.
When adding or renaming a repo-managed service, update this metadata in the same
change as the relevant host services file.

Set `sre.enabled: true` only after deciding the service should create SRE
issues. Unknown containers and metadata entries without `sre.enabled: true` are
ignored by the SRE agent. Set `sre.autofix: false` by default. Flip it to
`true` only for a service that has the small `homelab-sre-investigate` dispatch
wrapper, the required `OPENAI_API_KEY` and `SRE_GITHUB_TOKEN` GitHub Actions
secrets, and a deliberate decision to allow draft PR creation. The wrapper
should call the reusable workflow in `feocco/homelab-sre-agent` so SRE behavior
stays centrally managed.

The SRE agent reloads this metadata for every incident from the mounted
`/app/config/services.yaml`, so metadata-only deploys take effect without
rebuilding the SRE agent image.

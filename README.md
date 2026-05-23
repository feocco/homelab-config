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
  setup-status.md
```

## Standard Deploy Shape

1. Application repo builds an image.
2. Image is pushed to a registry such as GHCR.
3. `hosts/<host>/services.yaml` declares which host runs each service.
4. The target host pulls the image.
5. The target host runs the service with Docker Compose.

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
  deploy_base_dir: /Users/feocco/homelab-config-runtime

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
cd /Users/feocco/homelab-config-runtime
./scripts/homelab-deploy --host macmini hello-nas
```

Runner setup is documented in `docs/github-runner.md`.

## Security Posture

Runtime `.env` files are persistent and are still the normal way to configure
services on each Docker host. Service `.env` files live beside their Compose
files in the host runtime tree and are excluded from git. Higher-impact NAS
infrastructure credentials, such as the GitHub runner registration token, live
outside the repo-mounted runtime tree under `/volume1/docker/homelab-secrets`.
The NAS GitHub runner registration cache and Actions workdir live outside the
repo-mounted tree under `/volume1/docker/homelab-runner`.

Published service ports should bind to the narrowest useful host interface. Use
the host LAN IP for normal LAN-only access instead of Docker's default
all-interface bind: `192.168.1.191` for `nasfeo` and `192.168.1.43` for
`macmini`. Use `127.0.0.1` only when the service is accessed through an SSH
tunnel, reverse proxy, or another local-only path.

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

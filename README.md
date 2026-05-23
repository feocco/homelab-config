# Homelab Config

Private runtime configuration for services deployed on the NAS.

This repo is separate from public application repos. It should contain Compose
files, service-specific config, and deployment notes. Keep long-lived tokens and
passwords out of git unless explicitly intended.

## Layout

```text
services.yaml
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
3. `services.yaml` declares deployable services.
4. NAS pulls the image.
5. NAS runs the service with Docker Compose.

## Service Pattern

Use one folder per service. Do not use one giant Compose file unless services
are tightly coupled.

```text
homelab-config/
  services.yaml
  github-runner/
    docker-compose.yml
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

`services.yaml` is the deploy whitelist:

```yaml
services:
  plant-monitor:
    path: plant-monitor
    enabled: true
```

Deploy commands:

```bash
homelab-deploy --list
homelab-deploy plant-monitor
homelab-deploy --changed
homelab-deploy --all
```

On this Synology NAS, Compose v1 is installed, so the deploy script uses
`docker-compose`.

## Runtime Environment

Tracked non-secret runtime values live in each service's `.env.config`. Actual
tokens, private external URLs, and credentials stay out of git and are listed in
`service-secrets.yaml`.

The deploy workflow renders each NAS `.env` file from both sources:

1. tracked `<service>/.env.config`
2. GitHub Actions secrets named `<SERVICE_PREFIX>__<ENV_KEY>`

When adding or changing runtime keys, update the service `.env.example`, add
non-secret values to `.env.config`, list only sensitive values in
`service-secrets.yaml`, then run:

```bash
./scripts/generate-service-secret-workflow-env
./scripts/check-service-secrets
./scripts/test-deploy-tooling
```

Manual deploy:

```bash
cd /volume1/docker/homelab-config
git pull
./scripts/homelab-deploy plant-monitor
```

Runner setup is documented in `docs/github-runner.md`.

## Security Posture

Runtime `.env` files are persistent and are still the normal way to configure
services on the NAS. Service `.env` files live beside their Compose files and
are excluded from git. Higher-impact infrastructure credentials, such as the
GitHub runner registration token, live outside the repo-mounted runtime tree
under `/volume1/docker/homelab-secrets`.

Published service ports should bind to the narrowest useful host interface. Use
`HOST_BIND_ADDR=192.168.1.191` for normal LAN-only access on the NAS instead of
Docker's default all-interface bind. Use `127.0.0.1` only when the service is
accessed through an SSH tunnel, reverse proxy, or another local-only path.

Containers with `/var/run/docker.sock` access can effectively control Docker on
the NAS even when the socket mount is marked read-only. Treat those services as
trusted infrastructure and keep their HTTP APIs bound narrowly and token-gated.

## SRE Metadata

`homelab-sre-agent/services.yaml` maps Docker containers and images back to the
source repo, deploy config, issue repo, and SRE behavior for log investigations.
When adding or renaming a repo-managed service, update this metadata in the same
change as `services.yaml`.

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

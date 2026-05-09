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
  plants.yaml
  data/
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
    .env
  plant-monitor/
    docker-compose.yml
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

Manual deploy:

```bash
cd /volume1/docker/homelab-config
git pull
sudo -n /usr/local/bin/homelab-deploy plant-monitor
```

Runner setup is documented in `docs/github-runner.md`.

## SRE Metadata

`homelab-sre-agent/services.yaml` maps Docker containers and images back to the
source repo, deploy config, issue repo, and SRE behavior for log investigations.
When adding or renaming a repo-managed service, update this metadata in the same
change as `services.yaml`.

Set `sre.autofix: false` by default. Flip it to `true` only for a service that
has a `homelab-sre-investigate` workflow, an `OPENAI_API_KEY` GitHub Actions
secret, and a deliberate decision to allow draft PR creation.

The SRE agent reloads this metadata for every incident from the mounted
`/app/config/services.yaml`, so metadata-only deploys take effect without
rebuilding the SRE agent image.

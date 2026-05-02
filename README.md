# Homelab Config

Private runtime configuration for services deployed on the NAS.

This repo is separate from public application repos. It should contain Compose
files, service-specific config, and deployment notes. Keep long-lived tokens and
passwords out of git unless explicitly intended.

## Layout

```text
plant-monitor/
  docker-compose.yml
  .env.example
  plants.yaml
  data/
docs/
  setup-status.md
```

## Standard Deploy Shape

1. Application repo builds an image.
2. Image is pushed to a registry such as GHCR.
3. NAS pulls the image.
4. NAS runs the service with Docker Compose.

Deploy command once SSH/Compose is confirmed:

```bash
cd /volume1/docker/homelab-config/plant-monitor
git pull
docker compose pull
docker compose up -d
```


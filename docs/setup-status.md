# Setup Status

## Done

- Created private homelab config repo structure locally.
- Added `plant-monitor/docker-compose.yml` using `ghcr.io/feocco/plant-monitor:latest`.
- Added runtime config template at `plant-monitor/.env.example`.
- Added placeholder `plant-monitor/plants.yaml`.

## Blocked

- NAS `nasfeo` is not reachable from this Mac right now.
  - `nc -vz nasfeo 22`: no route to host
  - `nc -vz nasfeo 5000`: no route to host

## Next Manual Checks

Run these from a terminal that can reach the NAS:

```bash
ssh <nas-user>@nasfeo 'docker --version && docker compose version'
```

If that works, confirm GHCR login on the NAS:

```bash
echo '<github-token-with-read-packages>' | docker login ghcr.io -u feocco --password-stdin
```

## Open Decisions

- Registry: use GitHub Container Registry first.
- Package visibility: private.
- App repo visibility: per-repo choice; public is fine.
- NAS config repo: private.
- Deployment method: SSH + `docker compose pull && docker compose up -d`.


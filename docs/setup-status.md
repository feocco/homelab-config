# Setup Status

## Done

- Created private homelab config repo structure locally.
- Added `plant-monitor/docker-compose.yml` using `ghcr.io/feocco/plant-monitor:latest`.
- Added runtime config template at `plant-monitor/.env.example`.
- Added placeholder `plant-monitor/plants.yaml`.
- Created private GitHub repo: `feocco/homelab-config`.
- Added GitHub Actions workflow in `feocco/plant-monitor` to build and push the image to GHCR.
- Confirmed the first GHCR build completed successfully.
- Confirmed plant monitor runs on NAS with `docker-compose`.
- Confirmed passwordless sudo works for `/usr/local/bin/homelab-deploy plant-monitor`.
- Added `services.yaml` manifest pattern.
- Added repo-owned `scripts/homelab-deploy`.
- Added repo-owned `scripts/install-deploy-script`.
- Added self-hosted runner deploy workflow scaffold.

## Blocked

- Local GitHub CLI token cannot inspect package metadata because it does not have `read:packages`.
- Self-hosted GitHub Actions runner is not installed yet.

## Next Manual Checks

Confirm the package in GitHub:

```text
GitHub -> Profile/Org -> Packages -> plant-monitor
```

Expected image:

```text
ghcr.io/feocco/plant-monitor:latest
```

Make sure package visibility is public for now.

Run these from a terminal that can reach the NAS:

```bash
ssh <nas-user>@nasfeo 'docker --version && docker-compose version'
```

Install/update the deploy script on the NAS:

```bash
cd /volume1/docker/homelab-config
git pull
sudo scripts/install-deploy-script
sudo -n /usr/local/bin/homelab-deploy --list
sudo -n /usr/local/bin/homelab-deploy plant-monitor
```

## Open Decisions

- Registry: use GitHub Container Registry first.
- Package visibility: public for `plant-monitor`.
- App repo visibility: per-repo choice; public is fine.
- NAS config repo: private.
- Deployment method: self-hosted runner on NAS.

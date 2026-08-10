# Setup Status (historical)

> Archived owner notes from early bring-up. Not current runbook state.


## Done

- Created private homelab config repo structure locally.
- Added `services/plant-monitor/docker-compose.yml` using `ghcr.io/feocco/plant-monitor:latest`.
- Added runtime config template at `services/plant-monitor/.env.example`.
- Added placeholder `services/plant-monitor/plants.yaml`.
- Created private GitHub repo: `feocco/homelab-config`.
- Added GitHub Actions workflow in `feocco/plant-monitor` to build and push the image to GHCR.
- Confirmed the first GHCR build completed successfully.
- Confirmed plant monitor runs on NAS with `docker-compose`.
- Previously confirmed passwordless sudo worked for `/usr/local/bin/homelab-deploy plant-monitor`.
- Added host-aware `hosts/<host>/services.yaml` manifest pattern.
- Added repo-owned `scripts/homelab-deploy`.
- Added repo-owned `scripts/install-deploy-script`.
- Added self-hosted runner deploy workflow scaffold.
- Added Dockerized GitHub runner Compose config.
- Proved Mac mini runner and Tailnet-only `hello-nas` canary deploy.
- Adopted split placement: NAS for stable infra, Mac mini for app/compute services.
- Added generated Homepage front door on Mac mini and retired older dashboard
  services.
- Re-enabled `homelab-monitor` placement on Mac mini, with native Mac host
  metrics and Docker socket container metrics for monitoring.

## Blocked

- Local GitHub CLI token cannot inspect package metadata because it does not have `read:packages`.
- `netalertx` remains disabled until Mac mini host networking and scan
  interface details are validated.

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
./scripts/homelab-deploy --host nasfeo --list
./scripts/homelab-deploy --host nasfeo plant-monitor
```

## Open Decisions

- Registry: use GitHub Container Registry first.
- Package visibility: public for `plant-monitor`.
- App repo visibility: per-repo choice; public is fine.
- NAS config repo: private.
- Deployment method: self-hosted runners per Docker host.
- Future service placement: default app/compute services to `macmini`; keep
  storage-adjacent and NAS infrastructure on `nasfeo`.
- Dashboard placement: `homepage` and `homelab-monitor` run on `macmini`;
  `netalertx` stays deferred.

# Homelab Pattern

## Standard Shape

```text
public-or-private app repo
  Dockerfile
  .github/workflows/container.yml
  source code

private homelab-config repo
  services.yaml
  <service>/
    docker-compose.yml
    .env.example
    data/.gitkeep
```

Flow:

1. App repo pushes `ghcr.io/feocco/<service>:latest`.
2. `homelab-config` declares the runtime Compose project.
3. Push to `homelab-config/main` triggers the NAS runner.
4. Runner syncs files to `/volume1/docker/homelab-config`, preserving runtime `.env` and `data/`.
5. Runner calls `scripts/homelab-deploy --changed`.

## Homelab Commands

```bash
cd /Users/feocco/homelab-config
./scripts/test-deploy-tooling
./scripts/homelab-deploy --list
./scripts/homelab-deploy <service> --dry-run --deploy-base-dir /Users/feocco/homelab-config
```

After pushing:

```bash
gh run list --repo feocco/homelab-config --workflow Deploy --limit 3
gh run watch <run-id> --repo feocco/homelab-config --exit-status
gh run view <run-id> --repo feocco/homelab-config --log
```

If SSH is configured:

```bash
ssh -o BatchMode=yes feocco@nasfeo 'sudo -n /usr/local/bin/homelab-deploy --list'
ssh -o BatchMode=yes feocco@nasfeo 'sudo -n /usr/local/bin/docker ps --filter name=<service>'
ssh -o BatchMode=yes feocco@nasfeo 'sudo -n /usr/local/bin/docker logs --tail=100 <service>'
```

## services.yaml

`services.yaml` is the deploy whitelist. A service deploys only when it is enabled and the changed files include either `services.yaml` or files under that service path.

```yaml
services:
  plant-monitor:
    path: plant-monitor
    enabled: true
```

## Runtime Config

Public app repos should contain only generic examples. Private `homelab-config` may contain reviewed non-secret runtime config when useful. Real tokens and passwords still belong in runtime `.env` files, not git.

The deploy workflow currently excludes:

```text
./.git
./*/.env
./*/data
```

So pushed changes will not overwrite service `.env` or persistent runtime state on the NAS.

## Troubleshooting

- `No enabled services to deploy.` after a service-folder change usually means `services.yaml` parsing failed, the path does not match the changed directory, or the workflow is checking the wrong base directory.
- `executable file not found in $PATH` usually means the app image `CMD` or Compose `command` points to the wrong CLI entry point.
- Docker permission errors inside the runner usually mean the runner container lacks `/var/run/docker.sock` access or the workflow is running Docker outside the approved deploy path.
- Synology has Compose v1, so Compose files should remain compatible with `docker-compose`.
- Runner container shell tools can differ from macOS; avoid non-portable `awk` regex syntax such as interval quantifiers unless already verified in the runner.

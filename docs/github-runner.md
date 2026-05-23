# GitHub Runners

The NAS uses a Dockerized GitHub Actions runner instead of a native DSM runner.
The native path required missing system tools such as `ldd` and `ldconfig`, so
the containerized runner is the lower-maintenance option.

The Mac mini should use a native macOS GitHub Actions runner with labels
`self-hosted`, `homelab`, `docker`, and `macmini`. Keep the NAS runner labels as
`self-hosted`, `nasfeo`, `docker`, and `homelab`.

## Authentication

Use a fine-grained GitHub token first. GitHub App auth is supported by the runner
image and is a good future hardening step, but it adds app creation, private-key
handling, and installation setup.

Token target:

```text
Repository: feocco/homelab-config
Permission: Administration read/write
```

If the fine-grained token does not work with the runner image, use a classic PAT
with `repo` scope as the fallback.

## NAS Install

On the NAS:

```bash
cd /volume1/docker/homelab-config
git pull
sudo mkdir -p /volume1/docker/homelab-secrets
sudo mkdir -p /volume1/docker/homelab-runner/data /volume1/docker/homelab-runner/work
sudo cp github-runner/.env.example /volume1/docker/homelab-secrets/github-runner.env
sudo vi /volume1/docker/homelab-secrets/github-runner.env
sudo chmod 600 /volume1/docker/homelab-secrets/github-runner.env
```

Start the runner:

```bash
cd /volume1/docker/homelab-config/github-runner
docker-compose pull
docker-compose up -d
docker logs --tail=100 github-runner-homelab
```

This runner is intentionally persistent. `CONFIGURED_ACTIONS_RUNNER_FILES_DIR`
stores the runner registration files under `/volume1/docker/homelab-runner/data`,
and the job workspace lives under `/volume1/docker/homelab-runner/work`.
`DISABLE_AUTOMATIC_DEREGISTRATION=true` prevents the image from removing the
GitHub runner registration on normal restarts. If the container gets stuck with
`Cannot configure the runner because it is already configured`, recreate the
container from this Compose file instead of repeatedly restarting the old
container layer.

The runner token env file intentionally lives outside
`/volume1/docker/homelab-config`. The runner container mounts the homelab-config
runtime tree so deploy jobs can sync and render service config; keeping the
runner token, runner registration cache, and runner workdir outside that tree
prevents ordinary deploy jobs from reading those files by path.

If the runner has a stale GitHub session, stop it and reset only the external
registration cache:

```bash
cd /volume1/docker/homelab-config/github-runner
docker-compose down
sudo mv /volume1/docker/homelab-runner/data "/volume1/docker/homelab-runner/data.bak-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p /volume1/docker/homelab-runner/data /volume1/docker/homelab-runner/work
docker-compose up -d
```

Confirm in GitHub:

```text
homelab-config -> Settings -> Actions -> Runners
```

Expected labels:

```text
nasfeo,docker,homelab
```

## Mac Mini Install

Bootstrap SSH key access first, then install a native macOS runner from GitHub:

```text
homelab-config -> Settings -> Actions -> Runners -> New self-hosted runner -> macOS
```

Use the runner name `macmini-homelab` and labels:

```text
macmini,docker,homelab
```

Create the Mac runtime tree before the first deploy. Run this as the same user
that runs the GitHub Actions runner:

```bash
mkdir -p "${HOME}/homelab-config-runtime"
```

Confirm Docker works from the same user account that runs the runner:

```bash
docker version
docker compose version
```

## Deploy Flow

When `homelab-config/main` changes:

1. GitHub sends host-specific jobs to the matching runner.
2. The runner checks out the repo.
3. The workflow syncs repo files to the host runtime path, preserving service
   `.env` and `data/`.
4. `scripts/homelab-deploy --host <host> --changed` deploys affected enabled
   services for that host.

## Missed Deploy Recovery

If the runner was offline and a push deploy was cancelled, GitHub will not replay
that cancelled run automatically. After the runner is back online, later
successful deploy runs will sync the latest committed repo files, but they may
not recreate the container from the cancelled service change. Trigger a targeted
workflow dispatch for the affected service when the missed change should restart
or recreate a container.

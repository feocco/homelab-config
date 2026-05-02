# GitHub Runner

The NAS uses a Dockerized GitHub Actions runner instead of a native DSM runner.
The native path required missing system tools such as `ldd` and `ldconfig`, so
the containerized runner is the lower-maintenance option.

## Authentication

Use a fine-grained GitHub token first. GitHub App auth is supported by the runner
image, but it adds app creation, private-key handling, and installation setup.
That is not worth it for the first repo-scoped runner.

Token target:

```text
Repository: feocco/homelab-config
Permission: Administration read/write
```

If the fine-grained token does not work with the runner image, use a classic PAT
with `repo` scope as the fallback.

## Install

On the NAS:

```bash
cd /volume1/docker/homelab-config
git pull
cd github-runner
cp .env.example .env
vi .env
```

Start the runner:

```bash
cd /volume1/docker/homelab-config/github-runner
docker-compose pull
docker-compose up -d
docker logs --tail=100 github-runner-homelab
```

Confirm in GitHub:

```text
homelab-config -> Settings -> Actions -> Runners
```

Expected labels:

```text
nasfeo,docker,homelab
```

## Deploy Flow

When `homelab-config/main` changes:

1. GitHub sends the job to the NAS runner.
2. The runner checks out the repo.
3. The workflow syncs repo files to `/volume1/docker/homelab-config`, preserving
   `.env` and `data/`.
4. `scripts/homelab-deploy --changed` deploys affected enabled services.


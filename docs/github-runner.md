# GitHub Runners

> **Owner operations notes.** This page documents how *this* homelab was
> stood up. It is not a public install guide. Strangers cannot run these steps
> without host access, Actions secrets, and private overlays that are
> intentionally absent from git.

The NAS uses a Dockerized GitHub Actions runner instead of a native DSM runner.
The native path required missing system tools such as `ldd` and `ldconfig`, so
the containerized runner is the lower-maintenance option.

The Mac mini should use a native macOS GitHub Actions runner with labels
`self-hosted`, `homelab`, `docker`, and `macmini`. Keep the NAS runner labels as
`self-hosted`, `nasfeo`, `docker`, and `homelab`.

## Authentication

Use a dedicated GitHub App for the NAS runner. This avoids refreshing a personal
access token every 30 days and keeps runner registration scoped to this repo.

Create the app with:

```text
Name: homelab-runner
Homepage URL: https://github.com/feocco/homelab-config
Webhooks: disabled
Repository access: only feocco/homelab-config
Repository permission: Administration read/write
```

Install the app on `feocco/homelab-config`, download a private key, and keep the
private key only on the NAS in
`/volume1/docker/homelab-secrets/github-runner.env`.

The runner image expects `APP_ID`, `APP_LOGIN`, and `APP_PRIVATE_KEY`.
`APP_PRIVATE_KEY` must be stored as one line with literal `\n` separators. The
image converts those separators back into real PEM newlines before requesting a
GitHub App installation token.

## NAS Install

From the MacBook, write the NAS env file without printing the private key. Set
`APP_ID` to the GitHub App's numeric app id and `PRIVATE_KEY_PATH` to the
downloaded `.pem` file:

```bash
APP_ID=replace_me
PRIVATE_KEY_PATH="${HOME}/Downloads/homelab-runner.private-key.pem"
escaped_pem="$(
  python3 - "$PRIVATE_KEY_PATH" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).read_text().rstrip("\n").replace("\n", "\\n"))
PY
)"

ssh -t feocco@nasfeo 'set -eu
sudo mkdir -p /volume1/docker/homelab-secrets
sudo tee /volume1/docker/homelab-secrets/github-runner.env >/dev/null
sudo chmod 600 /volume1/docker/homelab-secrets/github-runner.env
sudo chown root:root /volume1/docker/homelab-secrets/github-runner.env
' <<EOF
APP_ID=${APP_ID}
APP_LOGIN=feocco
APP_PRIVATE_KEY=${escaped_pem}
EOF
unset escaped_pem
```

Prepare the runner directories on the NAS:

```bash
cd /volume1/docker/homelab-config
git pull
sudo mkdir -p /volume1/docker/homelab-runner/data /volume1/docker/homelab-runner/work
```

Before restarting the runner, validate that the GitHub App can create a runner
registration token. This command prints only the HTTP status and deletes the
registration token response:

```bash
ssh feocco@nasfeo 'set -eu
image=ghcr.io/myoung34/docker-github-actions-runner:2.336.0
app_token=$(docker run --rm \
  --env-file /volume1/docker/homelab-secrets/github-runner.env \
  --entrypoint bash \
  "$image" \
  -lc '"'"'nl="
"; APP_PRIVATE_KEY="${APP_PRIVATE_KEY//\\n/${nl}}" bash /app_token.sh'"'"')
code=$(curl -sS -o /tmp/github-runner-registration-token.json -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer ${app_token}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/feocco/homelab-config/actions/runners/registration-token)
rm -f /tmp/github-runner-registration-token.json
test "$code" = "201"
echo "GitHub App runner registration token check: $code"
'
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

The runner auth env file intentionally lives outside
`/volume1/docker/homelab-config`. The runner container mounts the homelab-config
runtime tree so deploy jobs can sync and render service config; keeping the app
private key, runner registration cache, and runner workdir outside that tree
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

The NAS runner env file should remain locked down:

```bash
ssh feocco@nasfeo 'sudo stat -c "%a %U:%G %n" /volume1/docker/homelab-secrets/github-runner.env'
```

Expected:

```text
600 root:root /volume1/docker/homelab-secrets/github-runner.env
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

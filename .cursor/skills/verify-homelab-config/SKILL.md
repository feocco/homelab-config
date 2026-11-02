---
name: verify-homelab-config
description: Verify the homelab-config CLI tooling, policy checks, deploy menu, and generated Caddy routes without deploying or reading private values. Use after changing runtime manifests, scripts, routes, auth policy, or workflows.
---

# Verify homelab config

Run this skill from the repository root. The repository has no local server to
launch. Its operator surface is the CLI tooling and the configuration generated
from tracked manifests.

## Launch

Create a proof directory. Keep it after verification.

```bash
cd "$(git rev-parse --show-toplevel)"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export VERIFY_HOMELAB_ARTIFACTS="/opt/cursor/artifacts/verify-homelab-config-${RUN_ID}"
mkdir -p "${VERIFY_HOMELAB_ARTIFACTS}"
```

Do not start Docker Compose, contact a homelab host, sync DNS, or run a deploy.
Do not bypass deploy guards.

## Doctor

Confirm that the runner is present and valid Bash.

```bash
test "$(git rev-parse --show-toplevel)" = "${PWD}"
test -x ./.cursor/skills/verify-homelab-config/scripts/run-verification
bash -n ./.cursor/skills/verify-homelab-config/scripts/run-verification
```

The runner checks all required commands, Python modules, and repository
executables. A missing dependency fails verification without hiding later
results.

## Drive

Run the verifier once.

```bash
./.cursor/skills/verify-homelab-config/scripts/run-verification
```

The runner executes every required check even after a failure. It preserves
combined output in one log per check, writes each exit status to `summary.txt`,
records `git status`, and exits nonzero when any required check fails.
For Caddy syntax, it builds a run-specific verification-only image from
`services/caddy/Dockerfile` with the tracked `CADDY_VERSION`. The Docker context
contains only that Dockerfile. The runner validates with no container network
and removes the verification image on success or failure. It never pulls,
retags, or removes the configured runtime image and does not use registry
credentials. Caddy image commands use an empty Docker client config.

Read the matching file under `features/` before diagnosing a failure.

## Evidence

Keep these files:

- One log per command, including failures.
- The generated `Caddyfile`.
- `git status --short --branch` in `git-status.log`.
- A `summary.txt` with every command, its exit status, and the aggregate result.

Proof is valid only when it comes from this checkout and every required command
ran. Do not include environment variables, `.env` contents, tokens, private
overlays, provider responses, or live host output.

## Cleanup

There is no process to stop. Remove only scratch files created outside
`VERIFY_HOMELAB_ARTIFACTS`. Keep the proof directory and generated Caddyfile.
Unset the run variable when finished.

```bash
unset VERIFY_HOMELAB_ARTIFACTS RUN_ID
```

---
name: homelab-github-secrets
description: "Use when Codex needs to add, update, validate, or troubleshoot runtime environment variables and GitHub Actions secrets for Joe Feocco's homelab-config deployment workflow. Trigger for requests involving service .env files, .env.example contracts, service-secrets.yaml, gh secret set, generated host-scoped deploy workflow secret mappings, or pairing secret updates with the homelab-docker-deploy skill."
---

# Homelab GitHub Secrets

## Core Rule

Keep secret values out of git, but keep the secret contract and non-secret
runtime config in git.

- `.env.example` documents the runtime keys a service expects.
- `<service>/.env.config` stores tracked non-secret runtime values such as
  ports, local service URLs, paths, cooldowns, log levels, and booleans.
- `service-secrets.yaml` is the source of truth only for keys managed through
  GitHub Actions secrets, such as tokens, credentials, and private external
  URLs.
- Ignored service `.env` files can contain local values used to upload/update
  GitHub secrets.
- GitHub Actions secrets store the real values centrally.
- The deploy workflow renders host runtime `.env` files from tracked
  `.env.config`, host overrides, and host-scoped GitHub secrets before Compose
  starts.

Use this skill alongside `homelab-docker-deploy`: deployment config should not be considered ready until required secrets are uploaded and render validation passes.

## Workflow

1. Work in `$HOME/code/homelab-config`.
2. Confirm the service exists in the intended `hosts/<host>/services.yaml` and
   has `services/<service>/.env.example`.
3. Put non-secret runtime values in `<service>/.env.config`:

```dotenv
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8099
LOG_LEVEL=INFO
```

4. Add only sensitive keys to `service-secrets.yaml`:

```yaml
services:
  my-service:
    env:
      - API_KEY
```

5. Ensure the ignored local `<service>/.env` exists and contains real values for every key in `service-secrets.yaml`.
6. Run:

```bash
./scripts/set-service-secrets <service> --repo feocco/homelab-config
./scripts/generate-service-secret-workflow-env
./scripts/check-service-secrets
./scripts/test-deploy-tooling
```

7. Commit `.env.config`, host overrides, `service-secrets.yaml`, generated
   workflow changes, and script/config changes. Never commit `<service>/.env`.
8. Push or PR `homelab-config`, watch the deploy workflow, and validate the
   target host runtime without printing secret values.

For a secret-value-only update where no config commit is needed, run:

```bash
./scripts/set-service-secrets <service> --repo feocco/homelab-config --dispatch
```

This uploads the ignored local `.env` secret values and dispatches the deploy workflow for that service so the container restarts with the new runtime environment.

## Naming Convention

Use service-prefixed GitHub secret names:

```text
<SERVICE_PREFIX>__<ENV_KEY>
```

Examples:

- `hello-nas` + `HELLO_NAS_MESSAGE` -> `HELLO_NAS__HELLO_NAS_MESSAGE`
- `my-service` + `API_KEY` -> `MY_SERVICE__API_KEY`

The app/container still receives the plain env key (`API_KEY`), because `render-service-env` maps the prefixed GitHub secret back into `<service>/.env`.

## Scripts

Prefer the repo scripts over hand-editing.

- `scripts/set-service-secrets <service> --repo feocco/homelab-config`: reads ignored `<service>/.env` and uploads values to GitHub Actions secrets.
- `scripts/set-service-secrets <service> --repo feocco/homelab-config --dispatch`: uploads values and runs the deploy workflow with `force_recreate=true` for that service.
- `scripts/generate-service-secret-workflow-env`: regenerates the marked
  host-scoped `env:` blocks in `.github/workflows/deploy.yml` from
  `service-secrets.yaml` and `hosts/<host>/services.yaml`.
- `scripts/render-service-env --host <host> --all`: used by the deploy workflow
  to write host runtime `.env` files from `.env.config`, host overrides, and
  GitHub secrets.
- `scripts/check-service-secrets`: verifies `service-secrets.yaml`,
  `.env.config`, host `.env.config`, `.env.example`, and generated workflow
  mappings are in sync.

If `service-secrets.yaml` or host service enablement changes, always regenerate
and check the workflow env blocks before committing.

## Validation

Use non-secret validation by checking presence, permissions, and hashes. Do not print real secret values in chat or logs.

Useful host-side validation pattern:

```bash
file_hash=$(sudo awk -F= '$1=="MY_KEY"{sub(/^[^=]*=/,""); printf "%s",$0}' /volume1/docker/homelab-config/services/my-service/.env | sha256sum | awk '{print $1}')
container_hash=$(sudo /usr/local/bin/docker exec my-service sh -c 'printf "%s" "$MY_KEY" | sha256sum' | awk '{print $1}')
test "$file_hash" = "$container_hash" && echo "MY_KEY matches runtime .env"
```

Also check:

```bash
sudo stat -c "%a %n" /volume1/docker/homelab-config/services/my-service/.env
```

Expected mode is `600`.

## Guardrails

- Do not commit real `.env` files.
- Do not add ordinary config values to `service-secrets.yaml`; use tracked
  `.env.config` unless the value is sensitive.
- Do not print secret values to prove validation.
- Do not rely on scripts to dynamically fetch arbitrary GitHub secrets during a workflow run; GitHub requires secret references to appear in workflow YAML before the job starts.
- Use `generate-service-secret-workflow-env` to maintain those explicit
  host-scoped workflow references programmatically.
- Treat `service-secrets.yaml`, `.env.config`, and `.env.example` drift as a deploy blocker.

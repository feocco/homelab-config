# Homelab GitHub Secrets Pattern

## Data Flow

```text
ignored local <service>/.env
  -> scripts/set-service-secrets
  -> GitHub Actions secrets on feocco/homelab-config
  -> generated workflow env block
  -> scripts/render-service-env on the NAS runner
  -> /volume1/docker/homelab-config/<service>/.env
  -> docker-compose env_file
  -> container environment
```

## Files

- `<service>/.env.example`: committed contract of required app/runtime env keys.
- `<service>/.env`: ignored local source of values for upload.
- `service-secrets.yaml`: committed manifest of which keys are managed as GitHub Actions secrets.
- `.github/workflows/deploy.yml`: contains a generated env block between `BEGIN GENERATED SERVICE SECRETS` and `END GENERATED SERVICE SECRETS`.

## Why Generated Workflow Env Is Required

GitHub Actions does not let shell scripts read arbitrary repository secrets by name during a workflow run. Secrets must be explicitly referenced in workflow YAML, for example:

```yaml
HELLO_NAS__HOST_PORT: ${{ secrets.HELLO_NAS__HOST_PORT }}
```

The manifest still helps because `scripts/generate-service-secret-workflow-env` writes those explicit references deterministically.


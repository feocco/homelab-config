# Homelab config verification map

This map covers the repository's maintainer-facing behavior. Run every feature
from the repository root without deploying or reading private configuration.

## Baseline preconditions

- Run the doctor in `../SKILL.md`.
- Create `VERIFY_HOMELAB_ARTIFACTS` as described in the launch instructions.
- Run `../scripts/run-verification`. Its prerequisite check reports missing
  commands, modules, or repository executables.
- Use only tracked public inputs. Do not load `.env` files or host overlays.

## Driving conventions

- Run commands from the repository root.
- Let the runner set each command's required environment.
- Treat a nonzero runner exit as failed verification.
- Use `summary.txt` and the matching feature log for diagnosis.
- Let Caddy validation build and remove its verification-only local image. Do
  not supply registry credentials.
- Do not use deploy commands, DNS apply modes, or deploy guard bypasses.

## Proof and skip reporting

- The runner saves combined output and the exit status for each command.
- The runner saves generated files under `VERIFY_HOMELAB_ARTIFACTS`.
- Report a missing dependency or command as a failure.
- Do not report an individual pass as proof that another entry point works.
- Do not capture secrets, private values, provider output, or live host data.

## Features

- [Deploy tooling](./deploy-tooling.md) covers the complete repository suite.
- [Deploy events](./deploy-events.md) covers structured deploy and check logs.
- [Workflow policy](./workflow-policy.md) covers workflow safety and fixtures.
- [Route authentication](./route-auth.md) covers the shared IdP policy.
- [Deploy service choices](./deploy-service-choices.md) covers the manual
  service menu.
- [Caddy routes](./caddy-routes.md) covers render and repository validation.

# Deploy service choices

Deploy service choices verifies that every tracked service directory appears in
the manual `workflow_dispatch` service menu.

## Sub-features

- `choice-source` reads service names from `services/`.
- `choice-menu` reads options from `.github/workflows/deploy.yml`.
- `choice-coverage` reports every service missing from the manual menu.
- `choice-native` delegates to the repository check when that check exists.

## How to get to it (user POV)

- Run the verification skill's deploy-service helper.

## Driving it with shell

Preconditions:

- `VERIFY_HOMELAB_ARTIFACTS` exists.
- The verification runner is executable.

- **Run verification.** Run
  `./.cursor/skills/verify-homelab-config/scripts/run-verification`.
- **Check menu coverage.** Read `deploy-service-choices.log` and the
  `deploy-service-choices` row in `summary.txt`.
- **Prove success.** Require exit status `0` and a coverage count.
- **Diagnose failure.** Compare each missing service with
  `on.workflow_dispatch.inputs.service.options` in the deploy workflow.

## Gotchas

- The helper delegates to `scripts/tests/check-deploy-service-choices` when the
  repository provides that check. Otherwise, it runs an equivalent read-only
  check.
- A service can exist in `services/` without being enabled on a host. The
  manual menu still needs the service so an operator can select it.

# Workflow policy

Workflow policy prevents untrusted events from reaching protected runners,
requires repository guards, limits default permissions, and pins third-party
actions.

## Sub-features

- `workflow-repository` validates the checked-in workflows.
- `workflow-fixtures` proves that unsafe fixtures fail and safe fixtures pass.
- `workflow-gate` checks the public CI gate and pinned dependency contract.

## How to get to it (user POV)

- Run the policy CLI against `.github/workflows`.
- Run the fixture test entry point.

## Driving it with shell

Preconditions:

- `VERIFY_HOMELAB_ARTIFACTS` exists.
- The verification runner is executable.

- **Run verification.** Run
  `./.cursor/skills/verify-homelab-config/scripts/run-verification`.
- **Validate workflows.** Require exit status `0` for the `workflow-policy`
  row in `summary.txt`.
- **Validate fixtures.** Require exit status `0` for the
  `workflow-policy-fixtures` row and
  `Workflow policy fixture checks passed.` in its log.

## Gotchas

- Do not validate with a different repository name. Repository guard matching
  is part of the policy.
- The fixture test expects unsafe examples to exit with status `1`.
- Do not install an unpinned PyYAML version to work around setup.

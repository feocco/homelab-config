# Deploy tooling

The deploy-tooling suite verifies service inventory, secret rendering,
rollout contracts, generated config, routing, and deploy guards without a live
deployment.

## Sub-features

- `suite-all` runs every check registered in `scripts/test-deploy-tooling`.
- `suite-safe` uses fixtures and dry runs instead of production mutation.
- `suite-result` emits one final success line only after every check passes.

## How to get to it (user POV)

- From the repository root, run the deploy-tooling test entry point.

## Driving it with shell

Preconditions:

- `VERIFY_HOMELAB_ARTIFACTS` exists.
- The verification runner is executable.

- **Run verification.** Run
  `./.cursor/skills/verify-homelab-config/scripts/run-verification`.
- **Inspect the suite.** Read `deploy-tooling.log` and the `deploy-tooling` row
  in `summary.txt`.
- **Prove success.** Require exit status `0` for the row and the final log line
  `Deploy tooling checks passed.`

## Gotchas

- The prerequisite row reports missing commands separately. The runner still
  attempts this suite and every later check.
- Live-proof fixtures use loopback HTTP servers. The suite must not contact
  Grafana, service docs, or other homelab endpoints.
- The suite already runs several focused checks. Run the focused features too
  because they produce smaller diagnostic logs.
- Do not replace the suite with selected scripts.

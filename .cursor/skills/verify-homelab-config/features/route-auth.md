# Route authentication

Route authentication verifies that routed services declare Authentik, an open
tailnet exception, or bearer-token API access under the repository policy.

## Sub-features

- `auth-declared` requires every non-redirect route to declare `route_auth`.
- `auth-values` restricts declarations to the supported auth modes.
- `auth-exceptions` requires open routes and token APIs in the reviewable
  allowlist.
- `auth-bypass` limits forward-auth bypasses to API and health paths.

## How to get to it (user POV)

- Run the route auth policy check against tracked service manifests.

## Driving it with shell

Preconditions:

- `VERIFY_HOMELAB_ARTIFACTS` exists.
- The verification runner is executable.

- **Run verification.** Run
  `./.cursor/skills/verify-homelab-config/scripts/run-verification`.
- **Validate route auth.** Read `route-auth.log` and the `route-auth` row in
  `summary.txt`.
- **Prove success.** Require exit status `0` and
  `route auth policy: ok`.
- **Diagnose failure.** Match the named service to its
  `services/<service>/ops.yaml` and the allowlist in the check.

## Gotchas

- Never build custom auth. If auth is needed, reuse the homelab IdP through
  Authentik. Bots use bearer tokens.
- The check does not force authentication onto a route. It requires an explicit
  reviewed classification.
- Redirect-only routes are exempt.

# Caddy routes

Caddy route verification renders a fresh Caddyfile from tracked `route_*`
metadata and checks the repository's required hosts, targets, redirects, TLS,
and DNS provider directive.

## Sub-features

- `caddy-render` generates a nonempty Caddyfile outside the source tree.
- `caddy-hosts` checks required active and retired hostnames.
- `caddy-targets` checks reverse-proxy ports and redirects.
- `caddy-tls` checks the Cloudflare DNS-01 directive.
- `caddy-syntax` validates the rendered file with an ephemeral Caddy image.

## How to get to it (user POV)

- Render the Caddyfile with `scripts/generate-caddy-config`.
- Run the Caddy route validation script.

## Driving it with shell

Preconditions:

- `VERIFY_HOMELAB_ARTIFACTS` exists.
- The verification runner is executable.

- **Run verification.** Run
  `./.cursor/skills/verify-homelab-config/scripts/run-verification`.
- **Render routes.** Require exit status `0` for `caddy-render` and a nonempty
  `Caddyfile` in the artifact directory.
- **Validate routes.** Require exit status `0` for `caddy-routes`.
- **Validate Caddy syntax.** Require exit status `0` for `caddy-syntax`. The
  runner reads `CADDY_VERSION` from `scripts/caddy-image-env`, builds a
  run-specific verification-only tag from the tracked Dockerfile, validates,
  and removes that tag on success or failure. The build context contains only
  the Dockerfile. The validation container has no network and receives only
  nonsecret placeholder values needed to adapt the generated environment
  directives.
- **Preserve proof.** Keep the generated Caddyfile and all Caddy logs.

## Gotchas

- The validation script renders its own temporary Caddyfile. The preserved
  render proves the exact output from this run.
- The runner does not pull, retag, or remove the configured runtime image and
  does not use registry credentials. It uses an empty Docker client config. A
  build can fetch the public base images declared by the Dockerfile.
- Generated Caddy output is evidence, not source. Do not commit it.
- Do not sync DNS or deploy Caddy as part of verification.

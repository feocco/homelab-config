# ADR 0001: Unified homelab identity

Status: accepted for the Pirate Radio rollout

## Decision

Authentik at `auth.home.feocco.com` is the homelab identity provider. It offers
verified local username/password enrollment and Google login. Google accounts
may link to an existing Authentik account only through `email_link`, and a
source policy must first prove Google's `verified_email` claim. Local accounts
are inactive until Authentik's email-verification stage succeeds.

Applications use OIDC authorization code with PKCE and identify a person by the
immutable `(issuer, subject)` pair. Username, display name, email, and group
names are mutable login-time snapshots. `pirate-radio-users` grants coarse app
access; `pirate-radio-admins` grants maintenance access. Applications must not
authorize from mutable email/username or proxy-supplied identity headers.

Each application owns row authorization and durable user state in its own
Postgres database. Authentik groups do not replace application ownership. For
Pirate Radio, the internal application-user id owns progress/completion and
submission rows. Identity and attribution snapshots remain after an Authentik
account disappears so history remains readable.

## Network identity versus application identity

Tailscale proves that a device/user may establish TCP connections to a named
service. Authentik proves the application user after the connection succeeds.
These controls are intentionally independent: the `group:friends` grant targets
only `svc:authentik` and `svc:pirate-radio` on TCP 443, while Pirate Radio still
requires a valid member session for every non-health route.

Each friend-facing service has a distinct TailVIP. Public Cloudflare DNS-only A
records point a route hostname to its service TailVIP; UniFi split-horizon DNS
continues pointing the same hostname at `192.168.1.43`. The Mac mini forwards
raw TCP 443 from each service to Caddy, preserving TLS SNI and the existing
`home.feocco.com` virtual-host pattern. Friends receive no node-wide Mac mini
grant and cannot reach other Caddy hostnames.

## Boundaries

- Authentik, Google, and Tailscale are reusable platform components.
- The OIDC contract is reusable in concept, but Pirate Radio keeps its
  implementation repo-local until a second application proves the abstraction.
- No Authentik proxy outpost, forward-auth middleware, shared database,
  OpenFGA, Casbin, or tenant framework is introduced.
- `akadmin` is independent break-glass access and is not Joe's daily account.
- Optional TOTP/passkey enrollment is user-managed; MFA is not mandatory in v1.

## Rollback invariant

Before restoring an older unauthenticated Pirate Radio image, revoke or drain
`svc:pirate-radio` from friends. Export Postgres progress into parsed legacy
JSON, restore the prior immutable app image/Compose shape, and preserve both
Postgres volumes and filesystem data. Authentik can remain available or roll
back independently.

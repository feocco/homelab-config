# ADR 0002: Never build custom auth; reuse the homelab IdP when auth is needed

- Status: Proposed
- Amends: [ADR 0001](0001-unified-homelab-identity.md)

## Context

`waiting.home.feocco.com` shipped with its own sign-in form that took a shared
API token and set an app-signed session cookie. That is custom authentication:
a second credential store and session system next to Authentik, with no MFA,
no central logout, and no group policy. ADR 0001 only describes multi-user apps
that are native OIDC clients, so it gave owner-only tools no sanctioned path.

## Decision

Homelab principle: **never build custom auth. If a service needs auth, reuse
the homelab IdP (Authentik).** Services with nothing sensitive can stay open on
the tailnet, and shared-functions calls use the existing tokens. Auth is not
required everywhere. Each Caddy route declares `route_auth`:

| Value | Use |
| --- | --- |
| `authentik_oidc` | Multi-user apps that own per-user data (ADR 0001 contract). |
| `authentik_forward_auth` | Owner-only tools with sensitive content. Caddy gates the route through the Authentik embedded outpost; the app has no login code. |
| `idp` | Authentik itself. |
| `tailnet_open` | Nothing sensitive; open on the tailnet. Listed in the check's allowlist. |
| `api_token` | Machine API using existing bearer tokens. Listed in the check's allowlist. |

Forward-auth rules:

- Caddy strips every client-supplied `X-Authentik-*` header on every request,
  then copies identity headers only from Authentik's auth response. Apps behind
  `authentik_forward_auth` may trust `X-Authentik-*` only because the app port
  binds to the host and is reachable only through Caddy.
- `route_auth_bypass_paths` may list only bearer-token API and health paths
  (`/v1/*`, `/health`, `/docs`, `/openapi.json`, `/metrics`). Browser pages
  never bypass the IdP.
- The ADR 0001 rule "proxy-supplied identity headers are never trusted" still
  holds for `authentik_oidc` apps. It does not apply to forward-auth apps, whose
  only identity source is the Caddy-stripped, Authentik-set header.

`scripts/tests/check-route-auth` enforces this in CI.

## Consequences

- Each forward-auth app needs an Authentik proxy provider (forward auth, single
  application), an application with a group binding, and membership in the
  embedded outpost. The waiting provider is proposed in
  `services/authentik/proposed-blueprints/` and is not applied yet.
- The allowlist is seeded with every currently open route. The check never
  forces auth onto an existing service; it only stops new routes from shipping
  without an explicit choice.

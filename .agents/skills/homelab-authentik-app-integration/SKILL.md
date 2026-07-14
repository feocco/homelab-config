---
name: homelab-authentik-app-integration
description: Use when adding or changing Authentik OIDC login, shared homelab identity, member/admin groups, application sessions, account menus, or friend-facing authenticated access across an app repo and homelab-config.
---

# Homelab Authentik App Integration

## Core Rule

Keep network admission, identity, and application authorization separate.
Tailscale decides who can connect, Authentik proves who signed in, Authentik
groups grant coarse access, and the application owns sessions and row-level
authorization.

Use native OIDC when an application supports it. Do not add an Authentik proxy
outpost, forward-auth middleware, or trusted identity headers as a shortcut.

## Read First

From `$HOME/code/homelab-config`, read:

- `docs/authentication.md` for the high-level architecture and reachability classes.
- `docs/adr/0001-unified-homelab-identity.md` for accepted decisions.
- `services/authentik/README.md` for provider operations and configuration ownership.
- The target app's `AGENTS.md`, architecture, configuration, and security docs.

## Classify The Integration

Before editing, decide:

- Which routes may remain unauthenticated. Usually only health, login, and
  callback qualify.
- Whether the app needs a member group, an administrator group, or both.
- Which user-owned rows or preferences require application authorization.
- Whether access is owner-private, friend-private, or intentionally public.
- Whether the app already has a durable database suitable for users, sessions,
  and ownership.

Friend-private access always uses a named Tailscale Service through Caddy. It is
not a second application-authentication mechanism.

## Application Contract

- Use OIDC authorization code with PKCE, state, and nonce.
- Bind state to the initiating browser, make it one-time, and enforce a short
  callback expiry.
- Key users by immutable `(issuer, subject)`. Never authorize by username,
  email, forwarded headers, or attribution snapshots.
- Refresh username, display name, email, and group snapshots after login.
- Use an application-owned internal user id for row ownership.
- Store opaque sessions in the application's durable store. Cookies are
  host-only, `Secure`, `HttpOnly`, and `SameSite=Lax`; document the expiry and
  renewal policy.
- Validate the configured public origin on state-changing requests.
- Protect APIs, downloads, media ranges, images, manifests, and documentation
  with the same session as application pages.
- Preserve historical attribution when an IdP user disappears.

Keep the implementation repo-local until a second application proves a shared
code package is worthwhile.

## Provider Workflow

1. Add `<app>-users` and, when needed, `<app>-admins` groups to a mounted
   blueprint.
2. Add `services/authentik/blueprints/<number>-<app>.yaml` with the OIDC
   provider, application, policy binding, exact callback URL, groups scope, and
   an invalidation flow containing Authentik's User Logout stage.
3. Use `openid profile email groups` unless the app documents a smaller scope
   set. Do not request unrelated Google scopes.
4. Add client id and secret keys to the Authentik and application service
   contracts. Use `$homelab-github-secrets` to upload and validate values.
5. Keep the shared Google source and verified-email `email_link` policy intact.
   Applications trust Authentik; they do not create separate Google login
   implementations.

Blueprints are durable provider truth. Individual users, credentials, and
group memberships remain runtime identity data. When an Authentik setting
cannot be blueprint-managed, use a checked-in convergence script plus a check;
do not leave an unexplained UI-only setting.

## Account Menu Contract

Provide a compact signed-in indicator showing the current username or display
name. It opens a small menu with:

- **Edit profile**, linking to
  `https://auth.home.feocco.com/if/user/#/settings`.
- **Log out**, revoking the application session and continuing through the
  provider end-session endpoint.

Do not build an application-specific profile editor. Test that logout ends both
the local session and the Authentik browser session instead of silently signing
the user back in.

## Network And Deployment Workflow

1. Use `$homelab-docker-deploy` for the application image, database, runtime
   configuration, monitoring, and durable `main` rollout.
2. Use `$homelab-https-route` for Caddy, UniFi DNS, Cloudflare DNS, and the
   selected reachability class.
3. For friend-private access, add `route_tailscale_service: svc:<app>` and a
   matching `named_services` entry with its approved TailVIP and raw
   `tcp:443 -> tcp://127.0.0.1:443` target.
4. Do not add a friend grant to the Mac mini node or the application's direct
   port. Remove any legacy direct-port mapping before approval.
5. Deploy and validate Authentik configuration before the application. Keep
   friend access disabled until the authenticated app path passes locally.

Google Cloud client creation and Tailscale service approval require their
authenticated provider surfaces. Record the resulting identifiers in the
git-owned contracts without committing secret values.

## Verification

At minimum, prove:

- PKCE, state, nonce, expired/replayed callback, session expiry, and logout behavior.
- Spoofed identity headers are ignored and invalid origins are rejected.
- Unauthenticated requests return `401`; non-admin maintenance requests return `403`.
- Member and administrator group changes take effect after a new login.
- Two users cannot read or overwrite each other's rows.
- Direct protected assets and media range requests require a valid session.
- Local and Google login with the same verified email resolve to one Authentik identity.
- LAN DNS reaches the Mac mini, public DNS reaches the service TailVIP, and raw
  TLS reaches the intended Caddy virtual host.
- A friend identity can reach only its granted named services and cannot
  connect to at least one unrelated Caddy service.

Run the app's focused tests, build, and container build, then run:

```bash
LC_ALL=C ./scripts/test-deploy-tooling
LC_ALL=C ./scripts/validate-service-rollout --service authentik --host macmini --check config --mode strict
LC_ALL=C ./scripts/validate-service-rollout --service <app> --host macmini --check config --mode strict
```

Repeat both service validations with `--check live` after deployment.

## Rollback

Revoke or disable the friend's application service grant first so an older
unauthenticated image is never friend-reachable. Then restore the prior
application image/runtime shape while preserving application and Authentik
database volumes. Authentik can remain available when only the application is
rolled back.

## Guardrails

- Do not share Authentik's database with applications.
- Do not treat email linking as authorization.
- Do not commit OAuth client secrets, session secrets, database passwords, or
  break-glass plaintext.
- Do not extract a shared auth library or account-menu package during the first
  integration. Reassess after a second application adopts the contract.
- Do not finish with a branch-only provider or runtime configuration when the
  rollout is intended to be durable production state.

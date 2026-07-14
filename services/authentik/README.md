# Authentik

Authentik is the homelab identity provider at
`https://auth.home.feocco.com`. Caddy owns HTTPS; only Authentik HTTP port 9000
is published to host loopback. The stack intentionally has no 9443 host port,
Docker socket, or proxy outpost.

The homelab-wide trust model and application adoption contract are documented
in `docs/authentication.md` and
`docs/adr/0001-unified-homelab-identity.md`. This file is the operational
runbook for the deployed provider.

## Configuration ownership

The mounted `blueprints/` directory owns the Feocco Home brand, verified local
enrollment, email recovery, Google verified-email linking, member/admin groups,
and Pirate Radio OIDC application. Secrets are rendered into the ignored `.env`
through the normal service-secret workflow.
The database container receives only its explicit Postgres settings; SMTP,
Google, bootstrap, and OIDC secrets are limited to the Authentik processes.

- `docker-compose.yml` and `ops.yaml` own the pinned runtime shape and image.
- `blueprints/` owns provider configuration that Authentik can reconcile.
- `.env.config`, `.env.example`, `ops.yaml`, and `service-secrets.yaml` own the
  configuration and secret-name contracts; real values stay outside git.
- `scripts/configure-authentik-settings` owns the tenant setting that Authentik
  cannot represent in a blueprint.
- The Authentik database owns runtime users, credentials, group membership,
  enrolled MFA devices, and sessions.

Do not leave a durable provider, flow, source, application, group, or policy as
an unexplained UI-only change. Add it to a blueprint, or document and automate
the exception when the Authentik model cannot be blueprint-managed.

## Break-glass access

The independent `akadmin` user is break-glass only. Its password is generated
locally, hashed with `ak hash_password`, and supplied only as
`AUTHENTIK_BOOTSTRAP_PASSWORD_HASH`. Store the ignored plaintext handoff file in
a password manager before deleting it.

Joe's normal account, not `akadmin`, owns routine group and user management.
Confirm break-glass access after material identity changes without using it as
the daily administrative session.

## Validation

Validate readiness at `/-/health/ready/` and SMTP with:

```bash
docker compose exec authentik-worker ak test_email joe@example.com
```

After configuration or image changes, also verify blueprint application,
verified local enrollment, Google login, account linking, central profile
editing, application login/logout, and recovery email delivery. Run:

```bash
LC_ALL=C ./scripts/validate-service-rollout --service authentik --host macmini --check config --mode strict
LC_ALL=C ./scripts/validate-service-rollout --service authentik --host macmini --check live --mode strict
```

## Account policy

Google's authorized callback is
`https://auth.home.feocco.com/source/oauth/callback/google/`. First-time Google
users must choose a username and are placed in `pirate-radio-users`. The source
policy rejects a Google profile unless `verified_email` is true before
`email_link` matching is allowed.

Local accounts remain inactive until email verification succeeds. Group
definitions and application policy bindings belong in blueprints; membership
for individual people is runtime identity data managed through Authentik.
Mutable username, name, and email attributes are never application identity
keys.

## User profile and application logout

The central self-service profile is
`https://auth.home.feocco.com/if/user/#/settings`. Authentik stores the global
"users can change username" switch on its internally managed tenant model, so
the setting cannot be owned by a blueprint. Apply and verify the one exception
with:

```bash
./scripts/configure-authentik-settings --apply
./scripts/configure-authentik-settings --check
```

`homelab-deploy` runs the apply command after each Authentik deployment, so a
fresh host converges automatically; the explicit commands remain useful for
inspection and repair.

Pirate Radio's OIDC provider uses its own invalidation flow with Authentik's
built-in User Logout stage. Its account menu first revokes the application
session, then visits the provider end-session endpoint without requesting a
post-logout redirect. This prevents an active Authentik SSO session from
immediately signing the browser back in without retaining an ID token in the
application session solely to satisfy redirect validation.

## Adding an OIDC application

1. Define `<app>-users` and, only when needed, `<app>-admins` groups.
2. Add a numbered application blueprint containing the OIDC provider,
   application, exact callback URI, `openid profile email groups` scopes,
   policy binding, and logout flow.
3. Add client id and secret names to Authentik's service contract and upload
   the values through the normal secret workflow.
4. Implement native authorization code with PKCE in the application. Use
   `(issuer, subject)` as identity and keep row authorization application-owned.
5. Use the `homelab-authentik-app-integration` skill to coordinate the app,
   provider, route, validation, and rollout changes.

Do not add a proxy outpost or forward-auth path for an application that can use
native OIDC.

## Backup, recovery, and upgrades

Authentik's Postgres database is the durable source for accounts, credentials,
membership, MFA enrollment, and sessions. Before upgrades or material identity
changes, write a timestamped custom-format dump to secure storage outside the
repo and runtime tree:

```bash
docker compose exec -T authentik-postgres \
  pg_dump -U authentik -d authentik --format=custom \
  > /secure/backup/path/authentik-$(date +%Y%m%d-%H%M%S).dump
```

Keep the database volume during rollback. Recovery should stop the server and
worker, restore a verified dump into Postgres, and restart with an image version
compatible with that database. Perform a restore drill before treating backups
as proven.

For upgrades, update the pinned Authentik image in both `docker-compose.yml`
and `ops.yaml`, review the upstream migration notes, take the database backup,
deploy as a production-host canary, and run the full validation above. Merge to
`main` and redeploy only after local and Google login paths pass.

## External provider boundaries

The Google Cloud project owns the OAuth client and authorized callback; the
blueprint owns how Authentik consumes it. Tailscale administration owns service
approval and grants; route manifests and host configuration own the intended
TailVIP mapping. Reconcile those provider-side actions with git and validation
rather than treating console state as durable configuration.

# Authentik

Authentik is the homelab identity provider at
`https://auth.home.feocco.com`. Caddy owns HTTPS; only Authentik HTTP port 9000
is published to host loopback. The stack intentionally has no 9443 host port,
Docker socket, or proxy outpost.

The mounted `blueprints/` directory owns the Feocco Home brand, verified local
enrollment, email recovery, Google verified-email linking, member/admin groups,
and Pirate Radio OIDC application. Secrets are rendered into the ignored `.env`
through the normal service-secret workflow.
The database container receives only its explicit Postgres settings; SMTP,
Google, bootstrap, and OIDC secrets are limited to the Authentik processes.

The independent `akadmin` user is break-glass only. Its password is generated
locally, hashed with `ak hash_password`, and supplied only as
`AUTHENTIK_BOOTSTRAP_PASSWORD_HASH`. Store the ignored plaintext handoff file in
a password manager before deleting it.

Validate readiness at `/-/health/ready/` and SMTP with:

```bash
docker compose exec authentik-worker ak test_email joe@example.com
```

Google's authorized callback is
`https://auth.home.feocco.com/source/oauth/callback/google/`. First-time Google
users must choose a username and are placed in `pirate-radio-users`. The source
policy rejects a Google profile unless `verified_email` is true before
`email_link` matching is allowed.

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

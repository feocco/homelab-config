# Authentik

Authentik is the homelab identity provider at
`https://auth.home.feocco.com`. Caddy owns HTTPS; only Authentik HTTP port 9000
is published to host loopback. The stack intentionally has no 9443 host port,
Docker socket, or proxy outpost.

The mounted `blueprints/` directory owns the Feocco Home brand, verified local
enrollment, email recovery, Google verified-email linking, member/admin groups,
and Pirate Radio OIDC application. Secrets are rendered into the ignored `.env`
through the normal service-secret workflow.

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

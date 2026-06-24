# Mealie

Mealie runs on the Mac mini and is intended to be published at
`https://mealie.home.feocco.com` through the LAN Caddy route. The older
Cloudflare Tunnel path can stay deployed during migration, but the repo-managed
runtime base URL now points at the LAN HTTPS route.
Cloudflare Access should be the first auth gate; Mealie password login remains
enabled for app accounts, households, recipes, meal plans, and admin settings.

## Runtime

- Host: `macmini`
- App container: `mealie`
- Database container: `mealie-postgres`
- Tunnel container: `mealie-cloudflared`
- Local-only debug URL on the Mac mini: `http://127.0.0.1:9925`
- LAN HTTPS URL: `https://mealie.home.feocco.com`

The Docker port binds to `127.0.0.1`; do not add router port forwarding.

## Cloudflare

The Cloudflare tunnel is named `mealie-macmini` and points
`mealie.home.feocco.com` at:

```text
http://mealie:9000
```

The tunnel token is stored as the GitHub Actions secret
`MEALIE__CLOUDFLARE_TUNNEL_TOKEN`.

Use a URL-safe value for `MEALIE__POSTGRES_PASSWORD`, such as a hex string.
Mealie builds a Postgres connection URL from this value; characters that have
special meaning in URLs can prevent the app from starting.

Cloudflare Access can protect the legacy public tunnel before traffic reaches
Mealie. The initial Access policy allows `Joefeocco@gmail.com` with the one-time PIN
identity provider. Add family members to the same Access application policy
before expecting them to log in.

## Storage

Runtime data is under the service `data/` directory:

- `data/app`: Mealie app data, images, and backup exports.
- `data/postgres`: PostgreSQL data directory.

Mealie's documentation warns that PostgreSQL major-version upgrades require
manual steps. Do not change the Postgres major image tag without planning a
database upgrade or dump/restore.

Backup TODO: fold Mealie into the broader homelab backup strategy. At minimum,
that plan needs scheduled PostgreSQL dumps plus `data/app` archives, restore
testing, retention policy, and off-host storage.

## AI Provider

Configure the AI provider inside Mealie after first login, under the relevant
group settings. Keep provider secrets out of git; if a provider key later needs
to be supplied by environment variable, add it to `service-secrets.yaml` and
regenerate the deploy workflow secret mappings.

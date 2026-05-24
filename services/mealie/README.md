# Mealie

Mealie runs on the Mac mini and is intended to be published at
`https://mealie.feoc.co` through Cloudflare Tunnel and Cloudflare Access.
Cloudflare Access should be the first auth gate; Mealie password login remains
enabled for app accounts, households, recipes, meal plans, and admin settings.

## Runtime

- Host: `macmini`
- App container: `mealie`
- Database container: `mealie-postgres`
- Tunnel container: `mealie-cloudflared`
- Local-only debug URL on the Mac mini: `http://127.0.0.1:9925`
- Public URL: `https://mealie.feoc.co`

The Docker port binds to `127.0.0.1`; do not add router port forwarding.

## Cloudflare

The Cloudflare tunnel is named `mealie-macmini` and points
`mealie.feoc.co` at:

```text
http://mealie:9000
```

The tunnel token is stored as the GitHub Actions secret
`MEALIE__CLOUDFLARE_TUNNEL_TOKEN`.

Important: `feoc.co` currently uses AWS Route53 DNS. Cloudflare Access rejected
the Access app because `mealie.feoc.co` does not belong to a Cloudflare zone.
Do not create the Route53 `mealie.feoc.co` CNAME until Access can protect it.
The remaining choices are:

- delegate `feoc.co` DNS to Cloudflare after migrating existing Route53 records;
- use another domain already managed by Cloudflare;
- accept Mealie-only auth and create a Route53 CNAME to the tunnel, which is not
  the preferred security posture.

## Storage

Runtime data is under the service `data/` directory:

- `data/app`: Mealie app data, images, and backup exports.
- `data/postgres`: PostgreSQL data directory.

Mealie's documentation warns that PostgreSQL major-version upgrades require
manual steps. Do not change the Postgres major image tag without planning a
database upgrade or dump/restore.

## AI Provider

Configure the AI provider inside Mealie after first login, under the relevant
group settings. Keep provider secrets out of git; if a provider key later needs
to be supplied by environment variable, add it to `service-secrets.yaml` and
regenerate the deploy workflow secret mappings.

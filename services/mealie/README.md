# Mealie

Mealie runs on the Mac mini at `https://mealie.feoc.co` through Cloudflare
Tunnel and Cloudflare Access. Cloudflare Access is the first auth gate; Mealie
password login is still enabled for app accounts, households, recipes, meal
plans, and admin settings.

## Runtime

- Host: `macmini`
- App container: `mealie`
- Database container: `mealie-postgres`
- Tunnel container: `mealie-cloudflared`
- Local-only debug URL on the Mac mini: `http://127.0.0.1:9925`
- Public URL: `https://mealie.feoc.co`

The Docker port binds to `127.0.0.1`; do not add router port forwarding. The
public hostname should be a Cloudflare Tunnel public hostname protected by a
Cloudflare Access self-hosted application that only allows Joe and his wife.

## Cloudflare

Create a remotely managed tunnel in Cloudflare Zero Trust, add a public hostname
for `mealie.feoc.co`, and point it at:

```text
http://mealie:9000
```

Copy the tunnel token into `services/mealie/.env` as
`CLOUDFLARE_TUNNEL_TOKEN`, then upload it through the repo secret workflow.

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

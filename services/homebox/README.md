# Homebox

Homebox runs on the Mac mini at `https://inventory.home.feocco.com`.
Caddy terminates HTTPS and proxies to the loopback-only Homebox port. The
Mac mini also exposes port 8105 to owner Tailnet clients through Tailscale
Serve.

## Runtime

- Image: `ghcr.io/sysadminsmedia/homebox:latest`
- Container: `homebox`
- Local URL: `http://127.0.0.1:8105`
- Tailnet URL: `http://maclabs-mac-mini.taildf3445.ts.net:8105`
- HTTPS URL: `https://inventory.home.feocco.com`
- Status API: `GET /api/v1/status`

The status API accepts unauthenticated requests and returns Homebox build,
health, registration, login, and telemetry settings. Other inventory API
endpoints require a bearer token or an authenticated application session.

## Accounts

Homebox requires registration for the first account. The tracked config keeps
registration and local password login enabled. After creating the owner
account, set `HBOX_OPTIONS_ALLOW_REGISTRATION=false` in
`$HOME/homelab-private-config/macmini/homebox.env` if open registration is no
longer wanted.

## Storage

Homebox stores its SQLite database, uploaded files, and generated config under
`/data`. The Compose bind mount persists that directory at `services/homebox/data`.
The image already configures its SQLite and file-storage paths for `/data`, so
the runtime config does not override those settings.

`HBOX_AUTH_API_KEY_PEPPER` is the only required secret. Homebox refuses to
start unless it contains at least 32 bytes. Keep the value stable because
rotating it invalidates issued API keys. Generate it with
`openssl rand -base64 48`.

Back up the whole `data/` directory while the container is stopped, or use a
SQLite-safe backup method before copying the database.

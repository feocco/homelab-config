# Pirate Radio

Pirate Radio polls configured article RSS feeds, sends Joe a Home Assistant
mobile notification for new articles, converts approved articles with OpenAI
TTS, and serves the generated audio library on the Tailnet.

## Runtime

- Images: `ghcr.io/feocco/pirate-radio:latest`, `postgres:17-alpine`
- Host: `macmini`
- Local bind: `127.0.0.1:8103`
- Container bind: `0.0.0.0:8103`
- LAN HTTPS URL: `https://pirate-radio.home.feocco.com/`
- Health: `/health`
- Library/state/Postgres volume: `services/pirate-radio/data`

The reader lists audio from the generated manifest and streams MP3 ranges only
after native OIDC session validation. It does not scan MP3 file contents to
build the listing. Postgres owns application users, hashed sessions, OIDC
transactions, private progress, completion, and submission attribution; media,
story files, RSS state, and manifests remain filesystem-owned.

## Configuration

Non-secret values live in `.env.config`. Required secrets are managed through
GitHub Actions secrets and rendered into the ignored runtime `.env`:

- `OPENAI_API_KEY`
- `X_API_BEARER_TOKEN` for official X Article lookup
- `HA_URL`
- `HA_LONG_LIVED_TOKEN`
- `HOMELAB_FUNCTIONS_TOKEN`
- `POSTGRES_PASSWORD`
- `PIRATE_RADIO_OIDC_CLIENT_ID`
- `PIRATE_RADIO_OIDC_CLIENT_SECRET`

The Postgres container receives only its explicit database variables, not the
application's OpenAI, Home Assistant, or OIDC credentials.

The public route uses Authentik issuer
`https://auth.home.feocco.com/application/o/pirate-radio/`. Friends reach the
same Caddy virtual host through `svc:pirate-radio`; no direct Tailscale Serve
port is retained.

`PWR_HEADLESS=true` is required for the containerized Playwright extraction
path. `PWR_PROFILE_DIR=/data/playwright-profile` keeps the logged-in browser
profile in the persistent runtime volume; that directory contains Pirate Wires
session state and must not be committed.

`PIRATE_RADIO_REAUTH_URL` points auth-required notifications at the Tailnet-only
temporary login browser. Keep that browser on demand, not permanently running,
so it does not hold the same Playwright profile open while extraction runs.

Start the browser when a login-required notification arrives:

```bash
scripts/pirate-radio-reauth-browser start
```

After login is complete and the full article is visible, stop it so the
extractor can use the profile:

```bash
scripts/pirate-radio-reauth-browser stop
```

## Storage

V1 uses the Mac mini Docker persistent service volume because no mounted
NAS-backed media path was available during setup. A NAS migration can move the
library directory later by changing `PIRATE_RADIO_LIBRARY_DIR` and the Compose
volume after read/write/list checks pass on the mounted path.

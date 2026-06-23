# Pirate Radio

Pirate Radio polls the Pirate Wires Substack RSS feed, sends Joe a Home
Assistant mobile notification for new articles, converts approved articles with
OpenAI TTS, and serves the generated audio library on the Tailnet.

## Runtime

- Image: `ghcr.io/feocco/pirate-radio:latest`
- Host: `macmini`
- Local bind: `127.0.0.1:8103`
- Container bind: `0.0.0.0:8103`
- Tailnet URL: `http://maclabs-mac-mini.taildf3445.ts.net:8103/`
- Health: `/health`
- Library/state volume: `services/pirate-radio/data`

The reader lists audio from the generated manifest and lets the browser request
MP3 files directly. It does not scan MP3 file contents to build the listing.

## Configuration

Non-secret values live in `.env.config`. Required secrets are managed through
GitHub Actions secrets and rendered into the ignored runtime `.env`:

- `OPENAI_API_KEY`
- `HA_URL`
- `HA_LONG_LIVED_TOKEN`
- `HOMELAB_FUNCTIONS_TOKEN`

`PWR_HEADLESS=true` is required for the containerized Playwright extraction
path. `PWR_PROFILE_DIR=/data/playwright-profile` keeps the logged-in browser
profile in the persistent runtime volume; that directory contains Pirate Wires
session state and must not be committed.

## Storage

V1 uses the Mac mini Docker persistent service volume because no mounted
NAS-backed media path was available during setup. A NAS migration can move the
library directory later by changing `PIRATE_RADIO_LIBRARY_DIR` and the Compose
volume after read/write/list checks pass on the mounted path.

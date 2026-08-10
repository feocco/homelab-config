# homelab-smoke-signal

Smoke Signal is the NAS-side outage alarm for the Mac mini Docker stack. Grafana
is still the main monitoring system; this service only sends the backup phone
alert when Grafana or the Mac runtime stack appears broadly unavailable.

The app code lives in `feocco/homelab-smoke-signal`. This folder owns only the
runtime deployment contract for `nasfeo`.

## Runtime Behavior

- Fetches canary targets from `homelab-functions`.
- Caches the last successful target payload under `/app/data`.
- Continues checking cached targets if Mac-hosted `homelab-functions` is down.
- Sends one grouped phone notification directly through Home Assistant after
  the outage condition persists for 5 minutes.
- Repeats notifications no more often than every 8 hours by default.
- Exposes `GET /health` on port `8095` for deploy validation.

## Configuration

Tracked non-secret values live in `.env.config`. Secrets are rendered from
GitHub Actions through `service-secrets.yaml`.

Required secrets:

- `HOMELAB_FUNCTIONS_TOKEN`
- `HA_URL`
- `HA_LONG_LIVED_TOKEN`
- `HA_NOTIFY_JOE_SERVICE`

Use `REPEAT_INTERVAL_SECONDS=172800` for a 48-hour vacation repeat window.

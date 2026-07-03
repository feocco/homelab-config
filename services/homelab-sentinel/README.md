# homelab-sentinel

`homelab-sentinel` is the NAS-side outage alarm for the Mac mini Docker stack.
It exists because Grafana, Prometheus, and most app containers run on the Mac
mini, so a Mac Docker/OrbStack outage can also stop normal Grafana alerting.

The service runs on `nasfeo`, checks generated Mac mini canary targets every
minute, and sends one grouped phone notification directly through Home
Assistant when the outage condition persists for 5 minutes.

## Runtime behavior

- Alert when Grafana is down, at least 3 critical canaries fail, or more than
  half of monitored Mac runtime services fail.
- Repeat notifications no more often than every 8 hours by default.
- Store alert state in `services/homelab-sentinel/data/state.json` so cooldown
  survives container restarts.
- Expose `GET /health` on port `8095` for deploy validation.

## Configuration

Tracked config lives in `.env.config`; secrets are rendered from GitHub Actions
through `service-secrets.yaml`.

Required secrets:

- `HA_URL`
- `HA_LONG_LIVED_TOKEN`
- `HA_NOTIFY_JOE_SERVICE`

The target list is generated during deploy from the service catalog:

```bash
./scripts/generate-sentinel-config --output services/homelab-sentinel/config
```

Use `REPEAT_INTERVAL_SECONDS=172800` for a 48-hour vacation repeat window.

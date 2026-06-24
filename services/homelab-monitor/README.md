# Homelab Monitor

Metrics-first Grafana and Prometheus stack for `macmini`.

## Runtime

- Grafana: `https://grafana.home.feocco.com`
- Grafana Tailscale fallback: `http://maclabs-mac-mini.taildf3445.ts.net:3000`
- Prometheus: internal only
- Exporters: internal only
- Phone alerts: Grafana webhook to Mac-hosted `homelab-functions`
- Homelab dashboard: `https://grafana.home.feocco.com/d/homelab-monitoring/homelab-monitoring`
- OpenAI cost dashboard: `https://grafana.home.feocco.com/d/openai-cost-usage/openai-cost-usage`

## Monitored Surface

- Mac mini host metrics through native Homebrew `node_exporter`.
- Docker/container metrics through the local Docker socket `docker-stats-exporter`.
- HTTP availability through blackbox_exporter:
  - Dashy
  - Plant Monitor
  - homelab-functions
  - hass-janitor
  - homelab-log-watcher
  - homelab-sre-agent
  - Hello NAS
  - Homarr
  - Grafana
  - Pi-hole
  - Portainer
  - Synology DSM
  - Home Assistant
- OpenAI API cost and usage metrics through `openai-cost-exporter`.

OpenAI cost collection requires `OPENAI_ADMIN_KEY` through the managed secret
flow. Cost alert thresholds are non-secret config in `.env.config`:
`OPENAI_COST_DAILY_SPEND_SPIKE_THRESHOLD_USD` and
`OPENAI_COST_7D_SPEND_HIGH_THRESHOLD_USD`.

`streamdeck-companion` and Raspberry Pi host metrics are intentionally deferred.
The Pi at `192.168.1.250` responded to ICMP during planning, but the Companion
HTTP port from Dashy was not reachable.

## Mac Mini Notes

The deploy workflow runs `scripts/ensure-macmini-node-exporter` before starting
the Compose stack. That script installs Homebrew `node_exporter`, writes
`--web.listen-address=127.0.0.1:9100`, restarts the brew service, and verifies
the `/metrics` endpoint. Prometheus scrapes it from inside Docker through
`host.docker.internal:9100`.

The old Linux/NAS containerized `node-exporter` and cAdvisor services are not
used on Mac mini because their host mounts target Linux and Synology paths.

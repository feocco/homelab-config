# Homelab Monitor

Metrics-first Grafana and Prometheus stack for `macmini`.

## Runtime

- Grafana: `https://grafana.home.feocco.com`
- Grafana Tailscale fallback: `http://maclabs-mac-mini.taildf3445.ts.net:3000`
- Prometheus: internal only
- Exporters: internal only
- Python exporter sidecars use `python:3.12-slim`; the exporter scripts are
  stdlib-only and do not require Python 3.13.
- Normal phone alerts: Grafana webhook to Mac-hosted `homelab-functions`
- Broad Mac outage alerts: NAS-hosted `homelab-smoke-signal` direct to Home
  Assistant
- Homelab dashboard: `https://grafana.home.feocco.com/d/homelab-monitoring/homelab-monitoring`
- OpenAI cost dashboard: `https://grafana.home.feocco.com/d/openai-cost-usage/openai-cost-usage`

## Monitored Surface

- Mac mini host metrics through native Homebrew `node_exporter`.
- Docker/container metrics through the local Docker socket `docker-stats-exporter`.
- HTTP availability through blackbox_exporter:
  - Homepage
  - Plant Monitor
  - homelab-functions
  - hass-janitor
  - homelab-log-watcher
  - homelab-sre-agent
  - Hello NAS
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

Container memory alerts page at 700 MiB by default. `streaming-sessions-kafka`
uses a 1300 MiB threshold because the Kafka JVM normally reserves about 1 GiB.

## Alerting Boundary

Grafana is the normal alerting and review surface. It is allowed to depend on
the Mac mini because it watches ordinary service, host, container, and cost
signals.

`homelab-smoke-signal` is the small independent alarm on NAS. It fetches and
caches targets from `homelab-functions`, then watches Grafana, Homepage,
`homelab-functions`, and generated Mac runtime service health checks. It sends
one grouped Home Assistant phone alert when the Mac stack is broadly down.

`streamdeck-companion` and Raspberry Pi host metrics are intentionally deferred.
The Pi at `192.168.1.250` responded to ICMP during planning, but the Companion
HTTP port was not reachable.

## Mac Mini Notes

The deploy workflow runs `scripts/ensure-macmini-node-exporter` before starting
the Compose stack. That script installs Homebrew `node_exporter`, writes
`--web.listen-address=127.0.0.1:9100`, restarts the brew service, and verifies
the `/metrics` endpoint. Prometheus scrapes it from inside Docker through
`host.docker.internal:9100`.

The old Linux/NAS containerized `node-exporter` and cAdvisor services are not
used on Mac mini because their host mounts target Linux and Synology paths.

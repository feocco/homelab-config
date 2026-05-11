# Homelab Monitor

Metrics-first Grafana and Prometheus stack for `nasfeo`.

## Runtime

- Grafana: `http://nasfeo:3000`
- Prometheus: internal only
- Exporters: internal only
- Phone alerts: Grafana webhook to `homelab-functions`

## Monitored Surface

- NAS host metrics through node_exporter.
- Docker/container metrics through cAdvisor.
- HTTP availability through blackbox_exporter:
  - Dashy
  - Plant Monitor
  - homelab-functions
  - hass-janitor
  - homelab-log-watcher
  - homelab-sre-agent
  - Hello NAS
  - Pi-hole
  - Portainer
  - Synology DSM
  - Home Assistant

`streamdeck-companion` and Raspberry Pi host metrics are intentionally deferred.
The Pi at `192.168.1.250` responded to ICMP during planning, but the Companion
HTTP port from Dashy was not reachable.

## Version Notes

cAdvisor is pinned to `v0.55.1` even though newer releases exist because
`nasfeo` currently runs Docker `20.10.3`, and cAdvisor `v0.56.0` dropped support
for Docker versions older than 25.0.

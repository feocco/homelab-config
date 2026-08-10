# Homepage

Generated homelab front door sourced from `homelab-config`.

- Primary LAN URL: `https://home.feocco.com`
- Legacy LAN aliases: `http://home.arpa` and `http://homepage.home.arpa`
  redirect through Caddy when those DNS records still exist.
- Config files in `config/` are generated during deploy
- Service tiles come from `dashboard_*` fields in service `ops.yaml` files
- External/manual links come from `manual-links.yaml`
- Remote access links in `manual-links.yaml` use browser protocol handlers such
  as `ssh://` and `vnc://`; client machines must allow those handlers.
- Generated service tiles for enabled Mac mini HTTP services include Homepage
  `siteMonitor` checks against `host.docker.internal:<port><health_path>`.
  These green/red dots are best-effort UI hints; Grafana and Prometheus remain
  the monitoring source of truth.
- Docker socket access is intentionally not mounted

Preview the generated config without writing tracked files:

```bash
tmpdir="$(mktemp -d)"
./scripts/generate-homepage-config --output "$tmpdir"
```

# Homepage

Generated homelab front door sourced from `homelab-config`.

- Primary LAN URL: `https://home.feocco.com`
- Legacy LAN aliases: `http://home.arpa` and `http://homepage.home.arpa`
  redirect through Caddy when those DNS records still exist.
- Homarr remains separate at `https://homarr.home.feocco.com`
- Config files in `config/` are generated during deploy
- Service tiles come from `dashboard_*` fields in service `ops.yaml` files
- External/manual links come from `manual-links.yaml`
- Docker socket access is intentionally not mounted

Preview the generated config without writing tracked files:

```bash
tmpdir="$(mktemp -d)"
./scripts/generate-homepage-config --output "$tmpdir"
```

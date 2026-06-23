# Homepage

Generated homelab front door sourced from `homelab-config`.

- Primary LAN URL: `http://home.arpa`
- Fallback LAN URL: `http://homepage.home.arpa`
- Homarr remains separate at `http://homarr.home.arpa`
- Config files in `config/` are generated during deploy
- Service tiles come from `dashboard_*` fields in service `ops.yaml` files
- External/manual links come from `manual-links.yaml`
- Docker socket access is intentionally not mounted

Preview the generated config without writing tracked files:

```bash
tmpdir="$(mktemp -d)"
./scripts/generate-homepage-config --output "$tmpdir"
```

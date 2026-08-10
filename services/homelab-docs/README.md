# Homelab Docs

Static MkDocs site for searchable homelab documentation.

- LAN HTTPS URL: `https://docs.home.feocco.com`
- Local container port: `127.0.0.1:8112`
- Rendered site: `.site/`
- Build script: `scripts/build-docs-site`

The rendered site is generated during `homelab-docs` deploy and served by
Nginx. Do not commit `.site/`, `.local/mkdocs-src/`, or
`docs/generated/service-index.md`; they are generated views over existing docs
and service manifests.

Deploy order for route changes:

```bash
./scripts/sync-unifi-dns --host macmini --check
./scripts/homelab-deploy --host macmini caddy
./scripts/homelab-deploy --host macmini homelab-docs
```

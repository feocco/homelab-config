# Caddy

LAN reverse proxy and HTTPS terminator for routed homelab services.

## Route Model

Service routes are declared in `services/<service>/ops.yaml` with flat fields:

```yaml
route_hostname: home.feocco.com
route_target_port: 7576
route_https: true
route_dns: unifi
```

`scripts/generate-caddy-config` builds the runtime `Caddyfile` from those
manifests. Do not hand-maintain `services/caddy/Caddyfile`; it is generated
during `homelab-deploy --host macmini caddy`.

Homepage is the first HTTPS route:

- `https://home.feocco.com` -> `host.docker.internal:7576`
- `http://home.arpa` and `http://homepage.home.arpa` redirect to
  `https://home.feocco.com` while the legacy records exist.

## TLS

Caddy uses Automatic HTTPS with the Cloudflare DNS-01 provider module. This
keeps the Mac mini private: Let's Encrypt validates temporary
`_acme-challenge` TXT records in Cloudflare, not inbound access to the Mac mini.

The deployed image is `ghcr.io/feocco/homelab-caddy:2.11.4-cloudflare`, built
from `services/caddy/Dockerfile`. The image workflow verifies
`dns.providers.cloudflare` before pushing.

Required runtime values:

- `CADDY_ACME_EMAIL` in `.env.config`
- `CADDY_HOME_DOMAIN=home.feocco.com` in `.env.config`
- `CLOUDFLARE_API_TOKEN` as a GitHub Actions secret named
  `CADDY__CLOUDFLARE_API_TOKEN`

The Cloudflare token should be scoped to the `feocco.com` zone with DNS edit and
zone read permissions.

## UniFi DNS

Use `scripts/sync-unifi-dns` to check or apply UniFi local DNS records for
routed services:

```bash
./scripts/sync-unifi-dns --host macmini --dry-run
./scripts/sync-unifi-dns --host macmini --check
./scripts/sync-unifi-dns --host macmini --apply
```

Required environment for `--check` and `--apply`:

- `UNIFI_BASE_URL`
- `UNIFI_API_KEY`
- optional `UNIFI_SITE_ID`
- optional `UNIFI_SKIP_TLS_VERIFY=true` for controllers with untrusted local TLS
- optional `UNIFI_CERT_SHA256` and `UNIFI_TLS_SERVER_NAME` to pin the UniFi
  controller certificate instead of disabling TLS verification

For Homepage, UniFi should resolve `home.feocco.com` to the Mac mini bind
address from `hosts/macmini/services.yaml`.

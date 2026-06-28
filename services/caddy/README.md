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
Retired hostnames can set `route_redirect_to` to keep DNS and TLS working while
redirecting users to the replacement service.

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

## Route DNS

Use `scripts/sync-unifi-dns` to check or apply UniFi local DNS records for
routed services. These records point LAN clients to `host.bind_addr`:

```bash
./scripts/sync-unifi-dns --host macmini --dry-run
./scripts/sync-unifi-dns --host macmini --check
./scripts/sync-unifi-dns --host macmini --apply
```

Use `scripts/sync-cloudflare-dns` to check or apply public DNS-only A records
for routed services. These records point off-LAN Tailnet clients to
`host.tailnet_addr`:

```bash
./scripts/sync-cloudflare-dns --host macmini --dry-run
./scripts/sync-cloudflare-dns --host macmini --check
./scripts/sync-cloudflare-dns --host macmini --apply
```

Required UniFi environment for `--check` and `--apply`:

- `UNIFI_BASE_URL`
- `UNIFI_API_KEY`
- optional `UNIFI_SITE_ID`
- optional `UNIFI_SKIP_TLS_VERIFY=true` for controllers with untrusted local TLS
- optional `UNIFI_CERT_SHA256` and `UNIFI_TLS_SERVER_NAME` to pin the UniFi
  controller certificate instead of disabling TLS verification

Required Cloudflare environment for `--check` and `--apply`:

- `CLOUDFLARE_API_TOKEN` or `CADDY__CLOUDFLARE_API_TOKEN`
- optional `CLOUDFLARE_ZONE_ID`
- optional `CLOUDFLARE_ZONE_NAME`, defaulting to `feocco.com`

For Homepage, UniFi should resolve `home.feocco.com` to the Mac mini bind
address from `hosts/macmini/services.yaml`, and Cloudflare should resolve it
to the Mac mini Tailnet address with proxying disabled.
Routes with `route_public_dns: cloudflare-tunnel`, such as Mealie, are skipped
by `sync-cloudflare-dns` because their public DNS path is managed by Cloudflare
Tunnel and Access instead.

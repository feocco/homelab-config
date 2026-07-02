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
Retired service hostnames that no longer have a service manifest belong in
`services/caddy/retired-routes.yaml` so Caddy keeps DNS and TLS working while
redirecting users to the replacement service. Active services can set
`route_redirect_to` in their `ops.yaml`.
UniFi DNS sync includes retired route hostnames so those redirects resolve on
the LAN.
Routes can set `route_dns_alias_target` when the LAN record should be a CNAME
instead of an A record, for example to hide a Cloudflare-proxied hostname's
public AAAA records from local clients.

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

## Private/Public Split-Horizon Routes

Use this pattern only for services that should be reachable from the public
internet without Tailscale while still bypassing Cloudflare Access on the
trusted LAN:

```yaml
route_hostname: mealie.feocco.com
route_target_port: 9925
route_https: true
route_dns: unifi
route_dns_alias_target: mealie.home.feocco.com
route_public_dns: cloudflare-tunnel
```

The DNS paths are intentionally different for the same hostname:

- On the LAN, UniFi local DNS answers the public hostname and sends clients to
  Caddy on the Mac mini bind address.
- Off the LAN, normal public DNS reaches Cloudflare Tunnel and Access.

This is one of several route patterns, not the default for every service. It
does not require Tailscale for off-LAN users. A phone that is not on the home
network and is not connected to Tailscale uses public DNS, reaches Cloudflare,
and gets the Access policy. A phone on the home Wi-Fi uses UniFi DNS and
reaches Caddy directly, as long as it is not bypassing local DNS with encrypted
DNS or a manually configured public resolver.

Prefer `route_dns_alias_target` when the public Cloudflare hostname has `AAAA`
records. A local A record override can still allow public IPv6 answers to leak
through on some clients. A local CNAME to a local-only hostname, plus a UniFi A
record for that local-only hostname, keeps LAN resolution on the private path.

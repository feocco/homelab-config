---
name: homelab-https-route
description: Use when adding, migrating, validating, or troubleshooting HTTPS routes, Caddy, UniFi DNS, Cloudflare DNS, DNS-01 certificates, Tailscale Services, or split-horizon access for Joe Feocco's homelab services.
---

# Homelab HTTPS Route

## Core Rule

Routes are declared in `services/<service>/ops.yaml` and rendered by tooling.
Do not hand-edit generated Caddy output.

## Choose The Route Pattern

- Default private route: use `service.home.feocco.com` for Mac mini
  user-facing HTTP services that should be reachable on LAN and Tailnet.
- Friend-private route: use a distinct named Tailscale Service and TailVIP to
  carry raw TCP 443 to Caddy. This is the only accepted friend-sharing pattern;
  do not grant the Mac mini node or expose a direct application port.
- Public internet without Tailscale: use the Mealie-style split-horizon pattern
  for a specific service. Public DNS stays on Cloudflare Tunnel/Access;
  UniFi DNS sends trusted LAN clients to Caddy.
- Do not route workers, disabled services, backend-only health endpoints, or
  services with incompatible base URL assumptions. Add `route_exempt_reason`
  when the service is intentionally unrouted.

## Manifest Fields

Default private route:

```yaml
route_hostname: service.home.feocco.com
route_target_port: 8100
route_https: true
route_dns: unifi
```

Friend-private route:

```yaml
route_hostname: service.home.feocco.com
route_target_port: 8100
route_https: true
route_dns: unifi
route_tailscale_service: svc:service
```

Add the matching host entry with its approved TailVIP:

```yaml
named_services:
  service:
    enabled: true
    service: svc:service
    tcp_port: 443
    target: tcp://127.0.0.1:443
    tailvip: 100.x.y.z
```

Split-horizon public route:

```yaml
route_hostname: mealie.feocco.com
route_target_port: 9925
route_https: true
route_dns: unifi
route_dns_alias_target: mealie.home.feocco.com
route_public_dns: cloudflare-tunnel
```

Use `route_dns_alias_target` when a Cloudflare-proxied public hostname leaks
public `AAAA` answers to LAN clients. The alias target should be a local-only
hostname that UniFi resolves to the Mac mini bind address.

## Route Workflow

1. Add or update only the service manifest route fields.
2. Generate and inspect runtime Caddy config:

```bash
./scripts/generate-caddy-config --host macmini
```

3. Check or apply LAN DNS:

```bash
./scripts/sync-unifi-dns --host macmini --check
./scripts/sync-unifi-dns --host macmini --apply
```

For credentialed provider operations, use the repository workflow instead of
asking Joe to enter individual records in a provider UI:

```bash
./scripts/dispatch-route-dns --mode check --watch
./scripts/dispatch-route-dns --mode apply --watch
```

The UniFi path requires a one-time `UNIFI_API_KEY` GitHub Actions secret. With
one accessible console, the script discovers it and uses the official cloud
connector. Set the optional `UNIFI_CONSOLE_ID` repository variable only when
the key can access multiple consoles. Keep `UNIFI_BASE_URL` and pinned local
TLS as the fallback, not the default agent path.

4. For private routes, check or apply public DNS-only Tailnet records:

```bash
./scripts/sync-cloudflare-dns --host macmini --check
./scripts/sync-cloudflare-dns --host macmini --apply
```

Default private routes use the host Tailnet address. Friend-private routes use
the named service's recorded TailVIP. UniFi DNS continues using the Mac mini
LAN address in both cases.

For `route_public_dns: cloudflare-tunnel`, do not let repo tooling overwrite
the existing Cloudflare Tunnel/Access record.

5. Validate before deploy:

```bash
LC_ALL=C ./scripts/validate-service-rollout --service <service> --host macmini --check config --mode strict
LC_ALL=C ./scripts/tests/check-caddy-routes
```

6. Deploy Caddy first, then the service. Branch deploys must be canaries on the
production host. Merge to `main` and redeploy from `main` for durable
production truth.

7. Validate live:

```bash
LC_ALL=C ./scripts/validate-service-rollout --service <service> --host macmini --check live --mode strict
curl -skI https://<hostname>/
```

For split-horizon routes also prove public DNS still uses Cloudflare:

```bash
dig @1.1.1.1 <hostname>
```

For friend-private routes, prove the public resolver returns the TailVIP, the
LAN resolver returns the Mac mini LAN address, raw TLS reaches the intended
Caddy virtual host, and a friend identity cannot connect to an unrelated Caddy
service. Run `./scripts/apply-tailscale-serve --dry-run` before applying the
service advertisement.

## Rename A Hostname

Treat a hostname rename as an identity and routing migration:

1. Update `route_hostname`, `live_base_url`, the application's configured
   public URL, and every Authentik launch/callback URL.
2. Add the old hostname to `services/caddy/retired-routes.yaml` with a 308
   redirect to the new origin when compatibility is desired.
3. Generate Caddy, dry-run both DNS providers, then run credentialed DNS check
   and apply through `dispatch-route-dns`.
4. Deploy Authentik/Caddy and the application in a coordinated canary, validate
   the new callback and protected media, then return durable production to
   `main`.

Host-only application cookies do not move to the new hostname, so expect one
normal sign-in after the cutover. A Tailscale Service identity and TailVIP can
stay unchanged when only its DNS hostname changes.

## Rollback

Rollback source truth with Git: revert the route commit or redeploy the prior
known-good `main` SHA. Do not delete service volumes, runtime data, or Caddy
state while debugging a route rollback.

For a friend-private route, revoke the friend grant or service advertisement
before restoring an older application image that lacks authentication.

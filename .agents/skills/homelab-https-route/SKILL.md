---
name: homelab-https-route
description: Use when adding, migrating, validating, or troubleshooting HTTPS routes, Caddy, UniFi DNS, Cloudflare DNS, DNS-01 certificates, or split-horizon access for Joe Feocco's homelab services.
---

# Homelab HTTPS Route

## Core Rule

Routes are declared in `services/<service>/ops.yaml` and rendered by tooling.
Do not hand-edit generated Caddy output.

## Choose The Route Pattern

- Default private route: use `service.home.feocco.com` for Mac mini
  user-facing HTTP services that should be reachable on LAN and Tailnet.
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

4. For default private routes, check or apply public DNS-only Tailnet records:

```bash
./scripts/sync-cloudflare-dns --host macmini --check
./scripts/sync-cloudflare-dns --host macmini --apply
```

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

## Rollback

Rollback source truth with Git: revert the route commit or redeploy the prior
known-good `main` SHA. Do not delete service volumes, runtime data, or Caddy
state while debugging a route rollback.

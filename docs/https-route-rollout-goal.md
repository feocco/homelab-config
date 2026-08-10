# HTTPS Route Rollout Goal

> **Owner operations notes.** This page documents how *this* homelab was
> stood up. It is not a public install guide. Strangers cannot run these steps
> without host access, Actions secrets, and private overlays that are
> intentionally absent from git.

Use this goal when converting one service at a time from direct HTTP/Tailscale
URLs to LAN HTTPS behind Caddy.

## Goal Prompt

`One eligible homelab service is converted to an HTTPS route under home.feocco.com verified by generated Caddy config, UniFi DNS check/apply to the host bind address, Cloudflare DNS check/apply to the host Tailnet address with proxying disabled, strict config validation, a canary deploy on the production host, DNS resolving to the host bind address on LAN, HTTPS returning a non-error response, and strict live validation while preserving existing service containers, ports, secrets, health checks, monitoring, and rollback through the current Git branch and prior runtime config. Use only services/*/ops.yaml route fields, generated Caddy config, scripts/sync-unifi-dns, scripts/sync-cloudflare-dns, scripts/validate-service-rollout, scripts/homelab-deploy --canary, and existing docs/tests. Between iterations, choose the next eligible service from ./scripts/list-https-route-candidates --status eligible, preferring simple single-container app/proxy services with existing health checks before multi-container or externally exposed services. If blocked or no valid paths remain, report the service, blocker, evidence command/output, and the user action or repo change that would unlock progress.`

## Per-Service Verification

For each service:

1. Pick a candidate:
   `./scripts/list-https-route-candidates --status eligible`
2. Add route fields to `services/<service>/ops.yaml`:
   `route_hostname`, `route_target_port`, `route_https: true`, and
   `route_dns: unifi`.
3. Run config checks:
   `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host macmini --check config --mode strict`
4. Sync DNS:
   `./scripts/sync-unifi-dns --host macmini --check`
   `./scripts/sync-unifi-dns --host macmini --apply`
   `./scripts/sync-cloudflare-dns --host macmini --check`
   `./scripts/sync-cloudflare-dns --host macmini --apply`
5. Deploy canary:
   `./scripts/homelab-deploy --host macmini caddy --canary`
   `./scripts/homelab-deploy --host macmini <service> --canary`
6. Prove live behavior:
   `dig +short <hostname>`
   `curl -I https://<hostname>/`
   `LC_ALL=C ./scripts/validate-service-rollout --service <service> --host macmini --check live --mode strict`

Do not add HTTPS routes for workers, disabled services, or services whose app
configuration hard-codes an incompatible external base URL until that service's
runtime config is updated.

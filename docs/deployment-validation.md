# Deployment Validation

`scripts/validate-service-rollout` is the homelab service rollout checker. It
keeps service-specific behavior out of scope and verifies the declared
operational outcome for each enabled service.

## High-Level Units

- App image: source repo, GHCR image, and public/private pull expectation.
- Secrets: `.env.example`, `.env.config`, `service-secrets.yaml`, generated
  workflow env block, and uploaded secret names.
- Runtime config: service folder, Compose file, host manifest, port uniqueness,
  deploy allowlist, and dry-run deploy.
- Tailnet: user-facing HTTP service exposure through
  `hosts/<host>/tailscale-serve.yaml`.
- Route: LAN HTTPS exposure through generated Caddy config and UniFi local DNS.
- Monitoring/SRE: Prometheus blackbox target, restart alert coverage,
  monitor-health coverage, and `homelab-sre-agent` metadata.
- Live proof: health/status endpoint, monitor-health output, and metric series
  after deployment.

## Usage

Each enabled service owns a private runtime manifest:

```text
services/<service>/ops.yaml
```

Run config validation before deploying:

```sh
./scripts/validate-service-rollout --service laundry-monitor --host macmini --check config --mode strict
```

Run live validation after deployment:

```sh
./scripts/validate-service-rollout --service laundry-monitor --host macmini --check live --mode strict
```

Use `--mode smoketest` for canaries, partial rollout debugging, or environments
where live external checks may not be available. Strict mode is for durable
production readiness. A service without declared live proof should pass live
validation by explicitly reporting that live checks were skipped.

## Manifest Shape

The manifest intentionally uses a small dependency-free YAML subset: top-level
scalar keys and top-level lists. The required fields are:

```yaml
service: laundry-monitor
kind: app
host: macmini
source_repo: feocco/laundry-monitor
image: ghcr.io/feocco/laundry-monitor:latest
container: laundry-monitor
secrets:
  - HA_URL
```

Optional fields enable additional units:

- `kind: app|worker|proxy|infra|multi-container` declares the service shape.
- `hosts:` replaces `host:` for multi-host services.
- `images:` and `containers:` replace `image` and `container` for
  multi-container services.
- `http_port` and `port_env` declare user-facing host ports when present.
- `public_image: true` checks anonymous GHCR manifest access.
- `health_path: /health` declares an HTTP health path when one exists.
- `docs_path: /docs` declares the human-facing service docs page for Homepage
  service cards.
- `openapi_path: /openapi.json` declares the machine-readable OpenAPI schema
  for externally callable service APIs.
- `docs_auth_required: true` declares that unauthenticated live validation must
  receive `401` from both the docs and OpenAPI paths.
- `api_framework: aiohttp` records the current service API framework. Valid
  values are `aiohttp`, `fastapi`, `node-http-server`, `python-http-server`,
  `other`, and `none`.
- `status_path: /v1/status` checks the status endpoint identifies the service.
- `live_base_url: http://maclabs-mac-mini.taildf3445.ts.net:8102` enables live
  HTTP validation.
- `tailnet: true` checks Tailscale Serve config and dry-run apply.
- `route_hostname: home.feocco.com` declares the LAN HTTPS hostname.
- `route_target_port: 7576` declares the backend port Caddy should proxy to.
- `route_https: true` requires the hostname to use Caddy HTTPS.
- `route_dns: unifi` requires the route to be present in UniFi local DNS.
- `route_dns_alias_target:` optionally makes the local DNS record a CNAME to a
  local-only hostname, useful when the public hostname is Cloudflare-proxied and
  would otherwise leak public AAAA records on LAN.
- `route_aliases:` optionally lists legacy HTTP hostnames that redirect to the
  HTTPS route.
- `route_redirect_to:` optionally turns a routed hostname into an HTTPS
  redirect instead of proxying to `route_target_port`. Use this for retired
  hostnames that should keep a useful destination.
- Retired hostnames without a service manifest belong in
  `services/caddy/retired-routes.yaml`.
- `route_public_dns: cloudflare-tunnel` opts a route out of DNS-only Tailnet A
  record sync when its public path is intentionally managed by Cloudflare Tunnel
  and Access.
- `route_exempt_reason: backend health endpoint only` blocks a service from the
  HTTPS route candidate list when it exposes health/metrics for operations but
  intentionally has no browser-facing LAN HTTPS route.
- `monitoring: true` checks Prometheus, restart alert, monitor-health, and live
  monitor-health proof.
- `sre: true` checks `homelab-sre-agent` service metadata.
- `tailnet_hosts`, `monitoring_hosts`, `sre_hosts`, and
  `live_base_url_<host>` allow multi-host services to declare host-specific
  outcomes without duplicating manifests.

Some fields are operational assertions rather than values that can be fully
discovered from existing config. `kind`, `public_image`, `status_path`, and
`live_base_url` should be filled from the intended runtime contract.

## Troubleshooting Failures

Missing manifest:

- Add `services/<service>/ops.yaml`.
- Keep the first manifest small and match the flat YAML subset shown above.

Secret mismatch:

- Compare the manifest `secrets:` list with `service-secrets.yaml`.
- Ensure every secret key is documented in `.env.example`.
- Run `LC_ALL=C ./scripts/generate-service-secret-workflow-env`, then
  `LC_ALL=C ./scripts/check-service-secrets`.

GHCR image failure:

- Confirm the app repo workflow published the image tag in `ops.yaml`.
- For `public_image: true`, anonymous `docker manifest inspect <image>` must
  work without local registry credentials.
- For private images, leave `public_image` unset or false and verify host
  registry auth separately.

Runtime config failure:

- Confirm the service is enabled in `hosts/<host>/services.yaml`.
- Check that Compose references the manifest image, container, and port.
- Resolve `SERVICE_PORT` collisions before deploying.
- Run `./scripts/homelab-deploy --host <host> <service> --dry-run`.

Tailnet failure:

- Add or correct the service entry in `hosts/<host>/tailscale-serve.yaml`.
- Run `./scripts/apply-tailscale-serve --host <host> --dry-run`.

Route failure:

- Add or correct the `route_*` fields in `services/<service>/ops.yaml`.
- Run `./scripts/generate-caddy-config --host <host>` and confirm the hostname
  appears.
- Run `./scripts/sync-unifi-dns --host <host> --dry-run` to confirm UniFi DNS
  will point the hostname at the host bind address.
- Ensure `caddy` is enabled on the host and publishes port `443`.

Monitoring or SRE failure:

- Add the Prometheus blackbox target, Grafana restart alert coverage, and
  monitor-health checks when `monitoring: true`.
- Add `services/homelab-sre-agent/services.yaml` metadata when `sre: true`.
- After changing monitor or SRE config, redeploy or force-recreate
  `homelab-monitor` or `homelab-sre-agent` before live validation.

Live proof failure:

- Check the service health URL from `live_base_url` plus `health_path`.
- If the health endpoint returns JSON with `status`, strict mode expects
  `status: ok`.
- If Prometheus series are missing right after deploy, confirm the monitor
  service reloaded and wait for a scrape interval before rechecking.

## Detailed Checks

App image:

- `public_image: true` runs anonymous `docker manifest inspect <image>` to
  prove the declared public pull expectation. Docker Hub rate limits are
  reported as warnings because they do not prove the image is private or
  missing. Registry timeouts are also warnings because they prove the registry
  probe was inconclusive, not that the service image contract is wrong.
- Private images can opt out of that public check; package auth remains a
  deployment concern for the target host.

Secrets:

- `ops.yaml` secret names must match the service entry in `service-secrets.yaml`.
- `.env.example` must document those secret keys.
- `.github/workflows/deploy.yml` must contain generated prefixed secret env
  entries.
- `scripts/check-service-secrets` must pass.
- New services should prefer generic list-style endpoint secrets, such as
  notification endpoint lists, rather than person-specific key names.

Runtime config:

- The selected host manifest must enable the service.
- Compose must reference the manifest images, containers, and declared port.
- The declared host port must match `port_env` in `.env.config` and be unique
  among services enabled on the same host.
- `scripts/homelab-deploy --host <host> <service> --dry-run` must pass.

Reachability class:

- Owner-private routes use the normal `*.home.feocco.com` pattern and the host
  Tailnet address for Joe's off-LAN access.
- Friend-private routes use `route_tailscale_service` and a distinct named
  Tailscale Service. This is the only accepted friend-sharing pattern.
- Intentionally public routes use the Cloudflare Tunnel/Access split-horizon
  pattern. They are a separate exposure decision, not an alternative way to
  share a private service with friends.

Tailnet:

- `tailnet: true` requires an entry in `hosts/<host>/tailscale-serve.yaml` with
  the manifest HTTP port.
- `route_tailscale_service: svc:<name>` requires an enabled entry under
  `named_services` with a recorded CGNAT TailVIP and raw
  `tcp:443 -> tcp://127.0.0.1:443` forwarding. This remains separate from
  legacy node HTTP mappings and preserves Caddy TLS SNI.
- A Tailscale Service host must have a tag-based identity. Before converting an
  existing user-owned node, audit its user-based grants and add an appropriate
  `tagOwners` entry. Merge `docs/tailscale-friends-policy.hujson` into the
  existing policy; do not replace the policy wholesale.
- `scripts/apply-tailscale-serve --dry-run` must pass.

Route:

- `route_hostname` must be a public DNS name, not `.home.arpa`, so Caddy can
  use public ACME certificates.
- `route_dns: unifi` routes LAN clients by local DNS. The preferred
  `sync-unifi-dns` path uses `UNIFI_API_KEY` to discover the console and call
  the Network API through the official UniFi cloud connector. Set optional
  `UNIFI_CONSOLE_ID` when the key can access multiple consoles. Local fallback
  uses `UNIFI_BASE_URL`, optional `UNIFI_SITE_ID`, and either optional
  `UNIFI_CERT_SHA256`/`UNIFI_TLS_SERVER_NAME` for pinned TLS or optional
  `UNIFI_SKIP_TLS_VERIFY` for temporary bootstrap.
- `scripts/sync-cloudflare-dns` routes off-LAN Tailnet clients by public
  DNS-only A records. Routes with `route_tailscale_service` use that service's
  TailVIP; other routes use `host.tailnet_addr`. It uses `CLOUDFLARE_API_TOKEN` or
  `CADDY__CLOUDFLARE_API_TOKEN`, optional `CLOUDFLARE_ZONE_ID`, and defaults
  the zone name to `feocco.com`.
- For services that should be reachable from the public internet without
  Tailscale, use the private/public split-horizon pattern. The same public
  hostname has two paths: UniFi DNS sends LAN clients to the Mac mini bind
  address, while Cloudflare public DNS sends off-LAN clients through
  Tunnel/Access. Use `route_public_dns: cloudflare-tunnel` so
  `sync-cloudflare-dns` does not overwrite the Tunnel record. If local clients
  still reach Cloudflare because public `AAAA` records leak through, set
  `route_dns_alias_target` to a local-only hostname and keep that alias in
  UniFi DNS.
- Caddy gets certificates with Cloudflare DNS-01. `CLOUDFLARE_API_TOKEN` is a
  Caddy service secret and should be scoped to DNS edit/zone read for
  `feocco.com`.
- Credentialed provider checks and mutations run through
  `scripts/dispatch-route-dns`, which dispatches `.github/workflows/route-dns.yml`.
  Review local provider dry-runs first, use `--mode check`, then use
  `--mode apply`; the workflow verifies state again after every apply.

Split-horizon proof:

- LAN resolver: `dig @192.168.1.1 <hostname> A` resolves to the Mac mini bind
  address or to a local CNAME that resolves to that address.
- LAN HTTPS: `curl -skI -w '%{remote_ip}' https://<hostname>/` returns the Mac
  mini bind address and no Cloudflare Access redirect.
- Public resolver: `dig @1.1.1.1 <hostname>` follows the intended public
  Cloudflare path, not the private LAN address.
- Public Access: forcing the public Cloudflare IP with `curl --resolve` returns
  the Cloudflare Access login or redirect for protected services.

Friend-service proof:

- The LAN resolver returns the Mac mini LAN address, while `dig @1.1.1.1
  <hostname> A` returns the service's recorded TailVIP.
- Raw TCP 443 forwarding reaches the intended Caddy virtual host with its
  normal certificate and application authentication; the service does not
  expose a direct application port to friends.
- A designated friend identity can reach the named Authentik and application
  services on TCP 443 but cannot establish a connection to at least one
  unrelated Caddy service.
- The application still proves unauthenticated, member, and administrator
  behavior independently of the Tailscale grant.
- Any replaced legacy direct-port mapping is absent from
  `hosts/<host>/tailscale-serve.yaml` before friend access is approved.

Monitoring/SRE:

- `monitoring: true` requires a Prometheus blackbox target, Grafana container
  restart alert coverage, and `scripts/check-macmini-monitor-health` coverage.
- Enabled Mac mini `Runtime Services` shown on Homepage should expose
  `GET /health`, declare `http_port` and `health_path`, use Tailnet/live
  validation, and enable monitoring unless they are explicitly documented as
  non-HTTP workers.
- `sre: true` requires a service entry in
  `services/homelab-sre-agent/services.yaml`.
- For NAS-only infrastructure, use the declared service outcome instead of
  forcing Mac mini monitor-health semantics.
- If Prometheus, alerting, monitor-health, or SRE config changed, redeploy or
  force-recreate the relevant service before expecting live checks to pass.

Live proof:

- The health endpoint must respond.
- If the health endpoint returns JSON with a `status` field, strict mode expects
  that field to be `ok`.
- If `status_path` is set, the status response must identify the service.
- For Mac mini monitored services, `scripts/check-macmini-monitor-health` must
  see the blackbox and container metric series.

External dependencies used by validation:

- Container registries: GHCR and Docker Hub, depending on the manifest images.
- Tailnet HTTP endpoints: declared `live_base_url` values.
- Tailscale CLI: dry-run validation for Tailnet Serve config.
- Grafana/Prometheus: monitor-health proof for monitored Mac mini services.

## Test Harness Model

`scripts/test-deploy-tooling` is the blessed command for deploy tooling
regression checks. Keep it as a thin orchestrator over focused subchecks.

`scripts/generate-service-catalog` and `scripts/generate-homepage-config` build
dashboard/catalog artifacts from `ops.yaml`, host manifests, Compose,
monitoring, SRE metadata, and `services/homepage/manual-links.yaml`. Homepage
runtime config is generated during deploy and files under
`services/homepage/config/` should not be committed.
`scripts/generate-caddy-config` builds Caddy runtime config from route
manifests during deploy and `services/caddy/Caddyfile` should not be committed.

Service rollout intake must be manifest-driven. `scripts/tests/check-service-rollout`
discovers `services/*/ops.yaml`, validates each manifest, and uses a generated
`validator-demo` service inside a temporary copied repo for negative cases. Do
not add real service names to this intake path just to test missing fields,
secret mismatches, port collisions, or monitoring omissions.

Some named canaries are still intentional in repo-level deploy tooling tests:

- `portainer`: NAS enabled infra service.
- `plant-monitor`: Mac app service.
- `plant-monitor` on `nasfeo`: disabled migrated service.
- `homelab-monitor`: multi-container service.

Those canaries protect known deploy-tooling shapes rather than service rollout
intake. If a canary changes or is replaced, update its comment and preserve the
invariant it was covering.

## Incremental Rollout

Add manifests in small batches. Start with one proven service, run config and
live validation, then use non-mutating subagent tasks to inspect whether the
output is understandable or overfit before expanding to the next batch.

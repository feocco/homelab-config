---
name: homelab-homepage-dashboard
description: Use when updating Joe Feocco's homelab Homepage dashboard, service cards, dashboard groups, manual links, status dots, or home.feocco.com runtime config.
---

# Homelab Homepage Dashboard

## Core Rule

Homepage is a generated view over the homelab source of truth. Do not create a
parallel catalog and do not hand-edit generated files under
`services/homepage/config/`.

## Sources

- Service cards come from flat `dashboard_*` fields in `services/*/ops.yaml`.
- External links, SSH/VNC protocol links, and cloud/admin links belong in
  `services/homepage/manual-links.yaml`.
- The generator is `scripts/generate-homepage-config`; inspect output in a temp
  directory.
- Groups currently include `Daily Ops`, `Infrastructure`, `Sources of Truth`,
  `Remote Access`, `Runtime Services`, `Monitoring & Cost`,
  `Cloud & External`, and `Disabled / Legacy`.

## Runtime Service Cards

Enabled Mac mini `Runtime Services` should expose `GET /health`, declare
`http_port`, `port_env`, `health_path`, `live_base_url`, `tailnet: true`, and
`monitoring: true`. Homepage status dots are generated from
`host.docker.internal:<http_port><health_path>`.

Use `route_exempt_reason` for backend health endpoints that should not become
LAN HTTPS route candidates. Manual links such as `ssh://`, `vnc://`, UniFi,
cloud consoles, and GitHub docs should not get `siteMonitor`.

## Validation

Run the narrow checks first:

```bash
LC_ALL=C ./scripts/tests/check-homepage-catalog
LC_ALL=C ./scripts/validate-service-rollout --service homepage --host macmini --check config --mode strict
```

For deployed changes, force-recreate `homepage` if generated config changes
need to reload, then verify `https://home.feocco.com/api/services`.

# Homelab Docs

This site is the high-context navigation layer for the homelab. It does not
replace `homelab-config/main` as the deploy source of truth, and it does not
create a new service catalog.

Use it when you need to understand what exists, where the current source of
truth lives, and which gaps are intentional.

## Start Here

- [Overview](docs/overview.md) gives the operating model.
- [Source Of Truth](docs/source-of-truth.md) maps current truth by engineering domain.
- [Services](services/index.md) is generated from the existing service catalog
  with one wrapper page per running service.
- [Service API Conventions](docs/service-api-conventions.md) explains `/docs`,
  `/openapi.json`, and current framework divergence.
- [Service Docs Migration](docs/service-docs-migration.md) gives agents the
  staged validator and task flow for migrating one service.
- [Docs Site](docs/docs-site.md) explains how this site is generated, previewed,
  validated, and hosted.
- [How To Navigate](docs/how-to-navigate.md) explains how Homepage, Grafana, GitHub,
  and this docs site fit together.

## Operating Principles

- Keep durable intent in git.
- Treat generated pages as views, not new truth.
- Keep Homepage as the fast launchpad.
- Keep Grafana and Prometheus as monitoring evidence.
- Keep the NAS sentinel as the out-of-band Mac outage alarm.
- Prefer small docs that point to the right owner over duplicated explanations.

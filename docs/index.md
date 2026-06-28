# Homelab Docs

This site is the high-context navigation layer for the homelab. It does not
replace `homelab-config/main` as the deploy source of truth, and it does not
create a new service catalog.

Use it when you need to understand what exists, where the current source of
truth lives, and which gaps are intentional.

## Start Here

- [Overview](overview.md) gives the operating model.
- [Source Of Truth](source-of-truth.md) maps current truth by engineering domain.
- [Service Index](generated/service-index.md) is generated from the existing
  service catalog.
- [How To Navigate](how-to-navigate.md) explains how Homepage, Grafana, GitHub,
  and this docs site fit together.

## Operating Principles

- Keep durable intent in git.
- Treat generated pages as views, not new truth.
- Keep Homepage as the fast launchpad.
- Keep Grafana and Prometheus as monitoring truth.
- Prefer small docs that point to the right owner over duplicated explanations.

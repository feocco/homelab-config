# How To Navigate The Homelab

Use each surface for a different job.

## Homepage

Homepage is the operational launchpad at `https://home.feocco.com`.

Use it to open apps, dashboards, infrastructure consoles, remote-access links,
and source-of-truth entrypoints.

## Homelab Docs

Homelab Docs is the reading and discovery layer.

Use it to understand domains, service ownership, deployment workflows, route
models, monitoring boundaries, and known gaps.

## Grafana And Prometheus

Grafana and Prometheus are the observability evidence source of truth.

Homepage status dots are quick UI hints. Use Grafana and Prometheus when you
need monitoring evidence.

## Outage Alerts

`homelab-smoke-signal` is the NAS-side backup alarm for broad Mac mini outages.
It sends direct Home Assistant phone alerts when the Mac stack is down enough
that Grafana may not be able to alert.

## GitHub

GitHub holds source and deploy history (this repo is a read-only showcase; PRs are disabled).

Use `homelab-config/main` for durable runtime intent. Treat branch deploys,
local runtime files, and provider consoles as evidence until they are reconciled
back into git.

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

Grafana and Prometheus are the observability source of truth.

Homepage status dots are quick UI hints. Use Grafana and Prometheus when you
need monitoring evidence.

## GitHub

GitHub holds source, deploy history, and pull-request context.

Use `homelab-config/main` for durable runtime intent. Treat branch deploys,
local runtime files, and provider consoles as evidence until they are reconciled
back into git.

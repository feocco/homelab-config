# Gaps And Roadmap

This page keeps the first documentation website honest about what it does not
model yet.

## V1

- Publish a small static documentation site from `homelab-config`.
- Generate a service index from the existing service catalog.
- Link the docs site from Homepage.
- Keep generated docs output out of git.

## V2 Candidates

- Add richer generated domain pages for networking, observability, and
  infrastructure.
- Document point-to-point service dependencies without moving app-owned API docs
  out of their repos.
- Add API and event-domain stubs that point to the owning app repos.
- Add drift and reconciliation reports for runtime state versus git intent.
- Revisit a Backstage-style developer portal only if ownership, templates, and
  plugin-style integrations become the bottleneck.

## Known Gaps

- Data and API domains are mostly app-local.
- Device-level network inventory is not centrally modeled here.
- Secret values, rotation state, and external secret-manager inventory are not
  modeled in this repo.
- Runtime evidence can drift from source until reconciled.

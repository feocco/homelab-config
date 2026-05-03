# Temporal

This service runs the official `temporalio/temporal:latest` image as a local
Temporal dev server for homelab workflows.

- Temporal UI: http://nasfeo:8233
- Temporal gRPC endpoint: `nasfeo:7233`
- Default namespace: `homelab`
- SQLite database: `data/temporal.db`

The `data/` directory is persisted on the NAS and intentionally ignored except
for `.gitkeep`.

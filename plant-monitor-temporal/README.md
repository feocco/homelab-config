# plant-monitor-temporal

Parallel Temporal rewrite of `plant-monitor`.

This service runs the same plant configuration as the current monitor, but uses:

- `plant temporal-run`
- `ghcr.io/feocco/plant-monitor:temporal`
- Temporal namespace `homelab`
- Temporal task queue `plant-monitor-temporal`

The existing `plant-monitor` service remains deployed as the rollback path while
this service sends clearly labeled `[Temporal]` notifications.

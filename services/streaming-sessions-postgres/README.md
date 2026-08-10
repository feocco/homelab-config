# Streaming Sessions Postgres

Postgres projection database for the Streaming Sessions pilot.

- Image: `postgres:18.4`
- Host bind: `127.0.0.1:15432`
- Database: `streaming_sessions`

This database stores rebuildable query projections from Kafka snapshots.

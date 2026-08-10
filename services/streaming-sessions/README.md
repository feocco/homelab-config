# Streaming Sessions

Private Codex session snapshot search service.

- LAN HTTPS URL: `https://streaming-sessions.home.feocco.com`
- Local API port: `127.0.0.1:8110`
- Source repo: `feocco/streaming-sessions`
- Image: `ghcr.io/feocco/streaming-sessions:latest`

The service runs API, collector, and materializer containers. The collector
mounts `/Users/maclab/.codex` read-only and publishes compacted session snapshot
JSON records to Kafka. The materializer projects snapshots into Postgres for the
API and CLI.

Secrets:

- `STREAMING_SESSIONS_API_TOKEN`
- `DATABASE_URL`

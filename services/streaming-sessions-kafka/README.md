# Streaming Sessions Kafka

Single-broker Kafka KRaft service for the Streaming Sessions pilot.

- Image: `apache/kafka:4.2.1`
- Host bind: `127.0.0.1:19092`
- Default topic partitions: `32`
- Snapshot message cap: `20 MiB`
- Replication factor: `1`

This service is intentionally localhost-bound on `macmini`. App containers use
`host.docker.internal:19092`.

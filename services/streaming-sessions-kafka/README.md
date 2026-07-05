# Streaming Sessions Kafka

Single-broker Kafka KRaft service for the Streaming Sessions pilot.

- Image: `apache/kafka:4.2.1`
- Host bind: `127.0.0.1:19092`
- Default topic partitions: `32`
- Snapshot message cap: `20 MiB`
- Replication factor: `1`
- JVM heap: `512 MiB` fixed with `KAFKA_HEAP_OPTS=-Xms512m -Xmx512m`
- Container memory envelope: `1536 MiB` with matching memory+swap limit
- JMX exporter: `127.0.0.1:19104`

This service is intentionally localhost-bound on `macmini`. App containers use
`host.docker.internal:19092`.

Prometheus scrapes the JMX exporter through `host.docker.internal:19104` from
`homelab-monitor`. Grafana includes Kafka JVM GC time and heap panels, plus an
alert when Kafka spends more than 10 percent of wall time in GC for 10 minutes.

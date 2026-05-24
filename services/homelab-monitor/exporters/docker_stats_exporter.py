#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import http.client
import json
import os
import socket
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


@dataclass
class ExporterState:
    lock: threading.RLock = field(default_factory=threading.RLock)
    last_attempt: float = 0.0
    last_success: float = 0.0
    next_refresh: float = 0.0
    success: bool = False
    error_reason: str = "not_collected"
    containers: list[dict[str, Any]] = field(default_factory=list)


STATE = ExporterState()


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str, timeout: int) -> None:
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.socket_path)
        self.sock = sock


def env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return int(value)


def docker_socket_path() -> str:
    docker_host = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    if docker_host.startswith("unix://"):
        return docker_host.removeprefix("unix://")
    return "/var/run/docker.sock"


def docker_json(path: str, timeout_seconds: int) -> Any:
    conn = UnixHTTPConnection(docker_socket_path(), timeout_seconds)
    conn.request("GET", path, headers={"Host": "docker"})
    response = conn.getresponse()
    payload = response.read()
    conn.close()
    if response.status >= 400:
        raise RuntimeError(f"docker_http_{response.status}")
    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def parse_docker_timestamp(value: str | None) -> float:
    if not value or value.startswith("0001-"):
        return 0.0
    clean = value.rstrip("Z")
    if "." in clean:
        head, fraction = clean.split(".", 1)
        clean = f"{head}.{fraction[:6].ljust(6, '0')}"
    clean = f"{clean}+00:00"
    try:
        return dt.datetime.fromisoformat(clean).timestamp()
    except ValueError:
        return 0.0


def container_name(container: dict[str, Any]) -> str:
    names = container.get("Names") or []
    if names:
        return str(names[0]).lstrip("/") or container["Id"][:12]
    return str(container.get("Id", ""))[:12]


def cpu_percent(stats: dict[str, Any]) -> float:
    cpu_stats = stats.get("cpu_stats") or {}
    pre_stats = stats.get("precpu_stats") or {}
    cpu_usage = cpu_stats.get("cpu_usage") or {}
    pre_usage = pre_stats.get("cpu_usage") or {}

    cpu_delta = float(cpu_usage.get("total_usage") or 0) - float(pre_usage.get("total_usage") or 0)
    system_delta = float(cpu_stats.get("system_cpu_usage") or 0) - float(pre_stats.get("system_cpu_usage") or 0)
    online_cpus = float(cpu_stats.get("online_cpus") or len(cpu_usage.get("percpu_usage") or []) or 1)
    if cpu_delta <= 0 or system_delta <= 0:
        return 0.0
    return (cpu_delta / system_delta) * online_cpus * 100.0


def collect_container(container: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    container_id = str(container.get("Id"))
    name = container_name(container)
    encoded_id = urllib.parse.quote(container_id, safe="")
    inspect = docker_json(f"/containers/{encoded_id}/json", timeout_seconds)
    state = inspect.get("State") or {}

    metrics: dict[str, Any] = {
        "id": container_id[:12],
        "name": name,
        "image": str(container.get("Image") or ""),
        "status": str(container.get("Status") or ""),
        "state": str(container.get("State") or ""),
        "running": 1 if state.get("Running") else 0,
        "restart_count": int(inspect.get("RestartCount") or 0),
        "started_at": parse_docker_timestamp(state.get("StartedAt")),
        "oom_killed": 1 if state.get("OOMKilled") else 0,
        "cpu_percent": 0.0,
        "memory_usage_bytes": 0,
        "memory_limit_bytes": 0,
    }

    if metrics["running"]:
        stats = docker_json(f"/containers/{encoded_id}/stats?stream=false&one-shot=true", timeout_seconds)
        memory = stats.get("memory_stats") or {}
        metrics["cpu_percent"] = cpu_percent(stats)
        metrics["memory_usage_bytes"] = int(memory.get("usage") or 0)
        metrics["memory_limit_bytes"] = int(memory.get("limit") or 0)

    return metrics


def collect(timeout_seconds: int) -> list[dict[str, Any]]:
    containers = docker_json("/containers/json?all=1", timeout_seconds)
    return [collect_container(container, timeout_seconds) for container in containers]


def refresh_if_needed(force: bool = False) -> None:
    now_ts = time.time()
    ttl = env_int("DOCKER_STATS_EXPORTER_CACHE_TTL_SECONDS", 15)
    with STATE.lock:
        if not force and now_ts < STATE.next_refresh:
            return
        STATE.last_attempt = now_ts
        STATE.next_refresh = now_ts + ttl

    try:
        containers = collect(env_int("DOCKER_STATS_EXPORTER_REQUEST_TIMEOUT_SECONDS", 10))
        with STATE.lock:
            STATE.containers = containers
            STATE.success = True
            STATE.error_reason = ""
            STATE.last_success = time.time()
    except Exception as exc:  # noqa: BLE001 - exporter must degrade to metrics.
        with STATE.lock:
            STATE.success = False
            STATE.error_reason = exc.__class__.__name__
        print(f"Docker stats collection failed: {exc}", flush=True)


def prom_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def metric_line(name: str, value: float | int, labels: dict[str, str] | None = None) -> str:
    label_text = ""
    if labels:
        label_text = "{" + ",".join(f'{key}="{prom_escape(str(val))}"' for key, val in labels.items()) + "}"
    return f"{name}{label_text} {float(value)}"


def render_metrics() -> bytes:
    refresh_if_needed()
    with STATE.lock:
        success = STATE.success
        last_attempt = STATE.last_attempt
        last_success = STATE.last_success
        error_reason = STATE.error_reason or "none"
        containers = list(STATE.containers)

    now_ts = time.time()
    lines = [
        "# HELP homelab_docker_exporter_up Whether the last Docker stats collection succeeded.",
        "# TYPE homelab_docker_exporter_up gauge",
        metric_line("homelab_docker_exporter_up", 1 if success else 0),
        "# HELP homelab_docker_exporter_last_attempt_timestamp_seconds Unix timestamp of the last collection attempt.",
        "# TYPE homelab_docker_exporter_last_attempt_timestamp_seconds gauge",
        metric_line("homelab_docker_exporter_last_attempt_timestamp_seconds", last_attempt),
        "# HELP homelab_docker_exporter_last_success_timestamp_seconds Unix timestamp of the last successful collection.",
        "# TYPE homelab_docker_exporter_last_success_timestamp_seconds gauge",
        metric_line("homelab_docker_exporter_last_success_timestamp_seconds", last_success),
        "# HELP homelab_docker_exporter_cache_age_seconds Seconds since the last successful collection.",
        "# TYPE homelab_docker_exporter_cache_age_seconds gauge",
        metric_line("homelab_docker_exporter_cache_age_seconds", max(now_ts - last_success, 0) if last_success else 0),
        "# HELP homelab_docker_exporter_error_info Last collection error reason, if any.",
        "# TYPE homelab_docker_exporter_error_info gauge",
        metric_line("homelab_docker_exporter_error_info", 0 if success else 1, {"reason": error_reason}),
        "# HELP homelab_docker_container_info Container metadata.",
        "# TYPE homelab_docker_container_info gauge",
        "# HELP homelab_docker_container_running Whether the container is running.",
        "# TYPE homelab_docker_container_running gauge",
        "# HELP homelab_docker_container_cpu_percent Container CPU use as a percent of one CPU.",
        "# TYPE homelab_docker_container_cpu_percent gauge",
        "# HELP homelab_docker_container_memory_usage_bytes Container memory usage in bytes.",
        "# TYPE homelab_docker_container_memory_usage_bytes gauge",
        "# HELP homelab_docker_container_memory_limit_bytes Container memory limit in bytes.",
        "# TYPE homelab_docker_container_memory_limit_bytes gauge",
        "# HELP homelab_docker_container_restarts_total Docker restart count for the container.",
        "# TYPE homelab_docker_container_restarts_total counter",
        "# HELP homelab_docker_container_start_time_seconds Unix timestamp of the container start time.",
        "# TYPE homelab_docker_container_start_time_seconds gauge",
        "# HELP homelab_docker_container_oom_killed Whether Docker reports the container state as OOM-killed.",
        "# TYPE homelab_docker_container_oom_killed gauge",
    ]

    for container in containers:
        labels = {
            "id": str(container["id"]),
            "name": str(container["name"]),
            "image": str(container["image"]),
            "state": str(container["state"]),
        }
        info_labels = dict(labels)
        info_labels["status"] = str(container["status"])
        lines.append(metric_line("homelab_docker_container_info", 1, info_labels))
        lines.append(metric_line("homelab_docker_container_running", container["running"], labels))
        lines.append(metric_line("homelab_docker_container_cpu_percent", container["cpu_percent"], labels))
        lines.append(metric_line("homelab_docker_container_memory_usage_bytes", container["memory_usage_bytes"], labels))
        lines.append(metric_line("homelab_docker_container_memory_limit_bytes", container["memory_limit_bytes"], labels))
        lines.append(metric_line("homelab_docker_container_restarts_total", container["restart_count"], labels))
        lines.append(metric_line("homelab_docker_container_start_time_seconds", container["started_at"], labels))
        lines.append(metric_line("homelab_docker_container_oom_killed", container["oom_killed"], labels))

    return ("\n".join(lines) + "\n").encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib API name.
        if self.path == "/healthz":
            refresh_if_needed()
            with STATE.lock:
                payload = json.dumps({"ok": STATE.success, "error": STATE.error_reason or None}).encode("utf-8")
            status = 200 if STATE.success else 503
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/metrics":
            payload = render_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        if args and len(args) >= 2 and str(args[1]).startswith(("4", "5")):
            print(f"{self.address_string()} - {fmt % args}", flush=True)


def main() -> None:
    port = env_int("DOCKER_STATS_EXPORTER_PORT", 9109)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"docker-stats-exporter listening on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

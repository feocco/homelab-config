from __future__ import annotations

import json
import logging
import os
import pathlib
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("homelab-sentinel")


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name, "")
    if not value:
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name, "")
    if not value:
        return default
    return float(value)


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name, "")
    if not value:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


TARGETS_PATH = pathlib.Path(os.environ.get("TARGETS_PATH", "/app/config/targets.json"))
STATE_PATH = pathlib.Path(os.environ.get("STATE_PATH", "/app/data/state.json"))
CHECK_INTERVAL_SECONDS = env_int("CHECK_INTERVAL_SECONDS", 60)
PENDING_SECONDS = env_int("PENDING_SECONDS", 300)
REPEAT_INTERVAL_SECONDS = env_int("REPEAT_INTERVAL_SECONDS", 28800)
REQUEST_TIMEOUT_SECONDS = env_int("REQUEST_TIMEOUT_SECONDS", 10)
CRITICAL_CANARY_FAILURES = env_int("CRITICAL_CANARY_FAILURES", 3)
RUNTIME_FAILURE_RATIO = env_float("RUNTIME_FAILURE_RATIO", 0.5)
NOTIFICATION_ENABLED = env_bool("NOTIFICATION_ENABLED", True)
NOTIFICATION_DRY_RUN = env_bool("NOTIFICATION_DRY_RUN", False)

SERVICE_HOST = os.environ.get("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = env_int("SERVICE_PORT", 8095)

HA_URL = os.environ.get("HA_URL", "").rstrip("/")
HA_LONG_LIVED_TOKEN = os.environ.get("HA_LONG_LIVED_TOKEN", "")
HA_NOTIFY_JOE_SERVICE = os.environ.get("HA_NOTIFY_JOE_SERVICE", "")

STATE_LOCK = threading.Lock()
CURRENT_STATUS: dict[str, Any] = {
    "ok": False,
    "message": "starting",
    "incident_active": False,
    "last_check": None,
}


def load_json(path: pathlib.Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        LOGGER.warning("Ignoring invalid JSON at %s: %s", path, exc)
        return default


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def check_target(target: dict[str, str]) -> dict[str, Any]:
    started = time.monotonic()
    request = urllib.request.Request(
        target["url"],
        headers={"User-Agent": "homelab-sentinel/1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response.read(1024)
            duration = round(time.monotonic() - started, 3)
            return {
                "name": target["name"],
                "url": target["url"],
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "duration_seconds": duration,
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        duration = round(time.monotonic() - started, 3)
        return {
            "name": target["name"],
            "url": target["url"],
            "ok": False,
            "error": str(exc),
            "duration_seconds": duration,
        }


def outage_reason(config: dict[str, Any], results: dict[str, list[dict[str, Any]]]) -> str:
    critical_failed = [result for result in results["critical_canaries"] if not result["ok"]]
    runtime_failed = [result for result in results["runtime_services"] if not result["ok"]]
    runtime_total = len(results["runtime_services"])
    critical_names = {result["name"] for result in critical_failed}

    if "Grafana" in critical_names or "grafana" in {name.lower() for name in critical_names}:
        return "Grafana is unreachable"

    if len(critical_failed) >= int(config.get("critical_canary_failures", CRITICAL_CANARY_FAILURES)):
        return f"{len(critical_failed)} critical canaries are unreachable"

    if runtime_total and len(runtime_failed) / runtime_total > float(config.get("runtime_failure_ratio", RUNTIME_FAILURE_RATIO)):
        return f"{len(runtime_failed)} of {runtime_total} Mac runtime services are unreachable"

    return ""


def format_failures(results: dict[str, list[dict[str, Any]]]) -> str:
    failed = [
        result["name"]
        for group in ("critical_canaries", "runtime_services")
        for result in results[group]
        if not result["ok"]
    ]
    unique = list(dict.fromkeys(failed))
    if len(unique) <= 8:
        return ", ".join(unique)
    return ", ".join(unique[:8]) + f", and {len(unique) - 8} more"


def notify_home_assistant(title: str, message: str) -> None:
    if not NOTIFICATION_ENABLED:
        LOGGER.info("Notification disabled: %s - %s", title, message)
        return
    if NOTIFICATION_DRY_RUN:
        LOGGER.info("Notification dry run: %s - %s", title, message)
        return
    if not HA_URL or not HA_LONG_LIVED_TOKEN or not HA_NOTIFY_JOE_SERVICE:
        LOGGER.error("Home Assistant notification settings are incomplete")
        return

    service = HA_NOTIFY_JOE_SERVICE
    if service.startswith("notify."):
        service = service.removeprefix("notify.")
    url = f"{HA_URL}/api/services/notify/{service}"
    payload = {
        "title": title,
        "message": message,
        "data": {
            "tag": "homelab-sentinel-mac-outage",
            "group": "homelab-sentinel",
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {HA_LONG_LIVED_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        response.read(1024)
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Home Assistant notify returned HTTP {response.status}")


def update_state(reason: str, results: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    now = int(time.time())
    state = load_json(STATE_PATH, {})
    active_since = state.get("active_since")
    last_notified_at = int(state.get("last_notified_at") or 0)

    if not reason:
        state["active_since"] = None
        state["last_reason"] = ""
        state["last_ok_at"] = now
        write_json(STATE_PATH, state)
        return {"incident_active": False, "notified": False}

    if not active_since:
        active_since = now
        state["active_since"] = active_since

    elapsed = now - int(active_since)
    should_notify = elapsed >= PENDING_SECONDS and now - last_notified_at >= REPEAT_INTERVAL_SECONDS
    if should_notify:
        failures = format_failures(results)
        message = f"{reason}. Failing checks: {failures or 'unknown'}."
        try:
            notify_home_assistant("Homelab Mac mini outage", message)
            state["last_notified_at"] = now
            state["last_notification_error"] = ""
            LOGGER.warning("Sent outage notification: %s", message)
        except Exception as exc:  # noqa: BLE001 - log and keep watcher alive.
            state["last_notification_error"] = str(exc)
            LOGGER.exception("Failed to send outage notification")

    state["last_reason"] = reason
    state["last_failed_targets"] = format_failures(results)
    write_json(STATE_PATH, state)
    return {"incident_active": True, "notified": should_notify}


def run_once() -> dict[str, Any]:
    config = load_json(TARGETS_PATH, {})
    critical = list(config.get("critical_canaries") or [])
    runtime = list(config.get("runtime_services") or [])
    if not critical:
        raise RuntimeError(f"No critical canaries configured in {TARGETS_PATH}")

    results = {
        "critical_canaries": [check_target(target) for target in critical],
        "runtime_services": [check_target(target) for target in runtime],
    }
    reason = outage_reason(config, results)
    state_result = update_state(reason, results)
    status = {
        "ok": not bool(reason),
        "message": reason or "ok",
        "incident_active": state_result["incident_active"],
        "last_check": int(time.time()),
        "failed_targets": format_failures(results),
    }
    with STATE_LOCK:
        CURRENT_STATUS.update(status)
    return status


def watcher_loop() -> None:
    while True:
        try:
            status = run_once()
            LOGGER.info("Check complete: %s", status["message"])
        except Exception as exc:  # noqa: BLE001 - log and keep watcher alive.
            LOGGER.exception("Sentinel check failed")
            with STATE_LOCK:
                CURRENT_STATUS.update(
                    {
                        "ok": False,
                        "message": str(exc),
                        "incident_active": False,
                        "last_check": int(time.time()),
                    }
                )
        time.sleep(CHECK_INTERVAL_SECONDS)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404)
            return
        with STATE_LOCK:
            payload = dict(CURRENT_STATUS)
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.debug(fmt, *args)


def main() -> None:
    thread = threading.Thread(target=watcher_loop, daemon=True)
    thread.start()
    server = ThreadingHTTPServer((SERVICE_HOST, SERVICE_PORT), HealthHandler)
    LOGGER.info("Serving health endpoint on %s:%s", SERVICE_HOST, SERVICE_PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()

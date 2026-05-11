#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


API_BASE = "https://api.openai.com/v1"


@dataclass
class ExporterState:
    lock: threading.RLock = field(default_factory=threading.RLock)
    last_attempt: float = 0.0
    last_success: float = 0.0
    next_refresh: float = 0.0
    success: bool = False
    error_reason: str = "not_collected"
    metrics: dict[str, Any] = field(default_factory=dict)


STATE = ExporterState()


def env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return int(value)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def start_of_day(day: dt.date) -> dt.datetime:
    return dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)


def unix_seconds(value: dt.datetime) -> int:
    return int(value.timestamp())


def parse_group_by(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def request_json(path: str, params: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_ADMIN_KEY", "").strip()
    if not api_key:
        raise RuntimeError("missing_admin_key")

    query = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(f"{API_BASE}{path}?{query}")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    org_id = os.getenv("OPENAI_ORG_ID", "").strip()
    if org_id:
        req.add_header("OpenAI-Organization", org_id)

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"openai_http_{exc.code}: {body}") from exc


def fetch_paginated(path: str, params: dict[str, Any], timeout_seconds: int) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = []
    page: str | None = None

    while True:
        page_params = dict(params)
        if page:
            page_params["page"] = page
        payload = request_json(path, page_params, timeout_seconds)
        data.extend(payload.get("data", []))
        if not payload.get("has_more"):
            return data
        page = payload.get("next_page")
        if not page:
            return data


def result_amount_usd(result: dict[str, Any]) -> Decimal:
    amount = result.get("amount")
    if isinstance(amount, dict):
        return Decimal(str(amount.get("value") or 0))
    if amount is not None:
        return Decimal(str(amount))
    return Decimal("0")


def collect_costs(now: dt.datetime, lookback_days: int, timeout_seconds: int) -> dict[str, Any]:
    today = now.date()
    start_date = today - dt.timedelta(days=max(lookback_days - 1, 0))
    start = start_of_day(start_date)
    end = now

    params: dict[str, Any] = {
        "start_time": unix_seconds(start),
        "end_time": unix_seconds(end),
        "bucket_width": "1d",
        "limit": min(max(lookback_days, 1), 180),
    }
    group_by = parse_group_by(os.getenv("OPENAI_COST_GROUP_BY", "project_id,line_item"))
    if group_by:
        params["group_by"] = group_by

    buckets = fetch_paginated("/organization/costs", params, timeout_seconds)

    daily: dict[str, Decimal] = {}
    line_items: dict[tuple[str, str, str], Decimal] = {}
    month_to_date = Decimal("0")
    last_30d = Decimal("0")
    last_7d = Decimal("0")
    today_total = Decimal("0")
    yesterday_total = Decimal("0")
    currency = "usd"

    month_start = today.replace(day=1)
    last_7d_start = today - dt.timedelta(days=6)
    yesterday = today - dt.timedelta(days=1)

    for bucket in buckets:
        bucket_start = dt.datetime.fromtimestamp(int(bucket["start_time"]), tz=dt.timezone.utc).date()
        date_label = bucket_start.isoformat()
        bucket_total = Decimal("0")
        results = bucket.get("results", [])

        # Older examples used bucket-level amount or line_items; keep this parser tolerant.
        if not results and "amount" in bucket:
            results = [bucket]
        if not results and "line_items" in bucket:
            results = bucket.get("line_items", [])

        for result in results:
            amount = result_amount_usd(result)
            amount_obj = result.get("amount")
            if isinstance(amount_obj, dict) and amount_obj.get("currency"):
                currency = str(amount_obj["currency"]).lower()

            project_id = str(result.get("project_id") or "unattributed")
            line_item = str(result.get("line_item") or "total")
            line_items[(project_id, line_item, currency)] = line_items.get((project_id, line_item, currency), Decimal("0")) + amount
            bucket_total += amount

        daily[date_label] = daily.get(date_label, Decimal("0")) + bucket_total
        last_30d += bucket_total
        if bucket_start >= month_start:
            month_to_date += bucket_total
        if bucket_start >= last_7d_start:
            last_7d += bucket_total
        if bucket_start == today:
            today_total += bucket_total
        if bucket_start == yesterday:
            yesterday_total += bucket_total

    return {
        "currency": currency,
        "daily": daily,
        "line_items": line_items,
        "windows": {
            "today": today_total,
            "yesterday": yesterday_total,
            "last_7d": last_7d,
            "last_30d": last_30d,
            "month_to_date": month_to_date,
        },
    }


def collect_completions_usage(now: dt.datetime, lookback_days: int, timeout_seconds: int) -> dict[tuple[str, str], dict[str, Decimal]]:
    if os.getenv("OPENAI_USAGE_COMPLETIONS_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        return {}

    today = now.date()
    start = start_of_day(today - dt.timedelta(days=max(lookback_days - 1, 0)))
    params: dict[str, Any] = {
        "start_time": unix_seconds(start),
        "end_time": unix_seconds(now),
        "bucket_width": "1d",
        "limit": min(max(lookback_days, 1), 31),
        "group_by": ["model", "project_id"],
    }
    buckets = fetch_paginated("/organization/usage/completions", params, timeout_seconds)

    usage: dict[tuple[str, str], dict[str, Decimal]] = {}
    for bucket in buckets:
        for result in bucket.get("results", []):
            model = str(result.get("model") or "unknown")
            project_id = str(result.get("project_id") or "unattributed")
            key = (model, project_id)
            values = usage.setdefault(
                key,
                {
                    "input_tokens": Decimal("0"),
                    "output_tokens": Decimal("0"),
                    "cached_input_tokens": Decimal("0"),
                    "requests": Decimal("0"),
                },
            )
            values["input_tokens"] += Decimal(str(result.get("input_tokens") or 0))
            values["output_tokens"] += Decimal(str(result.get("output_tokens") or 0))
            values["cached_input_tokens"] += Decimal(str(result.get("input_cached_tokens") or 0))
            values["requests"] += Decimal(str(result.get("num_model_requests") or 0))
    return usage


def refresh_if_needed(force: bool = False) -> None:
    now_ts = time.time()
    ttl = env_int("OPENAI_COST_CACHE_TTL_SECONDS", 3600)
    with STATE.lock:
        if not force and now_ts < STATE.next_refresh:
            return
        STATE.last_attempt = now_ts
        STATE.next_refresh = now_ts + ttl

    try:
        now = utc_now()
        lookback_days = env_int("OPENAI_COST_LOOKBACK_DAYS", 30)
        timeout_seconds = env_int("OPENAI_COST_REQUEST_TIMEOUT_SECONDS", 20)
        costs = collect_costs(now, lookback_days, timeout_seconds)
        usage = collect_completions_usage(now, min(lookback_days, 31), timeout_seconds)
        with STATE.lock:
            STATE.metrics = {"costs": costs, "usage": usage}
            STATE.success = True
            STATE.error_reason = ""
            STATE.last_success = time.time()
    except Exception as exc:  # noqa: BLE001 - exporter must degrade to metrics.
        with STATE.lock:
            STATE.success = False
            STATE.error_reason = str(exc).splitlines()[0][:180] or exc.__class__.__name__
        print("OpenAI cost collection failed:", STATE.error_reason, flush=True)
        traceback.print_exc()


def prom_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def metric_line(name: str, value: Decimal | float | int, labels: dict[str, str] | None = None) -> str:
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
        metrics = dict(STATE.metrics)

    now_ts = time.time()
    lines = [
        "# HELP openai_cost_exporter_up Whether the last OpenAI cost collection succeeded.",
        "# TYPE openai_cost_exporter_up gauge",
        metric_line("openai_cost_exporter_up", 1 if success else 0),
        "# HELP openai_cost_exporter_last_attempt_timestamp_seconds Unix timestamp of the last collection attempt.",
        "# TYPE openai_cost_exporter_last_attempt_timestamp_seconds gauge",
        metric_line("openai_cost_exporter_last_attempt_timestamp_seconds", last_attempt),
        "# HELP openai_cost_exporter_last_success_timestamp_seconds Unix timestamp of the last successful collection.",
        "# TYPE openai_cost_exporter_last_success_timestamp_seconds gauge",
        metric_line("openai_cost_exporter_last_success_timestamp_seconds", last_success),
        "# HELP openai_cost_exporter_cache_age_seconds Seconds since the last successful collection.",
        "# TYPE openai_cost_exporter_cache_age_seconds gauge",
        metric_line("openai_cost_exporter_cache_age_seconds", max(now_ts - last_success, 0) if last_success else 0),
        "# HELP openai_cost_exporter_error_info Last collection error reason, if any.",
        "# TYPE openai_cost_exporter_error_info gauge",
        metric_line("openai_cost_exporter_error_info", 0 if success else 1, {"reason": error_reason}),
        "# HELP openai_cost_usd OpenAI API cost in USD for common rolling windows.",
        "# TYPE openai_cost_usd gauge",
    ]

    costs = metrics.get("costs") or {}
    currency = str(costs.get("currency") or "usd")
    windows = costs.get("windows") or {}
    for window in ("today", "yesterday", "last_7d", "last_30d", "month_to_date"):
        lines.append(metric_line("openai_cost_usd", windows.get(window, Decimal("0")), {"window": window, "currency": currency}))

    lines.extend(
        [
            "# HELP openai_cost_daily_usd OpenAI API cost by UTC day.",
            "# TYPE openai_cost_daily_usd gauge",
        ]
    )
    for date_label, amount in sorted((costs.get("daily") or {}).items()):
        lines.append(metric_line("openai_cost_daily_usd", amount, {"date": date_label, "currency": currency}))

    lines.extend(
        [
            "# HELP openai_cost_line_item_usd OpenAI API cost by project and line item over the configured lookback window.",
            "# TYPE openai_cost_line_item_usd gauge",
        ]
    )
    for (project_id, line_item, item_currency), amount in sorted((costs.get("line_items") or {}).items()):
        lines.append(
            metric_line(
                "openai_cost_line_item_usd",
                amount,
                {"window": "last_30d", "project_id": project_id, "line_item": line_item, "currency": item_currency},
            )
        )

    lines.extend(
        [
            "# HELP openai_usage_completions_requests OpenAI completions usage request count over the configured lookback window.",
            "# TYPE openai_usage_completions_requests gauge",
            "# HELP openai_usage_completions_input_tokens OpenAI completions input tokens over the configured lookback window.",
            "# TYPE openai_usage_completions_input_tokens gauge",
            "# HELP openai_usage_completions_cached_input_tokens OpenAI completions cached input tokens over the configured lookback window.",
            "# TYPE openai_usage_completions_cached_input_tokens gauge",
            "# HELP openai_usage_completions_output_tokens OpenAI completions output tokens over the configured lookback window.",
            "# TYPE openai_usage_completions_output_tokens gauge",
        ]
    )
    for (model, project_id), values in sorted((metrics.get("usage") or {}).items()):
        labels = {"window": "last_30d", "model": model, "project_id": project_id}
        lines.append(metric_line("openai_usage_completions_requests", values["requests"], labels))
        lines.append(metric_line("openai_usage_completions_input_tokens", values["input_tokens"], labels))
        lines.append(metric_line("openai_usage_completions_cached_input_tokens", values["cached_input_tokens"], labels))
        lines.append(metric_line("openai_usage_completions_output_tokens", values["output_tokens"], labels))

    return ("\n".join(lines) + "\n").encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib API name.
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
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
        print(f"{self.address_string()} - {fmt % args}", flush=True)


def main() -> None:
    port = env_int("OPENAI_COST_EXPORTER_PORT", 9108)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"openai-cost-exporter listening on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tailnet client probe: check homelab sites the way Joe's phone reaches them.

Every PROBE_INTERVAL_SECONDS, for each target hostname:
1. Resolve it with this host's resolver (on nasfeo that is Tailscale MagicDNS,
   the same path a Tailscale-on phone at home uses).
2. Fail if any answer is outside the tailnet range. A LAN answer such as
   192.168.1.43 is what Android 17 Chrome cannot reach without the Local
   network permission (it loops into ERR_TOO_MANY_RETRIES).
3. Open HTTPS to each answer with SNI, verify the certificate, and fail on a
   connect/TLS error or an HTTP status >= 500.

After FAILURES_BEFORE_ALERT consecutive failing runs it notifies Joe through
homelab-functions, and sends an all-clear on the first passing run after that.
"""

from __future__ import annotations

import dataclasses
import http.client
import ipaddress
import json
import logging
import os
import pathlib
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Callable

TAILNET_NETWORKS = (ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48"))
log = logging.getLogger("tailnet-client-probe")


@dataclasses.dataclass(frozen=True)
class Result:
    hostname: str
    ok: bool
    detail: str


@dataclasses.dataclass
class State:
    consecutive_failures: int = 0
    alerted: bool = False

    @classmethod
    def load(cls, path: pathlib.Path) -> "State":
        try:
            return cls(**json.loads(path.read_text()))
        except (FileNotFoundError, ValueError, TypeError):
            return cls()

    def save(self, path: pathlib.Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(dataclasses.asdict(self)))
        tmp.replace(path)


Resolver = Callable[[str], list[str]]
Fetcher = Callable[[str, str, float], int]
Notifier = Callable[[str, str], bool]


def system_resolve(hostname: str) -> list[str]:
    infos = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


def https_status(hostname: str, address: str, timeout: float) -> int:
    context = ssl.create_default_context()
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as raw:
        raw.settimeout(timeout)
        raw.connect((address, 443))
        with context.wrap_socket(raw, server_hostname=hostname) as tls:
            tls.sendall(
                f"GET / HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: tailnet-client-probe\r\n"
                "Connection: close\r\n\r\n".encode()
            )
            response = http.client.HTTPResponse(tls)
            response.begin()
            return response.status


def check(hostname: str, resolve: Resolver, fetch: Fetcher, timeout: float) -> Result:
    try:
        addresses = resolve(hostname)
    except OSError as exc:
        return Result(hostname, False, f"DNS failed: {exc}")
    if not addresses:
        return Result(hostname, False, "DNS returned no addresses")
    local = [a for a in addresses if not any(ipaddress.ip_address(a) in net for net in TAILNET_NETWORKS)]
    if local:
        return Result(hostname, False, f"resolves to non-tailnet {', '.join(local)}; Android 17 Chrome cannot reach LAN addresses")
    for address in addresses:
        try:
            status = fetch(hostname, address, timeout)
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            return Result(hostname, False, f"HTTPS to {address} failed: {exc.__class__.__name__}: {exc}")
        if status >= 500:
            return Result(hostname, False, f"HTTPS to {address} returned {status}")
    return Result(hostname, True, f"{', '.join(addresses)} ok")


def homelab_functions_notifier(base_url: str, token: str, timeout: float) -> Notifier:
    def notify(title: str, message: str) -> bool:
        body = json.dumps({"title": title, "message": message, "tag": "tailnet-client-probe", "group": "homelab"})
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/v1/notify/joe",
            data=body.encode(),
            method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, OSError) as exc:
            log.error("notify failed: %s", exc)
            return False

    return notify


def run_once(
    targets: list[str],
    state: State,
    resolve: Resolver,
    fetch: Fetcher,
    notify: Notifier,
    failures_before_alert: int = 2,
    timeout: float = 10.0,
) -> list[Result]:
    results = [check(target, resolve, fetch, timeout) for target in targets]
    failed = [r for r in results if not r.ok]
    for result in results:
        log.log(logging.INFO if result.ok else logging.WARNING, "%s %s: %s", "ok" if result.ok else "FAIL", result.hostname, result.detail)
    if failed:
        state.consecutive_failures += 1
        if state.consecutive_failures >= failures_before_alert and not state.alerted:
            lines = "\n".join(f"{r.hostname}: {r.detail}" for r in failed)
            state.alerted = notify(
                f"Homelab sites failing for tailnet clients ({len(failed)}/{len(results)})",
                f"Failed {state.consecutive_failures} checks in a row from nasfeo.\n{lines}",
            )
    else:
        if state.alerted:
            state.alerted = not notify("Homelab sites OK for tailnet clients", f"All {len(results)} sites pass again.")
        state.consecutive_failures = 0
    return results


def load_targets(path: pathlib.Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]


def main() -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    targets = load_targets(pathlib.Path(os.environ.get("PROBE_TARGETS_PATH", "/app/targets.txt")))
    state_path = pathlib.Path(os.environ.get("STATE_PATH", "/app/data/state.json"))
    interval = int(os.environ.get("PROBE_INTERVAL_SECONDS", "900"))
    timeout = float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "10"))
    notify = homelab_functions_notifier(os.environ["HOMELAB_FUNCTIONS_URL"], os.environ["HOMELAB_FUNCTIONS_TOKEN"], timeout)
    once = "--once" in sys.argv
    while True:
        state = State.load(state_path)
        run_once(targets, state, system_resolve, https_status, notify, int(os.environ.get("FAILURES_BEFORE_ALERT", "2")), timeout)
        state.save(state_path)
        if once:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())

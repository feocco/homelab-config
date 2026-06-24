#!/usr/bin/env python3
"""Build generated homelab service catalog and Homepage config."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any


def clean_scalar(value: str) -> Any:
    value = value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    value = value.strip('"').strip("'")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    return value


def parse_simple_yaml(path: pathlib.Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list: str | None = None
    if not path.exists():
        return data
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise ValueError(f"List item without list key in {path}: {line}")
            data[current_list].append(clean_scalar(line[4:]))
            continue
        if line.startswith(" "):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$", line)
        if not match:
            continue
        key, value = match.groups()
        if value == "":
            data[key] = []
            current_list = key
        else:
            data[key] = clean_scalar(value or "")
            current_list = None
    return data


def parse_manual_links(path: pathlib.Path) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    if not path.exists():
        return links
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#") or line == "links:":
            continue
        match = re.match(r"^  - ([A-Za-z_][A-Za-z0-9_]*):\s*(.+)\s*$", line)
        if match:
            current = {match.group(1): str(clean_scalar(match.group(2)))}
            links.append(current)
            continue
        match = re.match(r"^    ([A-Za-z_][A-Za-z0-9_]*):\s*(.+)\s*$", line)
        if match and current is not None:
            current[match.group(1)] = str(clean_scalar(match.group(2)))
    return links


def as_list(mapping: dict[str, Any], single_key: str, list_key: str) -> list[str]:
    values: list[str] = []
    list_value = mapping.get(list_key)
    if isinstance(list_value, list):
        values.extend(str(value) for value in list_value)
    single_value = mapping.get(single_key)
    if single_value not in (None, ""):
        values.append(str(single_value))
    return values


def host_scoped_enabled(mapping: dict[str, Any], key: str, host: str) -> bool:
    if mapping.get(key) is True:
        return True
    if mapping.get(key) is False:
        return False
    values = mapping.get(f"{key}_hosts")
    return isinstance(values, list) and host in [str(value) for value in values]


def host_scoped_value(mapping: dict[str, Any], key: str, host: str) -> str:
    value = mapping.get(f"{key}_{host}")
    if value not in (None, ""):
        return str(value)
    value = mapping.get(key)
    return "" if value in (None, "") else str(value)


def manifest_value(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    return "" if value in (None, "") else str(value)


def dashboard_visible(mapping: dict[str, Any]) -> bool:
    value = mapping.get("dashboard_visible")
    if value is True:
        return True
    if value is False:
        return False
    return bool(mapping.get("dashboard_group"))


def parse_host_services(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    services: dict[str, dict[str, Any]] = {}
    in_services = False
    current: str | None = None
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if line == "services:":
            in_services = True
            continue
        if not in_services:
            continue
        if line and not line.startswith(" "):
            break
        match = re.match(r"^  ([^:\s][^:]*):\s*$", line)
        if match:
            current = match.group(1)
            services[current] = {"path": "", "enabled": True}
            continue
        if current is None:
            continue
        match = re.match(r"^    path:\s*(.+)\s*$", line)
        if match:
            services[current]["path"] = str(clean_scalar(match.group(1)))
            continue
        match = re.match(r"^    enabled:\s*(.+)\s*$", line)
        if match:
            services[current]["enabled"] = clean_scalar(match.group(1)) is not False
            continue
    return services


def parse_compose(path: pathlib.Path) -> dict[str, list[str]]:
    containers: list[str] = []
    images: list[str] = []
    if not path.exists():
        return {"containers": containers, "images": images}
    current = ""
    in_services = False
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if line == "services:":
            in_services = True
            continue
        if not in_services:
            continue
        match = re.match(r"^  ([^:\s][^:]*):\s*$", line)
        if match:
            current = match.group(1)
            containers.append(current)
            continue
        if not current:
            continue
        match = re.match(r"^    image:\s*(.+)\s*$", line)
        if match:
            images.append(str(clean_scalar(match.group(1))))
            continue
        match = re.match(r"^    container_name:\s*(.+)\s*$", line)
        if match:
            containers[-1] = str(clean_scalar(match.group(1)))
    return {
        "containers": sorted(dict.fromkeys(containers)),
        "images": sorted(dict.fromkeys(images)),
    }


def parse_prometheus_services(path: pathlib.Path) -> set[str]:
    services: set[str] = set()
    if not path.exists():
        return services
    for raw in path.read_text().splitlines():
        match = re.match(r"^\s+service:\s*(.+)\s*$", raw.rstrip())
        if match:
            services.add(str(clean_scalar(match.group(1))))
    return services


def parse_sre(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    services: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return services
    in_services = False
    current = ""
    section = ""
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if line == "services:":
            in_services = True
            continue
        if not in_services:
            continue
        match = re.match(r"^  ([^:\s][^:]*):\s*$", line)
        if match:
            current = match.group(1)
            services[current] = {"source_repo": "", "sre_enabled": False}
            section = ""
            continue
        if not current:
            continue
        match = re.match(r"^    ([A-Za-z_]+):\s*$", line)
        if match:
            section = match.group(1)
            continue
        if section == "source":
            match = re.match(r"^      repo:\s*(.+)\s*$", line)
            if match:
                services[current]["source_repo"] = str(clean_scalar(match.group(1)))
                continue
        if section == "sre":
            match = re.match(r"^      enabled:\s*(.+)\s*$", line)
            if match:
                services[current]["sre_enabled"] = clean_scalar(match.group(1)) is True
    return services


def parse_caddy_routes(path: pathlib.Path) -> dict[int, str]:
    routes: dict[int, str] = {}
    if not path.exists():
        return routes
    text = path.read_text()
    for match in re.finditer(r"http://([^ {\n]+)\s*\{(?P<body>.*?)\n\}", text, re.DOTALL):
        host = match.group(1)
        proxy = re.search(r"reverse_proxy\s+host\.docker\.internal:(\d+)", match.group("body"))
        if proxy:
            routes[int(proxy.group(1))] = f"http://{host}/"
    return routes


def service_manifests(base_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for path in sorted((base_dir / "services").glob("*/ops.yaml")):
        manifest = parse_simple_yaml(path)
        service = str(manifest.get("service") or path.parent.name)
        manifests[service] = manifest
    return manifests


def host_names(base_dir: pathlib.Path) -> list[str]:
    return sorted(path.name for path in (base_dir / "hosts").iterdir() if path.is_dir())


def display_name(service: str) -> str:
    fixed = {
        "caddy": "Caddy",
        "dashy": "Dashy",
        "dashy-redirect": "Dashy Redirect",
        "dog-bowl-monitor": "Dog Bowl Monitor",
        "grafana": "Grafana",
        "hass-janitor": "hass-janitor",
        "hello-nas": "Hello NAS",
        "homarr": "Homarr",
        "homelab-functions": "homelab-functions",
        "homelab-log-watcher": "homelab-log-watcher",
        "homelab-monitor": "Homelab Monitor",
        "homelab-sre-agent": "homelab-sre-agent",
        "homepage": "Homepage",
        "instacart-history-service": "Instacart History",
        "laundry-monitor": "Laundry Monitor",
        "mealie": "Mealie",
        "mealie-planner": "Mealie Planner",
        "openai-cost": "OpenAI Cost / Usage",
        "pi-hole": "Pi-hole",
        "plant-monitor": "Plant Monitor",
        "portainer": "Portainer",
    }
    return fixed.get(service, service.replace("-", " ").title())


def build_catalog(base_dir: pathlib.Path) -> dict[str, Any]:
    manifests = service_manifests(base_dir)
    monitored = parse_prometheus_services(base_dir / "services/homelab-monitor/prometheus/prometheus.yml")
    sre = parse_sre(base_dir / "services/homelab-sre-agent/services.yaml")
    caddy_routes = parse_caddy_routes(base_dir / "services/caddy/Caddyfile")
    rows: list[dict[str, Any]] = []

    for host in host_names(base_dir):
        services_file = base_dir / "hosts" / host / "services.yaml"
        if not services_file.exists():
            continue
        for service, entry in parse_host_services(services_file).items():
            path = str(entry.get("path") or f"services/{service}")
            manifest = manifests.get(service, {})
            compose = parse_compose(base_dir / path / "docker-compose.yml")
            images = as_list(manifest, "image", "images") or compose["images"]
            containers = as_list(manifest, "container", "containers") or compose["containers"]
            source_repo = str(manifest.get("source_repo") or sre.get(service, {}).get("source_repo") or "")
            http_port = manifest.get("http_port")
            homepage_url = homepage_url_for(service, host, manifest, caddy_routes)
            monitoring = host_scoped_enabled(manifest, "monitoring", host) or service in monitored
            sre_enabled = host_scoped_enabled(manifest, "sre", host) or bool(sre.get(service, {}).get("sre_enabled"))
            dashboard_url = manifest_value(manifest, "dashboard_url")
            rows.append(
                {
                    "service": service,
                    "name": display_name(service),
                    "dashboard_name": manifest_value(manifest, "dashboard_name") or display_name(service),
                    "dashboard_group": manifest_value(manifest, "dashboard_group"),
                    "dashboard_description": manifest_value(manifest, "dashboard_description"),
                    "dashboard_icon": manifest_value(manifest, "dashboard_icon"),
                    "dashboard_url": dashboard_url,
                    "dashboard_visible": dashboard_visible(manifest),
                    "host": host,
                    "enabled": bool(entry.get("enabled", True)),
                    "path": path,
                    "kind": str(manifest.get("kind") or ""),
                    "source_repo": source_repo,
                    "images": images,
                    "containers": containers,
                    "http_port": http_port,
                    "health_path": str(manifest.get("health_path") or ""),
                    "homepage_url": homepage_url,
                    "route_hostname": manifest_value(manifest, "route_hostname"),
                    "route_https": manifest.get("route_https") is True,
                    "route_dns": manifest_value(manifest, "route_dns"),
                    "route_target_port": manifest.get("route_target_port"),
                    "monitoring": monitoring,
                    "monitored": monitoring,
                    "sre_metadata": service in sre,
                    "sre_enabled": sre_enabled,
                    "tailnet": host_scoped_enabled(manifest, "tailnet", host),
                    "live_base_url": host_scoped_value(manifest, "live_base_url", host),
                }
            )

    rows.sort(key=lambda row: (row["host"], row["service"]))
    return {
        "schema": "homelab-catalog.v1",
        "generated_by": "scripts/generate-service-catalog",
        "services": rows,
    }


def homepage_url_for(service: str, host: str, manifest: dict[str, Any], caddy_routes: dict[int, str]) -> str:
    route_hostname = manifest_value(manifest, "route_hostname")
    if route_hostname:
        scheme = "https" if manifest.get("route_https") is True else "http"
        return f"{scheme}://{route_hostname.rstrip('/')}/"
    if service == "homepage":
        return "http://home.arpa/"
    if service == "homarr":
        return "http://homarr.home.arpa/"
    if service == "dashy":
        return "http://dashy.home.arpa/"
    port = manifest.get("http_port")
    if isinstance(port, int) and port in caddy_routes:
        return caddy_routes[port]
    live = host_scoped_value(manifest, "live_base_url", host)
    if live:
        return live.rstrip("/") + "/"
    return ""


def route_entries(base_dir: pathlib.Path, host: str | None = None) -> list[dict[str, Any]]:
    manifests = service_manifests(base_dir)
    entries: list[dict[str, Any]] = []
    for current_host in host_names(base_dir):
        if host and current_host != host:
            continue
        services_file = base_dir / "hosts" / current_host / "services.yaml"
        if not services_file.exists():
            continue
        for service, entry in parse_host_services(services_file).items():
            if entry.get("enabled") is False:
                continue
            manifest = manifests.get(service, {})
            hostname = manifest_value(manifest, "route_hostname")
            if not hostname:
                continue
            target_port = manifest.get("route_target_port") or manifest.get("http_port")
            entries.append(
                {
                    "service": service,
                    "host": current_host,
                    "hostname": hostname,
                    "target_port": target_port,
                    "https": manifest.get("route_https") is True,
                    "dns": manifest_value(manifest, "route_dns"),
                    "aliases": [str(value) for value in manifest.get("route_aliases", []) if str(value)],
                }
            )
    return sorted(entries, key=lambda row: (str(row["hostname"]), str(row["service"])))


def caddy_config(base_dir: pathlib.Path, host: str | None = None) -> str:
    entries = route_entries(base_dir, host)
    lines = [
        "{",
        "\temail {$CADDY_ACME_EMAIL}",
        "}",
        "",
        "*.{$CADDY_HOME_DOMAIN} {",
        "\ttls {",
        "\t\tdns cloudflare {env.CLOUDFLARE_API_TOKEN}",
        "\t}",
        "\trespond \"No homelab route configured for {host}\" 404",
        "}",
        "",
    ]
    for entry in entries:
        hostname = str(entry["hostname"])
        target_port = entry["target_port"]
        lines.extend(
            [
                f"{hostname} {{",
                "\ttls {",
                "\t\tdns cloudflare {env.CLOUDFLARE_API_TOKEN}",
                "\t}",
                f"\treverse_proxy host.docker.internal:{target_port}",
                "}",
                "",
            ]
        )
        for alias in entry["aliases"]:
            lines.extend(
                [
                    f"http://{alias} {{",
                    f"\tredir https://{hostname}{{uri}} 308",
                    "}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def yaml_scalar(value: Any) -> str:
    text = str(value)
    if text == "":
        return "''"
    if re.fullmatch(r"[A-Za-z0-9_./:@-]+", text):
        return text
    return json.dumps(text)


def homepage_item(name: str, href: str, description: str, icon: str) -> list[str]:
    lines = [f"    - {yaml_scalar(name)}:"]
    lines.append(f"        href: {yaml_scalar(href)}")
    if description:
        lines.append(f"        description: {yaml_scalar(description)}")
    if icon:
        lines.append(f"        icon: {yaml_scalar(icon)}")
    return lines


GROUP_ORDER = [
    "Daily Ops",
    "Infrastructure",
    "Runtime Services",
    "Monitoring & Cost",
    "Cloud & External",
    "Disabled / Legacy",
]


def homepage_services(catalog: dict[str, Any], manual_links: list[dict[str, str]]) -> str:
    rows = catalog["services"]
    grouped: dict[str, list[list[str]]] = {group: [] for group in GROUP_ORDER}
    lines: list[str] = []

    def group(title: str, items: list[list[str]]) -> None:
        if not items:
            return
        lines.append(f"- {title}:")
        for item in items:
            lines.extend(item)
        lines.append("")

    for link in manual_links:
        target_group = link.get("group") or "Cloud & External"
        grouped.setdefault(target_group, [])
        grouped[target_group].append(
            homepage_item(
                link.get("name", ""),
                link.get("href", ""),
                link.get("description", ""),
                link.get("icon", ""),
            )
        )

    seen_services: set[str] = set()
    for row in rows:
        if not row["dashboard_visible"] or row["service"] in seen_services:
            continue
        if not row["enabled"] and row["dashboard_group"] != "Disabled / Legacy":
            continue
        seen_services.add(row["service"])
        href = (
            row["dashboard_url"]
            or row["homepage_url"]
            or row["live_base_url"]
            or (f"https://github.com/{row['source_repo']}" if row["source_repo"] else "")
        )
        if not href:
            continue
        target_group = row["dashboard_group"] or "Runtime Services"
        grouped.setdefault(target_group, [])
        grouped[target_group].append(
            homepage_item(
                row["dashboard_name"],
                href,
                row["dashboard_description"],
                row["dashboard_icon"],
            )
        )

    for title in GROUP_ORDER:
        group(title, grouped.get(title, []))

    return "\n".join(lines).rstrip() + "\n"


def homepage_settings() -> str:
    return """---
title: Homelab
description: Generated from homelab-config
layout:
  Daily Ops:
    style: row
    columns: 4
  Infrastructure:
    style: row
    columns: 5
  Runtime Services:
    style: row
    columns: 4
  Monitoring & Cost:
    style: row
    columns: 3
  Cloud & External:
    style: row
    columns: 5
  Disabled / Legacy:
    style: row
    columns: 3
"""


def homepage_bookmarks() -> str:
    return """---
- Repositories:
    - homelab-config:
        - abbr: HC
          href: https://github.com/feocco/homelab-config
    - Actions:
        - abbr: GA
          href: https://github.com/feocco/homelab-config/actions
"""


def homepage_widgets() -> str:
    return """---
- search:
    provider: duckduckgo
    target: _blank
"""


def write_homepage_config(base_dir: pathlib.Path, output_dir: pathlib.Path) -> None:
    catalog = build_catalog(base_dir)
    manual_links = parse_manual_links(base_dir / "services/homepage/manual-links.yaml")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "service-catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    (output_dir / "settings.yaml").write_text(homepage_settings())
    (output_dir / "services.yaml").write_text(homepage_services(catalog, manual_links))
    (output_dir / "bookmarks.yaml").write_text(homepage_bookmarks())
    (output_dir / "widgets.yaml").write_text(homepage_widgets())


def table_text(rows: list[dict[str, Any]]) -> str:
    columns = [
        "service",
        "host",
        "enabled",
        "path",
        "containers",
        "images",
        "monitored",
        "sre_metadata",
        "sre_enabled",
        "source_repo",
    ]

    def text(value: Any) -> str:
        if isinstance(value, bool):
            return "yes" if value else "no"
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return str(value)

    widths = {
        column: max(len(column), *(len(text(row[column])) for row in rows))
        for column in columns
    }
    lines = [
        "  ".join(column.ljust(widths[column]) for column in columns),
        "  ".join("-" * widths[column] for column in columns),
    ]
    for row in rows:
        lines.append("  ".join(text(row[column]).ljust(widths[column]) for column in columns))
    return "\n".join(lines) + "\n"


def list_rows(catalog: dict[str, Any], host: str) -> list[dict[str, Any]]:
    rows = catalog["services"]
    if host != "all":
        rows = [row for row in rows if row["host"] == host]
    return [
        {
            "service": row["service"],
            "host": row["host"],
            "enabled": row["enabled"],
            "path": row["path"],
            "containers": row["containers"],
            "images": row["images"],
            "monitored": row["monitored"],
            "sre_metadata": row["sre_metadata"],
            "sre_enabled": row["sre_enabled"],
            "source_repo": row["source_repo"],
        }
        for row in rows
    ]


def main_list(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=str(pathlib.Path(__file__).resolve().parents[2]))
    parser.add_argument("--host", choices=["all", "macmini", "nasfeo"], default="all")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    args = parser.parse_args(argv)

    rows = list_rows(build_catalog(pathlib.Path(args.base_dir)), args.host)
    if args.format == "json":
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(table_text(rows), end="")
    return 0


def main_catalog(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=str(pathlib.Path(__file__).resolve().parents[2]))
    parser.add_argument("--format", choices=["json"], default="json")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    base_dir = pathlib.Path(args.base_dir)
    catalog = build_catalog(base_dir)
    payload = json.dumps(catalog, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = pathlib.Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload)
    else:
        print(payload, end="")
    return 0


def main_homepage(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=str(pathlib.Path(__file__).resolve().parents[2]))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    write_homepage_config(pathlib.Path(args.base_dir), pathlib.Path(args.output))
    return 0


def main_caddy(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=str(pathlib.Path(__file__).resolve().parents[2]))
    parser.add_argument("--host", default=None)
    parser.add_argument("--output", default="-")
    args = parser.parse_args(argv)

    payload = caddy_config(pathlib.Path(args.base_dir), args.host)
    if args.output == "-":
        print(payload, end="")
    else:
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
    return 0

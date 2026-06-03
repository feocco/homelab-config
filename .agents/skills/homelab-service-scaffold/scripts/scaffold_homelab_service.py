#!/usr/bin/env python3
"""Scaffold a Python homelab service repo."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "homelab-service"


def package_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not name:
        name = "homelab_service"
    if name[0].isdigit():
        name = f"service_{name}"
    return name


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def render_env(service: str, port: int, home_assistant: bool, openai: bool, stateful: bool) -> str:
    lines = [
        "SERVICE_HOST=0.0.0.0",
        f"SERVICE_PORT={port}",
        "LOG_LEVEL=INFO",
    ]
    if stateful:
        lines.append("DATA_DIR=/app/data")
    if home_assistant:
        lines.extend(
            [
                "HA_URL=https://example.ui.nabu.casa",
                "HA_LONG_LIVED_TOKEN=replace_me",
                "HOMELAB_FUNCTIONS_URL=http://host.docker.internal:8091",
                "HOMELAB_FUNCTIONS_TOKEN=replace_me",
            ]
        )
    if openai:
        lines.extend(["OPENAI_API_KEY=replace_me", "OPENAI_MODEL=gpt-5-mini"])
    return "\n".join(lines)


def render_pyproject(service: str, package: str, home_assistant: bool, openai: bool) -> str:
    deps = ['"python-dotenv>=1.0.0"']
    if home_assistant:
        deps.append('"homelab-functions @ https://github.com/feocco/homelab-functions/archive/refs/heads/main.zip"')
    if openai:
        deps.append('"openai>=1.99.0"')
    dep_block = "\n".join(f"  {dep}," for dep in deps)
    if dep_block:
        dep_block = "\n" + dep_block + "\n"

    return f"""
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{service}"
version = "0.1.0"
description = "Homelab service"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [{dep_block}]

[project.optional-dependencies]
dev = [
  "pytest>=8",
]

[project.scripts]
{service} = "{package}.main:main"

[tool.setuptools.packages.find]
include = ["{package}*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""


def render_config(package: str, service: str, port: int, stateful: bool) -> str:
    data_line = '    data_dir: Path = Path(os.environ.get("DATA_DIR", "/app/data"))' if stateful else ""
    return f"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    service_name: str = "{service}"
    host: str = os.environ.get("SERVICE_HOST", "0.0.0.0")
    port: int = int(os.environ.get("SERVICE_PORT", "{port}"))
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
{data_line}


def load_settings() -> Settings:
    return Settings()
"""


def render_main(package: str, service: str) -> str:
    return f"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import load_settings


def build_health_payload() -> dict[str, str]:
    return {{"service": "{service}", "status": "ok"}}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in ("/health", "/v1/status", "/"):
            self.send_error(404)
            return
        body = json.dumps(build_health_payload()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    settings = load_settings()
    server = ThreadingHTTPServer((settings.host, settings.port), Handler)
    print(f"starting {{settings.service_name}} on port {{settings.port}}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
"""


def render_homelab_yaml(
    service: str,
    package: str,
    port: int,
    home_assistant: bool,
    openai: bool,
    stateful: bool,
) -> str:
    externals = []
    if home_assistant:
        externals.extend(["Home Assistant", "homelab-functions"])
    if openai:
        externals.append("OpenAI API")
    external_block = "\n".join(f"    - {item}" for item in externals) or "    - none"
    persistent_block = "    - data/" if stateful else "    []"
    restore_block = "    - data/**" if stateful else "    []"
    return f"""
service: {service}
image: ghcr.io/feocco/{service}:latest
package: {package}
host: macmini
port: {port}
health:
  url: http://127.0.0.1:{port}/health
checks:
  - python -m pytest -q
  - docker build .
runtime:
  env_example: .env.example
  persistent_paths:
{persistent_block}
  external_dependencies:
{external_block}
risk:
  default: direct
  canary:
    - Dockerfile
  restore:
{restore_block}
"""


def render_readme(service: str, package: str, description: str, port: int, stateful: bool) -> str:
    state_note = "\nPersistent runtime state lives under `data/`.\n" if stateful else ""
    return f"""
# {service}

{description}

## Quickstart

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m {package}.main
```

The service exposes `GET /health` on port `{port}` by default.
{state_note}
## Deployment

This repo publishes `ghcr.io/feocco/{service}:latest` from
`.github/workflows/container.yml`. Runtime deployment is owned by
`homelab-config`; this repo's deploy contract is `homelab.yaml`.
"""


def render_architecture(service: str, description: str) -> str:
    return f"""
# Architecture

`{service}` is a small Python Docker service.

## Boundaries

- Source, tests, Dockerfile, and GHCR publishing live in this app repo.
- Runtime configuration, secrets, Compose files, and host placement live in
  `homelab-config`.
- `homelab.yaml` documents the app-side deploy contract used by agents and
  deploy planning tools.

## Flow

1. The service starts an HTTP health endpoint.
2. The container image is published to GHCR.
3. `homelab-config` pulls the image and supplies runtime configuration.
"""


def render_configuration(service: str, port: int, home_assistant: bool, openai: bool, stateful: bool) -> str:
    rows = [
        ("SERVICE_HOST", "0.0.0.0", "HTTP bind host inside the container."),
        ("SERVICE_PORT", str(port), "HTTP bind port inside the container."),
        ("LOG_LEVEL", "INFO", "Python logging verbosity."),
    ]
    if stateful:
        rows.append(("DATA_DIR", "./data", "Persistent state directory."))
    if home_assistant:
        rows.extend(
            [
                ("HA_URL", "", "Home Assistant base URL."),
                ("HA_LONG_LIVED_TOKEN", "", "Home Assistant long-lived access token."),
                ("HOMELAB_FUNCTIONS_URL", "http://host.docker.internal:8091", "Notification/helper service URL."),
                ("HOMELAB_FUNCTIONS_TOKEN", "", "Notification/helper service token."),
            ]
        )
    if openai:
        rows.append(("OPENAI_API_KEY", "", "OpenAI API key."))

    table = "\n".join(f"| `{name}` | `{default}` | {desc} |" for name, default, desc in rows)
    return f"""
# Configuration

Use `.env.example` for placeholders only. Real values belong in ignored local
`.env` files or private `homelab-config` runtime config.

| Variable | Default | Purpose |
| --- | --- | --- |
{table}
"""


def render_security(home_assistant: bool, openai: bool, stateful: bool) -> str:
    secret_notes = []
    if home_assistant:
        secret_notes.append("- Home Assistant tokens are secrets and must not be committed.")
    if openai:
        secret_notes.append("- OpenAI API keys are secrets and must not be committed.")
    if stateful:
        secret_notes.append("- Runtime data under `data/` is local state and must not be committed.")
    if not secret_notes:
        secret_notes.append("- Keep future credentials in ignored `.env` files or homelab-config secrets.")
    return f"""
# Security

## Trust Boundaries

- App source and generic examples may live in this repo.
- Runtime secrets and host-specific configuration belong outside this repo.
- The container should expose only the configured service port.

## Credentials And State

{chr(10).join(secret_notes)}
"""


def render_dockerfile(package: str, port: int) -> str:
    return f"""
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY {package}/ ./{package}/

RUN python -m pip install --no-cache-dir --upgrade pip \\
    && python -m pip install --no-cache-dir .

EXPOSE {port}

CMD ["python", "-m", "{package}.main"]
"""


def render_workflow(service: str) -> str:
    return f"""
name: Container

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

env:
  IMAGE_NAME: ghcr.io/${{{{ github.repository_owner }}}}/{service}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v4

      - name: Log in to GHCR
        uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Build and push
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: |
            ${{{{ env.IMAGE_NAME }}}}:latest
            ${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}
"""


def render_gitignore(stateful: bool) -> str:
    lines = [
        ".env",
        ".venv/",
        "__pycache__/",
        ".pytest_cache/",
        "*.egg-info/",
        ".DS_Store",
    ]
    if stateful:
        lines.extend(["data/*", "!data/.gitkeep"])
    return "\n".join(lines)


def scaffold(args: argparse.Namespace) -> Path:
    service = slugify(args.name)
    package = package_name(args.package or service)
    description = args.description or f"{service} homelab service."
    output_dir = Path(args.output_dir or Path.cwd() / service).expanduser().resolve()

    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        raise SystemExit(f"{output_dir} exists and is not empty; pass --force to overwrite scaffold files")

    files = {
        "README.md": render_readme(service, package, description, args.port, args.stateful),
        "docs/architecture.md": render_architecture(service, description),
        "docs/configuration.md": render_configuration(service, args.port, args.with_home_assistant, args.with_openai, args.stateful),
        "docs/security.md": render_security(args.with_home_assistant, args.with_openai, args.stateful),
        "homelab.yaml": render_homelab_yaml(service, package, args.port, args.with_home_assistant, args.with_openai, args.stateful),
        ".env.example": render_env(service, args.port, args.with_home_assistant, args.with_openai, args.stateful),
        ".gitignore": render_gitignore(args.stateful),
        ".dockerignore": ".git\n.env\n.venv\n.pytest_cache\n__pycache__\n*.egg-info\ndata\n",
        "pyproject.toml": render_pyproject(service, package, args.with_home_assistant, args.with_openai),
        "Dockerfile": render_dockerfile(package, args.port),
        ".github/workflows/container.yml": render_workflow(service),
        f"{package}/__init__.py": f'"""Package for {service}."""\n',
        f"{package}/config.py": render_config(package, service, args.port, args.stateful),
        f"{package}/main.py": render_main(package, service),
        "tests/test_config.py": f"from {package}.config import load_settings\n\n\ndef test_load_settings_defaults():\n    settings = load_settings()\n    assert settings.service_name == \"{service}\"\n    assert settings.port == {args.port}\n",
        "tests/test_health.py": f"from {package}.main import build_health_payload\n\n\ndef test_health_payload():\n    assert build_health_payload() == {{\"service\": \"{service}\", \"status\": \"ok\"}}\n",
    }

    for relative_path, content in files.items():
        write_file(output_dir / relative_path, content)
    if args.stateful:
        write_file(output_dir / "data/.gitkeep", "")
    return output_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Service/repo name, for example plant-monitor.")
    parser.add_argument("--description", default="", help="Short README description.")
    parser.add_argument("--package", default="", help="Python package name. Defaults to normalized service name.")
    parser.add_argument("--port", type=int, default=8000, help="Default HTTP port.")
    parser.add_argument("--output-dir", "--path", default="", help="Directory to create. Defaults to ./<name>.")
    parser.add_argument("--with-home-assistant", action="store_true", help="Add Home Assistant env/dependency placeholders.")
    parser.add_argument("--with-openai", action="store_true", help="Add OpenAI env/dependency placeholders.")
    parser.add_argument("--stateful", action="store_true", help="Add data/.gitkeep and stateful deploy contract fields.")
    parser.add_argument("--force", action="store_true", help="Overwrite scaffold-managed files in an existing directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_dir = scaffold(args)
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

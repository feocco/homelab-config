---
name: homelab-service-scaffold
description: "Use when Codex needs to scaffold a new Joe Feocco homelab Python service repo with docs, pyproject.toml, Docker, GHCR publishing, homelab.yaml deploy contract, env examples, package files, tests, and optional persistent state."
---

# Homelab Service Scaffold

Use this skill to create a new Python homelab service repo that fits Joe's
current Docker/GHCR/homelab-config workflow.

## Workflow

1. Pick the service name, package name, description, port, and whether it needs
   Home Assistant, OpenAI, or persistent state.
2. Run the bundled generator:

```bash
python3 /Users/feocco/codex-skills/homelab-service-scaffold/scripts/scaffold_homelab_service.py \
  --name my-service \
  --description "Short service description" \
  --output-dir /Users/feocco/code/my-service
```

Useful flags:

- `--package my_service` to override the Python package name.
- `--port 8080` for HTTP services with a non-default port.
- `--with-home-assistant` to include Home Assistant env placeholders and
  `homelab-functions` dependency.
- `--with-openai` to include `OPENAI_API_KEY` placeholder and dependency.
- `--stateful` to add `data/.gitkeep`, state docs, and stateful contract fields.

## After Generation

Validate the generated repo before handing it off:

```bash
cd /Users/feocco/code/my-service
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
docker build .
```

For deployment work, use `$homelab-docker-deploy` after the app repo is ready.
Do not put real secrets in the generated `.env.example`; local values belong in
ignored `.env` files or private `homelab-config` runtime config.

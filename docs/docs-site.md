# Docs Site

The Homelab Docs site is the searchable reading layer for this repository. It
is not a new source of truth and it is not the fast operations launchpad.

Use Homepage when you want to open a tool or check a status dot. Use this docs
site when you need context about what exists, which file owns it, and what work
is still intentionally unfinished.

## Source Model

Durable source-of-truth content stays in the files that already own it:

- `docs/*.md` contains homelab-wide documentation and cross-cutting policies.
- `docs/service-api-conventions.md` owns the app API docs convention:
  `docs_path`, `openapi_path`, and `api_framework`.
- `services/*/ops.yaml`, host manifests, Compose files, monitoring config, and
  SRE metadata feed the generated service catalog.
- Application-specific human docs stay with each app. When a service adopts the
  convention, the central service page embeds the live app-owned `/docs` page
  and links to `/openapi.json` instead of copying narrative documentation here.

Generated files are views over existing truth:

- `docs/generated/service-index.md` and `docs/generated/services/*.md` are
  generated during the docs build.
- `.local/mkdocs-src/` is a temporary MkDocs source tree.
- `.site/` is the rendered static site.

Those paths are ignored and should not be committed as durable state.

## Build Flow

The build is intentionally small:

1. `scripts/generate-docs-service-index` reads the existing service catalog and
   writes `docs/generated/service-index.md`.
2. `scripts/build-docs-site` prepares `.local/mkdocs-src/`.
3. The build script copies `docs/` into that temporary tree.
4. It copies only cross-cutting service docs that belong in the central site,
   currently `services/caddy/README.md` and
   `services/homelab-monitor/README.md`.
5. Generated service pages are copied into the temporary MkDocs tree as
   `/services/` and `/services/<service>/`.
6. MkDocs builds the rendered site into `.site/`.

This means service pages in the docs site are either central docs or generated
catalog wrappers. App-specific docs are loaded live from the service-owned
`/docs` endpoint when that endpoint validates.

## Local Preview

Use a local virtual environment so docs tooling does not become a system Python
dependency:

```bash
python3 -m venv .local/docs-venv
.local/docs-venv/bin/python -m pip install -r docs/requirements.txt
PATH="$PWD/.local/docs-venv/bin:$PATH" ./scripts/build-docs-site
python3 -m http.server 8765 --bind 127.0.0.1 --directory .site
```

Then open `http://127.0.0.1:8765/`.

The local preview is private to this machine. The deployed homelab route is
`https://docs.home.feocco.com`.

## Hosting Status

The primary homelab route is `https://docs.home.feocco.com`. It is served by
the `homelab-docs` Nginx container on the Mac mini, with Caddy terminating HTTPS
and UniFi DNS resolving the hostname on the LAN.

This repository also has a GitHub Pages workflow in `.github/workflows/docs.yml`.
That workflow builds `.site/` and deploys it to GitHub Pages after the workflow
is merged to `main` or manually dispatched from the default branch.

Do not assume GitHub Pages and private homelab DNS are the same deployment
model. The homelab route is private infrastructure; GitHub Pages is a separate
publishing path.

## Validation

Run the focused docs check after changing docs navigation, generation, or
Homepage docs links:

```bash
./scripts/tests/check-docs-site
```

That check verifies the MkDocs configuration, generated service index shape,
ignored generated output, Homepage docs link, and strict MkDocs build when
MkDocs is installed.

Service API convention validation is separate. When a service declares
`docs_path`, `openapi_path`, and `api_framework`, rollout validation checks the
metadata during config validation and checks live HTML/OpenAPI responses during
live validation:

```bash
LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check config --mode strict
LC_ALL=C ./scripts/validate-service-rollout --service <service> --host <host> --check live --mode strict
```

The generated service index reports which active Mac mini app services have
migrated and which still need separate app-repo work.

The service wrapper pages use three docs statuses:

- `Live docs available`: live `/docs` returns HTML and `/openapi.json` returns
  valid OpenAPI during the docs build.
- `Declared but failing`: docs metadata exists, but the live endpoints do not
  validate.
- `Not migrated`: no service docs metadata is declared.

## Migration Work

Do not migrate every service as part of docs-site plumbing. The service API
convention should move one service at a time:

1. Update the app repo to serve `/docs` and `/openapi.json`.
2. Add app tests for docs HTML, OpenAPI JSON, and unchanged health/API behavior.
3. Publish and deploy the app image through the normal service workflow.
4. Update `services/<service>/ops.yaml` with `docs_path`, `openapi_path`, and
   `api_framework`.
5. Run config validation before deploy and live validation after deploy.

The first pilots are `hello-nas` and `homelab-functions`. The remaining active
services should be migrated separately after the convention lands.

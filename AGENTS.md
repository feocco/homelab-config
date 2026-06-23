# AGENTS.md

## Repo-Specific Decisions

- This repo owns private Docker runtime config only. App repos own source,
  Dockerfiles, tests, and GHCR publishing.
- Use Docker Compose and host manifests, not Kubernetes.
- Default app/compute services to `macmini`; keep NAS infrastructure,
  storage-adjacent services, Portainer, Pi-hole, and the NAS runner on
  `nasfeo`.
- Run one `homelab-log-watcher` per Docker host. The central
  `homelab-sre-agent` runs on `macmini`.

## Agent Workflows

- Classify deployment work before editing runtime config:
  - App code changed only: commit/push the app repo, publish the image, then
    run an operational redeploy through the homelab-config workflow. Do not
    edit this repo unless the runtime shape changed.
  - Runtime config changed: make the matching homelab-config change for env,
    secrets, ports, volumes, host placement, image references, commands,
    monitoring, dashboards, links, or SRE metadata.
  - Third-party or config-only service changed: this repo usually owns the
    durable change.
- Inspect `git status --short --branch` before deployment work.
- Validate deployment changes with `./scripts/test-deploy-tooling`.
- When secrets or `.env.config` files change, run:
  `./scripts/generate-service-secret-workflow-env`,
  `./scripts/check-service-secrets`, and `./scripts/test-deploy-tooling`.
- Prefer host-aware commands, for example
  `./scripts/homelab-deploy --host macmini <service> --dry-run`.
- Do not treat a dirty or unpushed deploy as durable production state.
  Commit and push before a durable deploy.
- Treat branch deploys as temporary canaries. Use `--canary`, then merge and
  redeploy from `main` when the canary should become production truth.
- If you must leave temporary runtime state behind, say so explicitly in the
  final answer.
- Final answers for deploy work must say what was committed, pushed, and
  deployed.

## Runtime And Deployment Notes

- Mac services bind Docker ports to `127.0.0.1` and expose selected ports
  through `hosts/macmini/tailscale-serve.yaml`.
- Mac containers should call other Mac-hosted services through
  `host.docker.internal`.
- NAS-to-Mac calls should use the Mac mini Tailnet name.
- Setting `enabled: false` in a host manifest does not stop an already-running
  container. Stop old containers manually after the new host is verified.
- `scripts/homelab-deploy` writes local deploy provenance to
  `.homelab-deploy-state/<host>/<service>.json` in the runtime tree. This is
  evidence only; `main` remains the source of truth.
- See `docs/deployment-source-of-truth.md` for the branch, dirty deploy, and
  emergency runtime edit model.

## Footguns

- Do not hand-edit generated secret blocks in `.github/workflows/deploy.yml`.
  Update `service-secrets.yaml` or host manifests, then run the generator.
- Never commit real `.env` files or runtime `data/` contents.

## Cursor Cloud specific instructions

- This repo is bash/python CLI tooling + deploy config; there is no
  long-running app to start and no language dependency manifests. Standard
  commands live in `README.md` (deploy) and the `## Agent Workflows` section
  above (validate/secrets).
- Always run the deploy tooling with `LC_ALL=C`. The generated secret block in
  `.github/workflows/deploy.yml` is sorted under C collation (underscore sorts
  after letters). Under the VM default `en_US.UTF-8`, `sort` reorders keys, so
  `./scripts/test-deploy-tooling`, `./scripts/check-service-secrets`, and
  `./scripts/generate-service-secret-workflow-env` falsely report the block as
  stale (and the generator would rewrite it incorrectly). Prefix all three with
  `LC_ALL=C`, e.g. `LC_ALL=C ./scripts/test-deploy-tooling`.
- The `tailscale` CLI binary must be on `PATH` for the test suite to pass:
  `./scripts/test-deploy-tooling` runs `apply-tailscale-serve --dry-run`, which
  checks `command -v tailscale` before its dry-run branch. The startup update
  script installs the static `tailscale` CLI; the daemon is not needed.
- To exercise a real deploy offline (no Docker daemon, no GHCR access), put fake
  `docker`/`docker-compose` shims on `PATH` and deploy to a temp
  `--deploy-base-dir` with `--allow-dirty --canary` (needed off `main`). This is
  the same offline pattern `./scripts/test-deploy-tooling` uses; it renders the
  runtime `.env`, runs `compose up`, and writes the provenance JSON.

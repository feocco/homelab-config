# Deployment Source Of Truth

`homelab-config/main` is the durable production source of truth.

## Root Cause

The confusing state comes from temporary deploys escaping the branch where they
were created.

- Branch deploys create real host state before `main` knows about it.
- Dirty deploys create host state that no commit can reproduce.
- Later `main` deploys overwrite unmerged runtime state.
- Multiple Codex sessions can leave partial changes in one shared repo.
- Compose can leave old containers when service names or projects change.
- Restarts expose drift; restarts are not the root cause.

Common symptoms are duplicate containers, reverted config, missing services, or
a service working until the next deploy from `main`.

## Recommended Model

- `main` is durable production truth.
- Feature branches are review and canary space.
- Branch deploys are temporary canaries only.
- Dirty deploys are blocked by default.
- Runtime edits are emergencies only.
- Successful canaries must be merged and redeployed from `main`.

## Durable Deploy Workflow

1. Inspect repo state with `git status --short --branch`.
2. Make the smallest config change needed.
3. Run `./scripts/test-deploy-tooling`.
4. Commit and push the change.
5. Merge or push to `main` for durable production state.
6. Deploy from `main`, preferably service-scoped.
7. Confirm the final answer says what was committed, pushed, and deployed.

Service-scoped deploys remain preferred. A full-host deploy can restart unrelated
services and increase blast radius, so it is not the default fix for drift.

## App-Code-Only Image Redeploys

When only an application repo changed, do not edit `homelab-config`. Commit and
push the app repo, wait for the GHCR image publish, then trigger an operational
redeploy:

```sh
./scripts/redeploy-image --host macmini plant-monitor
```

That wrapper dispatches the existing `deploy.yml` workflow from
`homelab-config/main` with `force_recreate=true`, so the target host pulls the
latest Joe-owned `ghcr.io/feocco/*` image and recreates the service container.
Use `--print` to preview the workflow command and `--watch` to follow the run.

Plain container restarts are not the durable image-update path because they do
not guarantee a fresh image pull. Third-party images such as Docker Hub services
are not force-pulled on every deploy; update them intentionally by changing the
image reference or running a manual maintenance update.

## Canary And Emergency Deploys

Use `--canary` for a branch deploy:

```sh
./scripts/homelab-deploy --host macmini plant-monitor --canary
```

A canary is only a runtime test. If it works, merge the same config to `main`
and redeploy from `main` when practical.

Use `--allow-dirty` only for an emergency runtime edit:

```sh
./scripts/homelab-deploy --host macmini plant-monitor --allow-dirty
```

`--allow-dirty` skips only the dirty-worktree gate. A non-`main` branch still
needs `--canary`, deploying to macmini from another machine still needs
`--allow-foreign-host`, and pre-deploy config validation still runs unless you
pass `--skip-config-validate`. Each escape hatch names exactly the guard it
skips, so an emergency edit only bypasses what you consciously chose to bypass.

After an emergency deploy, immediately write down what changed, commit the
durable config, and redeploy from `main`.

## Script Guardrails

`scripts/homelab-deploy` now:

- Blocks non-dry-run deploys from dirty worktrees (`--allow-dirty` overrides
  only this gate).
- Requires `--canary` for non-`main` deploys.
- Requires the macmini production host identity (`--allow-foreign-host`
  overrides only this gate).
- Runs `validate-service-rollout --check config --mode strict` before every
  real deploy (`--skip-config-validate` overrides only this gate).
- Explicitly pulls only Compose services whose image is `ghcr.io/feocco/*`.
- Runs Compose with `--remove-orphans`.
- Writes runtime provenance to `.homelab-deploy-state/<host>/<service>.json`.

The deploy state files are local runtime evidence only. They are ignored by git
and do not replace `main` as source of truth.

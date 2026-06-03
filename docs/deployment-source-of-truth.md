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
2. Plan the service path with `./scripts/homelab-plan --service <service>`.
3. Make the smallest config change needed.
4. Run `./scripts/test-deploy-tooling`.
5. Commit and push the change.
6. Merge or push to `main` for durable production state.
7. Deploy from `main`, preferably service-scoped.
8. Confirm the final answer says what was committed, pushed, and deployed.

Service-scoped deploys remain preferred. A full-host deploy can restart unrelated
services and increase blast radius, so it is not the default fix for drift.

## Deploy Paths

`scripts/homelab-plan` reads `homelab-deploy-policy.yaml`, host manifests, and
changed files to recommend one of three paths.

### Direct

Use a direct deploy for low-risk service changes that do not match canary or
restore-required policy.

```sh
./scripts/homelab-plan --service hello-nas
./scripts/homelab-deploy --host macmini hello-nas
```

A direct deploy should still come from clean, committed, pushed config when it
is meant to become durable production state.

### Canary

Use `--canary` for a branch deploy:

```sh
./scripts/homelab-plan --service plant-monitor
./scripts/homelab-deploy --host macmini plant-monitor --canary
```

A canary is only a runtime test. If it works, merge the same config to `main`
and redeploy from `main` when practical.

### Restore Required

When the planner reports `restore`, do not deploy yet. Record the backup,
restore, or rollback proof needed for the changed data, migration, recovery,
secret, auth, or token path. Deploy only after that proof exists and the plan no
longer leaves restore work implicit.

The planner intentionally emits no deploy command for this path.

### Emergency Dirty Deploy

Use `--allow-dirty` only for an emergency runtime edit:

```sh
./scripts/homelab-deploy --host macmini plant-monitor --allow-dirty
```

After an emergency deploy, immediately write down what changed, commit the
durable config, and redeploy from `main`.

## Script Guardrails

`scripts/homelab-deploy` now:

- Blocks non-dry-run deploys from dirty worktrees.
- Requires `--canary` for non-`main` deploys.
- Allows `--allow-dirty` as an explicit emergency override.
- Runs Compose with `--remove-orphans`.
- Writes runtime provenance to `.homelab-deploy-state/<host>/<service>.json`.

The deploy state files are local runtime evidence only. They are ignored by git
and do not replace `main` as source of truth.

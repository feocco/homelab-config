---
name: verify-homelab-deploy
description: Check the homelab-deploy guard, canary, Mac mini identity, image pull, compose, and provenance decisions after a change to scripts/homelab-deploy. Use when editing deploy gates, --canary, --allow-dirty, --allow-foreign-host, --skip-config-validate, prepare, image pull, compose up, or deploy provenance.
---

# Verify homelab deploy

The check is a TLA+ model of one `scripts/homelab-deploy` invocation. TLC explores every situation in the model. A pass covers that model, not the whole homelab. Read every result with `/statechart`. The spec is `specs/homelab-deploy/HomelabDeploy.tla`, the config is `specs/homelab-deploy/HomelabDeploy.cfg`, and the chart view is `specs/homelab-deploy/view.mjs`.

`/statechart` pins TLC (tla2tools 1.7.4) and needs Java. The first run installs those tools. Do not add that download, or any TLC step, to `scripts/test-deploy-tooling` or the GitHub-hosted preflight. This check does not deploy. Do not pass `--allow-dirty`, `--canary`, `--allow-foreign-host`, or `--skip-config-validate` to a real deploy while checking it.

## What is covered

Sync commit: `5f75448767b00ce529b4d21d85a7d1e445f3c179`

`scripts/homelab-deploy` is unchanged since that commit. The model describes these parts of it:

- `git_branch` and `git_dirty_state`
- `require_host_identity` and `require_deploy_allowed`
- `run_config_validation`
- the `prepare_service` result inside `deploy_service` (a non-zero return stops the deploy; dry-run does not run the generator)
- `joe_owned_compose_services` and the pull decision in `deploy_service`
- `deploy_service` from the `.render-env-skipped` check through `write_deploy_state`

A change outside those lines does not by itself make the model stale. A change inside them does.

## When a change touches that code

1. Diff those functions from the sync commit to the commit you are on.
2. If a branch, a refusal, or the order of steps changed, edit the matching action in `HomelabDeploy.tla` so it describes the new code. Do this before you trust a pass. A pass on the old action does not see the new script.
3. Change an invariant only when the promise changed on purpose. The promise is the guard text in `scripts/homelab-deploy` and the "Script Guardrails" section of `docs/deployment-source-of-truth.md`. Cite that evidence in the spec comment. Do not weaken an invariant to make TLC pass.
4. Read the result with `/statechart`.
5. Move the sync commit in this skill forward only after the model describes the code at the new commit and the new run is done. Leave it where it is if the run could not finish.

To see that a rule can still fail, break the matching action in a scratch copy of the spec (delete the refusal, or let the failed step continue), run that copy, confirm the named invariant fails, then drop the scratch. Do not leave the break in `scripts/homelab-deploy`. The last scratch that was dropped removed the non-main `--canary` refusal from `require_deploy_allowed` and the same refusal from `CanaryGate`. TLC then failed `CanaryGateHeld`, `FeatureCheckoutNeedsCanary`, and `DetachedHeadIsNotMain`. Restoring both files left `ConfigProof` as the only failure.

## Known finding

`ConfigProof` fails on the current script. Do not weaken it, and do not change the script to satisfy it unless Joe asks.

The rule: a real deploy writes provenance only after strict config validation passed, or the operator passed `--skip-config-validate`.

The script's path: `run_config_validation` sees `scripts/validate-service-rollout` missing or not executable, or `python3` missing. It prints `deploying without config proof`, logs `config-validate` `skip`, and returns 0. Prepare, image pull, and compose up then run, and `write_deploy_state` writes `.homelab-deploy-state/<host>/<service>.json` with `canary` false and `git_dirty` false when the tree was a clean `main`. That JSON does not say validation was skipped.

`/statechart` numbers the shortest path. Replay it against `deploy_service` before calling it a modeling error. This path happens in the script. A step that cannot happen is a modeling error: fix the model, not the invariant.

## How to tell a bug from a modeling error

- The counterexample is a sequence of operator-visible steps. Walk it through `scripts/homelab-deploy`. If the script cannot do the next step, the model is wrong.
- `ConfigProof` is a bug in the sense that the script breaks the documented rule. It is not drift. The warning text shows the branch is intentional. Report it. Do not "fix" the model so the branch disappears.
- These rules held at the sync commit, and each failed when its check was removed in a scratch model: `ProvenanceFollowsUp`, `DirtyGateHeld`, `CanaryGateHeld`, `ForeignHostGateHeld`, `NasfeoSkipsIdentity`, `NamedMainIsMain`, `FeatureCheckoutNeedsCanary`, `DetachedHeadIsNotMain`, `DryRunWritesNothing`, `AuthPullDoesNotStart`, `PrepareFailureStops`, `CaddyDoesNotPull`, `ThirdPartyDoesNotPull`, `SecretsBlockTheDeploy`, `ProvenanceRecordsFlags`, `EveryStopIsExplained`, `TypeOK`. `NoDeadlock` holds because finished states take a step that changes nothing.

## Bounds

TLC checks 38 situations and 282 states. The situations are one clean `main` deploy on nasfeo plus the refusals, the single-flag passes (`--allow-dirty`, `--canary`, `--allow-foreign-host`, `--skip-config-validate`), and the pairs where one of those flags is set and a different gate must still refuse. Branch resolution includes a named `main` checkout with `GITHUB_REF_NAME=50/merge`, a named feature checkout with `GITHUB_REF_NAME=main`, and detached `HEAD` with `50/merge` or an empty job ref.

The model assumes the service is enabled and has a compose file, and that `hosts/macmini/services.yaml` sets both `deploy_user` and `bind_addr`. `onProductionHost` is both halves of `require_host_identity` (user, then address). An empty value skips that half in the script and is not a separate situation.

## Left out

`--list` does not deploy. `--all` and `--changed` call the same gates, then `deploy_service` once per service; a failure stops the rest because of `set -e`. `--changed` can add caddy when the generated Caddyfile differs. `--force-recreate` only changes the compose arguments. The Caddy reload's ten attempts are one success or one failure. `configure-authentik-settings --apply` sits in the same subshell after compose up, so a failure skips provenance the way a failed Caddy reload does, and it is not its own situation. The model does not open `validate-service-rollout` and does not decide which image tag was pulled, only whether the pull was skipped, succeeded, denied or missing, or a transient failure that continues with the cached image. Provenance does not record `--allow-foreign-host`.

After a change that skipped this skill, use `/maintain-formal-verification-skill`.

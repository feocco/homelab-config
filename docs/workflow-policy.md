# GitHub Actions Workflow Policy

`scripts/check-workflow-policy` is a copyable static guard for repositories that
use GitHub Actions, especially public repositories that can receive untrusted
pull requests and comments.

## Enforced Policy

Every workflow must declare top-level `permissions` with only `read` or `none`
access (or `read-all`). A job may elevate its own permissions when needed.
Write access at the workflow level fails policy unless every reachable event
root is `workflow_dispatch` or `repository_dispatch`; dispatch-only workflows
emit a warning instead.

Third-party `uses:` references must pin an exact 40-character commit SHA.
References under `actions/*` and `github/*`, local actions and reusable
workflows are exempt.

Jobs using the `self-hosted`, `nasfeo`, or `macmini` runner labels must not be
reachable from:

- `pull_request` or `pull_request_target`;
- issue, commit, discussion, or pull-request comment events;
- issue creation or updates, forks, or watches;
- pull-request review events;
- a local reusable-workflow call rooted in one of those events; or
- a transitive `workflow_run` chain rooted in one of those events.

Jobs in an explicitly configured deploy workflow, jobs using a protected runner
label, and jobs whose runner expression cannot be proven GitHub-hosted must
include a literal repository identity guard:

```yaml
if: github.repository == 'feocco/example'
```

The equality must be the first condition and may only be followed by `&&`.
Parenthesized alternatives after that conjunction are allowed, but a top-level
`||` could bypass the guard and is rejected. The identity guard is defense in
depth. It does not make an untrusted event safe for a self-hosted runner.

## Usage

Install the pinned parser and run the validator with the repository identity
that must appear in sensitive job guards:

```sh
python3 -m pip install --require-hashes -r scripts/requirements-workflow-policy.txt
scripts/check-workflow-policy \
  --repository feocco/homelab-config \
  --deploy-workflow .github/workflows/deploy.yml
scripts/tests/check-workflow-policy
```

The repository's `Workflow Policy` workflow runs the fixture suite on every
pull request and every push to `main`, using GitHub-hosted runners only.

## Adopting In Another Public Repository

For a new public `feocco` repository such as Pebble:

1. Copy `scripts/check-workflow-policy` and
   `scripts/requirements-workflow-policy.txt`.
2. Copy `.github/workflows/workflow-policy.yml` and its fixture test, or invoke
   the validator directly if the repository has its own test harness.
3. Change `--repository` in the test and workflow invocation to the exact
   `feocco/<repo>` identity. Pass each deployment workflow path with a repeated
   `--deploy-workflow`; do not rely on naming heuristics. Keep action references
   pinned to full commit SHAs.
4. Start the workflow with top-level read-only permissions. Put publishing
   scopes such as `packages: write` on the publishing job only.
5. Keep pull-request, comment, and review automation on GitHub-hosted runners.
   Put deployment on a trusted trigger such as a push to `main` or a manually
   dispatched workflow, with the literal repository identity guard on every
   deploy or self-hosted job.

Pebble does not need the homelab-specific `nasfeo` or `macmini` labels for the
validator to be useful; the generic `self-hosted` protection and permissions
rules still apply.

## Static-Analysis Boundaries

The validator resolves `workflow_run` sources by their workflow `name`,
including transitive chains, then separately follows local
`./.github/workflows/...` reusable calls. This distinction avoids treating an
inline reusable call as a standalone run that could trigger `workflow_run`. It
intentionally treats declared event reachability as reachable even when a job
has another conditional guard.

It does not fetch or inspect reusable workflows from other repositories.
Protected runner labels must be literal in `runs-on`, or literal values in a
referenced matrix. Arbitrary runner expressions and object/group selections fail
closed because the validator cannot prove they select GitHub-hosted capacity.
Repository or organization runner-group policy is not resolved statically.
GitHub Actions still validates workflow syntax and unresolved local call or
`workflow_run` names.

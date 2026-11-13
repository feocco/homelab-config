# Deploy events

Deploy and check commands print one JSON object per stage on stderr. The
fields are `event`, `slug`, `stage`, `outcome`, and `ms`.

## Sub-features

- `event-deploy` logs a service deploy from `scripts/homelab-deploy`.
- `event-check` logs one row per check from `scripts/test-deploy-tooling`.
- `event-shape` requires exactly those five fields, with `ms` a non-negative integer.
- `event-dry-run` records skip and dry-run outcomes without starting containers.

## How to get to it (user POV)

- Run a dry-run deploy, or run the deploy-tooling suite.

## Driving it with shell

Preconditions:

- `VERIFY_HOMELAB_ARTIFACTS` exists.
- The verification runner is executable.

- **Run verification.** Run
  `./.cursor/skills/verify-homelab-config/scripts/run-verification`.
- **Check the event contract.** Read `deploy-events.log` and the `deploy-events`
  row in `summary.txt`.
- **Prove success.** Require exit status `0` and `deploy event log: ok`.
- **Read a deploy line.** A dry-run for a service emits `event` `deploy`, the
  service `slug`, and stages `config-validate`, `prepare`, `image-pull`, and
  `compose-up`. `outcome` is `ok`, `fail`, `skip`, or `dry-run`. `ms` is
  elapsed milliseconds.
- **Read a check line.** `event` is `check`, `slug` is the check script name,
  and `stage` is `offline` or `live`.

## Gotchas

- Event lines go to stderr. `--json` on the suite still prints its summary
  object on stdout.
- `--list` does not emit deploy events.
- Live tailnet fetches stay behind `--live`. This feature's dry-run does not
  contact Grafana or hello-nas.
- Do not deploy, and do not pass `--allow-dirty`, `--canary`,
  `--allow-foreign-host`, or `--skip-config-validate`.

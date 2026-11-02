# Waiting

Runtime config for the private `feocco/waiting` action inbox, served at
`https://waiting.home.feocco.com` through Caddy and UniFi internal DNS.

It replaces the dashboard that homelab-functions served on the same hostname.
`data/` holds the feedback store (`waiting-feedback.sqlite3`).

Secrets (GitHub Actions, rendered into `.env`): `WAITING__WAITING_TOKEN`,
`WAITING__DASHBOARD_GH_APP_KEY`, `WAITING__CURSOR_API_KEY`.

Deploy checks:

```bash
LC_ALL=C ./scripts/validate-service-rollout --service waiting --host macmini --check config --mode strict
./scripts/homelab-deploy --host macmini waiting --dry-run --base-dir /Users/feocco/code/homelab-config --deploy-base-dir /Users/feocco/code/homelab-config
```

# Bedtime

Private runtime config for the `feocco/bedtime` Home Assistant watcher.

The app repo stays public and generic. This folder owns the real Home Assistant
entity mapping, runtime environment contract, and persistent `data/state.json`
used to enforce one notification per bedtime night and keep the local usage
history for morning follow-up replies.

Deploy checks:

```bash
./scripts/check-service-secrets
./scripts/homelab-deploy bedtime --dry-run --base-dir /Users/feocco/homelab-config --deploy-base-dir /Users/feocco/homelab-config
```

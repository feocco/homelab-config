# Bedtime

Private runtime config for the `feocco/bedtime` Home Assistant watcher.

The app repo stays public and generic. This folder owns the real Home Assistant
entity mapping, runtime environment contract, and persistent `data/state.json`
used to enforce one notification per bedtime night and keep the local usage
history for morning follow-up replies.

Deploy checks:

```bash
LC_ALL=C ./scripts/validate-service-rollout --service bedtime --host macmini --check config --mode strict
./scripts/homelab-deploy --host macmini bedtime --dry-run --base-dir /Users/feocco/code/homelab-config --deploy-base-dir /Users/feocco/code/homelab-config
```

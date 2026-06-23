# laundry-monitor

Runtime config for the `laundry-monitor` app repo.

The service runs on `macmini`, reads washer and dryer power from Home Assistant,
and sends mobile notifications for laundry lifecycle workflows. The primary
workflow reminds Joe and Jess when a washer load has not moved to the dryer
within 6 hours.

Secrets live in GitHub Actions secrets and the local ignored `.env` file:

- `HA_URL`
- `HA_LONG_LIVED_TOKEN`
- `HA_NOTIFY_JOE_SERVICE`
- `HA_NOTIFY_JESS_SERVICE`

Non-secret thresholds live in `.env.config`.

## Operations

The service exposes:

- `GET /health` on `127.0.0.1:8102` for blackbox monitoring.
- `GET /v1/status` for washer, dryer, transfer-reminder, and validation state.
- persistent runtime state in `data/state.json`.

Expected monitoring coverage:

- Prometheus `blackbox-http` probe for `service="laundry-monitor"`.
- Docker restart alert coverage for the `laundry-monitor` container.
- `homelab-sre-agent` mapping with SRE enabled and autofix disabled.

Useful checks on `macmini`:

```sh
docker ps --filter name=laundry-monitor
docker logs --tail 200 laundry-monitor
curl -fsS http://127.0.0.1:8102/health
curl -fsS http://127.0.0.1:8102/v1/status
```

If reminders do not fire, check `/v1/status` first:

- `appliances.*.fresh` should be true during active power updates. Idle dryer
  readings may be stale without making global health fail.
- `washer_to_dryer.waiting_since` should be set after a washer finish.
- `washer_to_dryer.next_reminder_at` should be due before a reminder is sent.
- `validation.pending` should only contain rollout confirmation prompts.

Common failure modes:

- `HA_LONG_LIVED_TOKEN` invalid or expired: the container logs show Home
  Assistant connection/authentication errors and `/health` is degraded.
- missing Home Assistant entities: confirm
  `sensor.smartthings_outletv4_power` and `sensor.dryer_plug_power` exist.
- notification actions ignored: verify `mobile_app_notification_action` events
  are reaching Home Assistant and the app logs show action handling.
- image pull failures: confirm `ghcr.io/feocco/laundry-monitor:latest` exists
  and has the expected package visibility for the runtime host.
- port binding failures: confirm no other local service uses `8102`.

# Dog Bowl Monitor

Mac mini service that listens for Home Assistant Nest camera events and checks
whether the sun room dog bowl has food.

- App repo: `/Users/feocco/code/dog-bowl-monitor`
- Image: `ghcr.io/feocco/dog-bowl-monitor:latest`
- Local health: `http://127.0.0.1:8101/health`
- Persistent data: `./data`

## Paused

This service is intentionally decommissioned for now because the current sun room
camera placement cannot reliably see the dog bowl. The app repo, runtime config,
secret mappings, and persistent data are preserved so it can be picked back up
after the camera is moved or re-aimed.

To reactivate it, set `dog-bowl-monitor` back to `enabled: true` in
`hosts/macmini/services.yaml` and `hosts/macmini/tailscale-serve.yaml`, restore
`tailnet`, `monitoring`, `sre`, route fields, and dashboard visibility in
`ops.yaml`, restore the Prometheus, Grafana, monitor-health, and SRE entries,
then redeploy the service and affected support services.

The service uses Home Assistant events from `event.sun_room_camera_motion`,
captures frames from `camera.sun_room_camera`, sends accepted frames to OpenAI
vision, and notifies Joe after every check.

Browser capture is intentionally deferred. See the app repo follow-up doc if
event-timed API capture keeps returning Home Assistant/Nest placeholder frames.

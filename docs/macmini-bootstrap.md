# Mac Mini Bootstrap

The Mac mini is the app/compute Docker host. The first canary service is
`hello-nas`; after canary validation, app-style services run here while NAS
infrastructure remains on `nasfeo`.

## Target

```text
host: macmini
lan_ip: 192.168.1.43
runtime_path: ${HOME}/homelab-config-runtime
runner_labels: self-hosted,macmini,docker,homelab
```

## SSH Access

Install a dedicated deploy public key for `feocco@192.168.1.43`, then verify:

```bash
ssh -o BatchMode=yes feocco@192.168.1.43 'hostname; sw_vers; docker version; docker compose version'
```

## Runtime Setup

On the Mac mini:

```bash
mkdir -p "${HOME}/homelab-config-runtime"
```

Install a native macOS GitHub Actions runner for `feocco/homelab-config` and add
the labels `macmini,docker,homelab`.

## Canary

After the runner is online, dispatch:

```bash
gh workflow run Deploy \
  --repo feocco/homelab-config \
  -f host=macmini \
  -f service=hello-nas \
  -f force_recreate=true
```

Then verify over Tailscale:

```bash
curl -fsS http://maclabs-mac-mini.taildf3445.ts.net:8099/health
```

Mac mini services should bind Docker ports to `127.0.0.1` and expose selected
ports through Tailscale Serve. OrbStack listened on `192.168.1.43` when
configured with the LAN IP directly, but HTTP requests did not complete. The
working v1 pattern is local-only Docker ports plus Tailnet-only Tailscale Serve.

## Current App Placement

The Mac mini is expected to run:

- `hello-nas`
- `bedtime`
- `dashy`
- `hass-janitor`
- `homelab-functions`
- `homarr`
- `homelab-monitor`
- `plant-monitor`
- `homelab-log-watcher`
- `homelab-sre-agent`

The NAS keeps Portainer, the NAS runner, Pi-hole outside this repo, and its own
`homelab-log-watcher`. `netalertx` remains disabled until its Mac mini host
networking and scan interface are validated.

`homelab-monitor` uses native Homebrew `node_exporter` on Mac mini for host
metrics and a Docker socket exporter for high-level container stats. Grafana is
exposed only through Tailscale Serve at
`http://maclabs-mac-mini.taildf3445.ts.net:3000`.

## Tailscale Dependency

The NAS must be a Tailscale node before the central Mac-hosted SRE agent can
receive incidents from the NAS log watcher. Verify from the NAS:

```bash
/var/packages/Tailscale/target/bin/tailscale status
curl -fsS http://maclabs-mac-mini.taildf3445.ts.net:8099/health
```

Mac-hosted containers should call each other through `host.docker.internal`.
Cross-host calls from NAS to Mac should use
`maclabs-mac-mini.taildf3445.ts.net`.

## Migration Footgun

Changing `enabled: false` in a host manifest prevents future deploys but does
not stop an existing container. During migrations, copy any needed state first,
deploy the new host, verify health, then manually stop the old host container.

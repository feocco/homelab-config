# Mac Mini Bootstrap

The Mac mini is the app/compute Docker host. The first canary service is
`hello-nas`; production services should stay on `nasfeo` until the canary deploy
path is proven.

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

Then verify:

```bash
curl -fsS http://192.168.1.43:8099/health
```

Note: the Mac mini canary binds `HOST_BIND_ADDR=0.0.0.0`. OrbStack listened on
`192.168.1.43` when configured with the LAN IP directly, but HTTP requests did
not complete. Binding all interfaces is the working v1 path until Tailscale or a
reverse proxy gives us a cleaner Mac-specific bind target.

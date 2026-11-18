# tailnet-client-probe

Checks every homelab site the way Joe's Pixel reaches it with Tailscale on,
every 15 minutes from `nasfeo`, and alerts Joe through homelab-functions.

## Why

Android 17 drops an app's traffic to LAN addresses (RFC1918, link-local, and
100.64.0.0/10 on Wi-Fi) unless the app holds the Local network permission.
Chrome 156 can lose that grant and then fails every LAN-resolved page with
`ERR_TOO_MANY_RETRIES` (crbug.com/579403238). Traffic over the Tailscale VPN is
exempt, so homelab names must resolve to tailnet addresses for tailnet
clients. `scripts/sync-tailscale-split-dns` sets that up; this probe proves it
keeps working.

## What one run checks

For each hostname in `targets.txt`:

1. Resolve with the host resolver (Tailscale MagicDNS on `nasfeo`).
2. Fail if any answer is outside `100.64.0.0/10` or `fd7a:115c:a1e0::/48`.
3. HTTPS to each answer with SNI and certificate verification. Fail on a
   connect or TLS error or an HTTP status of 500 or more. 401 and 302 pass,
   since they are the normal login walls.

## Alerts

- After `FAILURES_BEFORE_ALERT` (2) failing runs in a row: one notification
  listing each failing host and why.
- On the first passing run after an alert: one all-clear.
- A failed notify is retried on the next run. State lives in
  `data/state.json`, so a restart does not reset the count.

## Targets

`targets.txt` is every DNS-only route name from
`scripts/sync-cloudflare-dns --dry-run`. `scripts/tests/check-tailnet-client-probe`
fails CI when it drifts. Regenerate with:

```sh
./scripts/sync-cloudflare-dns --dry-run | sed -E 's/^Would upsert Cloudflare A ([^ ]+) .*/\1/' | sort
```

## Run once by hand

```sh
docker compose run --rm tailnet-client-probe python /app/probe.py --once
```

## Limits

The probe checks the server side of the path: DNS answers and HTTPS over the
tailnet. It cannot see a phone's permission state, so Chrome's own bug can
still show up for a site reached by a LAN address.

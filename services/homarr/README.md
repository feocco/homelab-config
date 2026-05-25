# Homarr

Homarr is the primary homelab dashboard during the Dashy migration.

- URL: `http://maclabs-mac-mini.taildf3445.ts.net:7575/`
- Dashy remains available at `http://maclabs-mac-mini.taildf3445.ts.net:8080/`
  and through the NAS redirect at `http://nasfeo:8080/`
- Docker socket access is intentionally not mounted
- Persistent application data is stored in `./data`

## Seeding

The first-pass Homelab board is seeded from `seed/homelab.json` through the
ignored local API key in `.env`. If `HOMARR_URL` is set in the shell or in
`.env`, the script uses it; otherwise it defaults to the Mac mini Tailnet URL
above.

```bash
./scripts/seed-homarr --dry-run
./scripts/seed-homarr --apply
```

The script creates or updates named apps, creates the private `Homelab` board
when missing, applies sections and app widgets, and sets `Homelab` as the
desktop and mobile home board. The seed groups daily-use links into a full
first row so the dashboard uses wide monitors better. It does not delete
unknown apps or boards.

Homarr app status checks run from the Homarr container, not from the browser.
Keep `pingEnabled` off for links that are only cleanly reachable from the LAN
or browser; Grafana/Prometheus should own those availability checks.

The mounted `nginx.conf.template` intentionally strips `Accept-Encoding` before
proxying to Homarr's Next.js server. That avoids compressed chunked HTML
responses on the Tailnet URL, which Chrome has shown as
`ERR_INCOMPLETE_CHUNKED_ENCODING` for board pages.

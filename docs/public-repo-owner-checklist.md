# Public repo owner checklist

Everything the owner must do before flipping this repo to public. Designed to be
run from the Mac mini (directly or over SSH) with as little manual entry as
possible. No new GitHub Actions secrets are required (repo is near the ~82
secret limit); scrubbed identity values live in private host overlays instead.

## 1. Migrate scrubbed identifiers (one command, no typing)

The scrubbed values still exist in the live rendered `.env` files on the Mac
mini. Harvest them into private overlays **before** deploying the scrubbed
config.

If `./scripts/install-private-config` is not in the runtime tree yet (first
migration, before this commit is deployed), use the bootstrap harvest in the
assistant chat, or pull this commit into a checkout and run the script against
`--deploy-base-dir ~/homelab-config-runtime`. Once this commit is live:

```bash
# On the Mac mini (or: ssh maclab@<mac-mini> 'cd ~/homelab-config-runtime && ...')
cd ~/homelab-config-runtime
./scripts/install-private-config --host macmini
```

That reads `~/homelab-config-runtime/services/<service>/.env`, extracts the
managed keys, and writes:

```text
~/homelab-private-config/macmini/<service>.env   (chmod 600)
```

Managed keys (all Mac mini): `CADDY_ACME_EMAIL`, `AUTHENTIK_BOOTSTRAP_EMAIL`,
`DEFAULT_EMAIL`, `HA_NOTIFY_JOE_SERVICE`, `HA_NOTIFY_JESS_SERVICE`,
`SRE_DIAGNOSTIC_S3_BUCKET`, `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`.

Re-running is safe (idempotent). `render-service-env` prefers the overlay over
the tracked placeholder, so the next deploy keeps the real values.

### If the live .env no longer has real values

If you already deployed the scrubbed config, the harvest reports `MISSING`. Fall
back to a template you fill once:

```bash
./scripts/install-private-config --print-template > /tmp/private.ini
# edit /tmp/private.ini, fill each key (comments explain each one)
./scripts/install-private-config --host macmini --from-file /tmp/private.ini
rm /tmp/private.ini
```

Verify a render picks up the overlay (writes a runtime `.env`, values not
printed):

```bash
CADDY__CLOUDFLARE_API_TOKEN=dummy ./scripts/render-service-env --host macmini caddy \
  --deploy-base-dir "$(mktemp -d)"
```

## 2. Tailscale — checked from the CLI, no browser

Use the helper instead of the admin console.

```bash
# Tags + serve state (local CLI only, no key needed):
./scripts/tailscale-acl status
```

Already confirmed from here: `maclabs-mac-mini` carries
`tag:homelab-service-host` and is online, which is what makes the friend
Services serve.

For the full grants/ACL text the Tailscale CLI has no read command, so the
helper uses the Tailscale API. Create an API access token once
(`https://login.tailscale.com/admin/settings/keys`), then everything is CLI:

```bash
export TAILSCALE_API_KEY=tskey-api-...
export TAILNET=taildf3445.ts.net   # or your tailnet name; default is token tailnet
./scripts/tailscale-acl get        # prints live policy
./scripts/tailscale-acl check      # asserts tag owner + svc:authentik/svc:pirate-radio grants
```

`docs/tailscale-friends-policy.hujson` is now a **template** (real friend emails
removed). The live policy lives in your tailnet; the token lets the helper read
or diff it. Store the token in your password manager, not in git.

## 3. UniFi console link — what changed

Scrubbed from exactly one place: the `UniFi Devices` card in
`services/homepage/manual-links.yaml` (and its test assertion). The old value
was a deep link that embedded your unique console id and site id:

```text
https://unifi.ui.com/consoles/<CONSOLE_ID>:<SITE_ID>/network/default/clients/main
```

It now points at `https://unifi.ui.com/`. On `home.feocco.com` the card is
**still clickable** — it just lands on the UniFi console picker and you click
into your console, instead of jumping straight to the clients page.

If you want the one-click deep link back without publishing the id, put the full
URL in your browser bookmarks / password manager. (A future option: move it into
a private Homepage links overlay, similar to env overlays. Not built yet.)

## 4. LAN map — does it matter?

Mostly correct: those `192.168.1.x` / `100.x` Tailnet addresses only help
someone who is **already on your LAN or in your tailnet**. They are routing
hints, not credentials, and they do not expose anything to the public internet
by themselves — reaching a service still requires being on the network plus
passing Caddy/Authentik/Tailscale auth.

Recommendation: **leave them** (Option A). They were not scrubbed in this pass.
Softening prose docs later is optional; moving binds into overlays is a larger
generator/test change and not worth secret slots.

## 5. GitHub settings already applied by the assistant

- Pull requests: **disabled** (strangers cannot open PRs)
- Issues / Wiki / Projects: **disabled**
- Dependabot vulnerability alerts: **enabled**
- Branch protection on `main`: no force-push, no deletion, enforce admins
- Ruleset `Protect main`: deletion + non-fast-forward blocked

After the repo is public (some show only then on personal repos):

- Confirm **secret scanning** + **push protection** are enabled
- Optionally tighten Actions allowlist (currently `all`)

## 6. Order of operations to go public

1. `./scripts/install-private-config --host macmini` on the Mac mini (section 1)
2. Tell the assistant → it commits/pushes this prep and deploys once so the
   scrubbed config + overlays are live together
3. `./scripts/tailscale-acl status` (and `check` if you set a token)
4. Full-history secret scan (`gitleaks` or `trufflehog`)
5. Flip visibility to public
6. Verify secret scanning on; confirm PRs still disabled

## 7. Secrets caution

- ~**82** Actions secrets already exist. Do not migrate emails / App IDs /
  bucket names into new secrets — overlays avoid that entirely.
- Existing notify / SMTP secrets can stay as secrets; do not duplicate them into
  overlays.
- If you need headroom, prefer deleting unused secrets over adding new ones.

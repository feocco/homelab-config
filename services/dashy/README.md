# Dashy

Dashy runs from the standard `homelab-config` deployment shape on `macmini` and
is exposed through Tailscale Serve at
`http://maclabs-mac-mini.taildf3445.ts.net:8080/`.

Dashy sub-pages are configured with the top-level `pages` list in
`user-data/conf.yml`. The referenced page files live beside `conf.yml` in
`user-data/`.

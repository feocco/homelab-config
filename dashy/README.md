# Dashy

Dashy is currently running from `/volume1/docker/dashy-0` on `nasfeo`.

This folder stages the same service under the standard `homelab-config`
deployment shape. It is disabled in `services.yaml` until the standalone Dashy
container is stopped and the runtime config is cut over.

Dashy sub-pages are configured with the top-level `pages` list in
`user-data/conf.yml`. The referenced page files live beside `conf.yml` in
`user-data/`.

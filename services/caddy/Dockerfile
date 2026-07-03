ARG CADDY_VERSION=2.11.4

FROM caddy:${CADDY_VERSION}-builder-alpine AS builder
RUN xcaddy build \
    --with github.com/caddy-dns/cloudflare

FROM caddy:${CADDY_VERSION}-alpine
LABEL org.opencontainers.image.source=https://github.com/feocco/homelab-config
COPY --from=builder /usr/bin/caddy /usr/bin/caddy

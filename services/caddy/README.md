# Caddy

LAN reverse proxy for Mac mini dashboard hostnames.

## URLs

- Homarr: `http://homarr.home.arpa`
- Grafana: `http://grafana.home.arpa`
- Dashy: `http://dashy.home.arpa`

## UniFi DNS

Create these UniFi local DNS Host A records:

- `homarr.home.arpa` -> `192.168.1.43`
- `grafana.home.arpa` -> `192.168.1.43`
- `dashy.home.arpa` -> `192.168.1.43`

In UniFi Network, use **Settings > Policy Table > Create New Policy > DNS** on
Network 9.4, or **Settings > Policy Engine > DNS > Create DNS Record** on
Network 9.3. Choose `Host (A)`, then enter the hostname and Mac mini LAN IP.

The service is HTTP-only. `home.arpa` is local-only, so normal public ACME
certificates are not available for these names.

The container publishes Caddy on `0.0.0.0:80` because Docker on macOS does not
reliably expose ports when the publish address is pinned to the LAN IP. UniFi
DNS still points clients at the Mac mini LAN address.

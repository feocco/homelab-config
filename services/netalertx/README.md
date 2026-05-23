# NetAlertX

NetAlertX provides discovery-first network inventory for the home catalog.

- URL: `http://nasfeo:20211/`
- API / GraphQL port: `20212`
- Scan target: `192.168.1.0/24 --interface=eth0`
- Mode: discovery only; no VLAN or firewall changes

The container uses host networking because NetAlertX needs LAN-level discovery
visibility. Alerts should stay quiet until the inventory baseline is useful.

# Homarr

Homarr is the planned primary homelab dashboard during the Dashy migration.

- URL: `http://nasfeo:7575/`
- Dashy remains running at `http://nasfeo:8080/`
- Docker socket access is intentionally not mounted
- Persistent application data is stored in `./data`

The initial dashboard should be seeded manually or from the private
`feocco/home-catalog` generated Homarr app list.

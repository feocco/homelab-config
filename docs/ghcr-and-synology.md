# GHCR and Synology Notes

> **Owner operations notes.** This page documents how *this* homelab was
> stood up. It is not a public install guide. Strangers cannot run these steps
> without host access, Actions secrets, and private overlays that are
> intentionally absent from git.

## Recommended Path

Use GitHub Container Registry for images and Docker Compose on the NAS for
runtime configuration.

```text
public/private app repo -> GHCR image -> NAS compose project
```

## Synology Registry Setting

The registry selected in Synology Container Manager is mainly for browsing and
pulling images through the Synology UI. It should not prevent Docker Compose or
Docker CLI from pulling fully qualified images such as:

```text
ghcr.io/feocco/plant-monitor:latest
```

The practical path is:

```bash
docker-compose pull
docker-compose up -d
```

Existing Docker Hub containers such as Pi-hole can keep running. They
do not need to be moved to GHCR.

## NAS Login

If an image is private, create a GitHub token for the NAS with:

```text
read:packages
```

Then run on the NAS:

```bash
echo '<token>' | docker login ghcr.io -u feocco --password-stdin
```

For public images, no Docker registry login is required.

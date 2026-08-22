# Airtime Atlas

A responsive rollercoaster discovery app with search, type filters, ride statistics, and browser-persisted favourites. It ships as a small, unprivileged Nginx container and publishes multi-platform images to GitHub Container Registry.

## Run with Docker

```bash
docker compose up --build
```

Open <http://localhost:8080>. The container health endpoint is available at `/health`.

## Pull the published image

After the first successful GitHub Actions run:

```bash
docker pull ghcr.io/OWNER/rollercoaster-app:latest
docker run -d --name airtime-atlas -p 8080:8080 --restart unless-stopped ghcr.io/OWNER/rollercoaster-app:latest
```

Replace `OWNER` with the lowercase GitHub account name. The workflow also publishes immutable `sha-*` tags and version tags such as `v1.0.0`.

## Local development

The application uses plain HTML, CSS, and JavaScript, so it can be opened directly or served by any static file server.

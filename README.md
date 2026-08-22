# Airtime Atlas

A responsive rollercoaster discovery app backed by SQLite. It imports openly licensed statistics from Wikidata, exposes a JSON API, and publishes multi-platform images to GitHub Container Registry.

## Run with Docker

```bash
docker compose up --build
```

Open <http://localhost:8080>. The container health endpoint is available at `/health`.

The first start seeds the database immediately, then refreshes it from Wikidata in the background. Data is persisted in the `coaster-data` Docker volume. Set `SYNC_ON_START=false` to disable automatic refreshes.

## API

- `GET /api/coasters?q=taron&country=Germany&limit=100&offset=0`
- `GET /api/search?q=stel+vengeance&limit=8` (ranked fuzzy suggestions)
- `GET /api/coasters/Q16665871`
- `GET /api/stats`

Records include height, track length, speed, opening date, park, country, manufacturer, capacity, inversions, coordinates, and source URL where Wikidata provides them. Missing source values are returned as `null`.

## Pull the published image

After the first successful GitHub Actions run:

```bash
docker pull ghcr.io/simonbolton/rollercoaster-app:latest
docker run -d --name airtime-atlas -p 8080:8080 --restart unless-stopped ghcr.io/simonbolton/rollercoaster-app:latest
```

The workflow also publishes immutable `sha-*` tags and version tags such as `v1.0.0`.

## Local development

Run `python backend/server.py` from the repository root. Use `python backend/sync_wikidata.py` to refresh the local database manually.

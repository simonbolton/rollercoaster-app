# Airtime Atlas

A responsive rollercoaster discovery app backed by SQLite. It imports openly licensed statistics from Wikidata, exposes a JSON API, and publishes multi-platform images to GitHub Container Registry.

The bundled worldwide catalogue is normalized from Rob Mulla's CC0 Wikipedia rollercoaster dataset. Wikidata remains the refresh source for newer records.

## Run with Docker

```bash
docker compose up --build
```

Open <http://localhost:8080>. The container health endpoint is available at `/health`.

Every start upserts the bundled catalogue, then refreshes it from Wikidata in the background. This means existing Docker volumes receive newly bundled coasters without losing locally persisted data. Set `SYNC_ON_START=false` to disable automatic refreshes.

## API

- `GET /api/coasters?q=taron&country=Germany&limit=100&offset=0`
- `GET /api/parks?q=energylandia&country=Poland&limit=500&offset=0`
- `GET /api/search?q=stel+vengeance&limit=8` (ranked fuzzy suggestions)
- `GET /api/coasters/Q16665871`
- `GET /api/stats`

Records include height, track length, speed, opening date, park, country, manufacturer, capacity, inversions, coordinates, and source URL where Wikidata provides them. Missing source values are returned as `null`.

The API stores measurements in metric units; the web interface converts height and track length to feet for display.

## Data sources

- The bundled catalogue is derived from the [Roller Coaster Database dataset](https://www.kaggle.com/datasets/robikscube/rollercoaster-database), released under CC0 and originally collected from Wikipedia.
- `backend/import_cc0.py` reproduces the normalization from the downloaded `coaster_db.csv` file and can derive countries from public-domain Natural Earth boundaries.
- `backend/index_images.py` indexes representative photos and source pages through Wikipedia's public API.

Every coaster card also links to a targeted YouTube search for a front-seat POV using the ride and park names, avoiding stale hard-coded video IDs.

The Parks catalogue is derived from the coaster records and summarizes each park's indexed coaster count, tallest and fastest rides, opening-year span, and a representative indexed photo.
- `backend/sync_wikidata.py` adds or updates records from Wikidata through a configurable SPARQL endpoint.

The importer rejects implausible measurement outliers and never manufactures missing statistics.

## Pull the published image

After the first successful GitHub Actions run:

```bash
docker pull ghcr.io/simonbolton/rollercoaster-app:latest
docker run -d --name airtime-atlas -p 8080:8080 --restart unless-stopped ghcr.io/simonbolton/rollercoaster-app:latest
```

The workflow also publishes immutable `sha-*` tags and version tags such as `v1.0.0`.

## Local development

Run `python backend/server.py` from the repository root. Use `python backend/sync_wikidata.py` to refresh the local database manually.

import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", ROOT / "data" / "coasters.db"))
SEED_PATH = ROOT / "data" / "seed.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS coasters (
  wikidata_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  park TEXT,
  country TEXT,
  manufacturer TEXT,
  opened TEXT,
  height_m REAL,
  length_m REAL,
  speed_kmh REAL,
  capacity INTEGER,
  inversions INTEGER,
  image_url TEXT,
  latitude REAL,
  longitude REAL,
  source_url TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_coasters_name ON coasters(name);
CREATE INDEX IF NOT EXISTS idx_coasters_park ON coasters(park);
CREATE INDEX IF NOT EXISTS idx_coasters_country ON coasters(country);
"""

UPSERT = """
INSERT INTO coasters (
  wikidata_id, name, park, country, manufacturer, opened, height_m,
  length_m, speed_kmh, capacity, inversions, image_url, latitude,
  longitude, source_url, updated_at
) VALUES (
  :wikidata_id, :name, :park, :country, :manufacturer, :opened, :height_m,
  :length_m, :speed_kmh, :capacity, :inversions, :image_url, :latitude,
  :longitude, :source_url, CURRENT_TIMESTAMP
)
ON CONFLICT(wikidata_id) DO UPDATE SET
  name=excluded.name, park=excluded.park, country=excluded.country,
  manufacturer=excluded.manufacturer, opened=excluded.opened,
  height_m=excluded.height_m, length_m=excluded.length_m,
  speed_kmh=excluded.speed_kmh, capacity=excluded.capacity,
  inversions=excluded.inversions, image_url=excluded.image_url,
  latitude=excluded.latitude, longitude=excluded.longitude,
  source_url=excluded.source_url, updated_at=CURRENT_TIMESTAMP
"""


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(SCHEMA)
    return connection


def upsert_many(records):
    with connect() as connection:
        connection.executemany(UPSERT, records)
    return len(records)


def seed_catalogue():
    """Upsert the bundled catalogue so existing Docker volumes receive new records."""
    upsert_many(json.loads(SEED_PATH.read_text(encoding="utf-8")))

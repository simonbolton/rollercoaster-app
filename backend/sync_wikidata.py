import json
import argparse
import os
import time
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

from database import upsert_many

ENDPOINT = os.getenv("WIKIDATA_SPARQL_ENDPOINT", "https://qlever.dev/api/wikidata")
ID_QUERY = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?coaster WHERE {
  ?coaster wdt:P31 wd:Q204832.
}
ORDER BY ?coaster
LIMIT 5000
"""
DETAIL_QUERY = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?coaster ?coasterLabel ?parkLabel ?countryLabel
  ?manufacturerLabel ?opened ?height ?length ?speed ?capacity ?inversions
  ?image ?coordinates
WHERE {
  VALUES ?coaster { %s }
  ?coaster rdfs:label ?coasterLabel.
  FILTER(LANG(?coasterLabel) = "en")
  OPTIONAL { ?coaster wdt:P276 ?park. }
  OPTIONAL { ?park wdt:P17 ?country. }
  OPTIONAL { ?park rdfs:label ?parkLabel. FILTER(LANG(?parkLabel) = "en") }
  OPTIONAL { ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }
  OPTIONAL { ?coaster wdt:P176 ?manufacturer. }
  OPTIONAL { ?manufacturer rdfs:label ?manufacturerLabel. FILTER(LANG(?manufacturerLabel) = "en") }
  OPTIONAL { ?coaster wdt:P571 ?opened. }
  OPTIONAL { ?coaster wdt:P2048 ?height. }
  OPTIONAL { ?coaster wdt:P2043 ?length. }
  OPTIONAL { ?coaster wdt:P2052 ?speed. }
  OPTIONAL { ?coaster wdt:P1083 ?capacity. }
  OPTIONAL { ?coaster wdt:P2670 ?inversions. }
  OPTIONAL { ?coaster wdt:P18 ?image. }
  OPTIONAL { ?coaster wdt:P625 ?coordinates. }
}
"""


def value(binding, key, cast=None):
    raw = binding.get(key, {}).get("value")
    if raw is None:
        return None
    try:
        return cast(raw) if cast else raw
    except (TypeError, ValueError):
        return None


def parse_point(point):
    if not point or not point.startswith("Point("):
        return None, None
    longitude, latitude = point[6:-1].split()
    return float(latitude), float(longitude)


def fetch_query(query):
    body = query.encode("utf-8")
    request = urllib.request.Request(ENDPOINT, data=body, headers={
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/sparql-query; charset=utf-8",
        "User-Agent": "AirtimeAtlas/1.0 (https://github.com/simonbolton/rollercoaster-app)",
    })
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)["results"]["bindings"]
        except HTTPError as error:
            if error.code not in {429, 502, 503, 504} or attempt == 4:
                raise
            time.sleep(min(int(error.headers.get("Retry-After", "5")) * (attempt + 1), 45))


def fetch():
    ids = [value(row, "coaster").rsplit("/", 1)[-1] for row in fetch_query(ID_QUERY)]
    bindings = []
    for index in range(0, len(ids), 25):
        batch = ids[index:index + 25]
        query = DETAIL_QUERY % " ".join(f"wd:{wikidata_id}" for wikidata_id in batch)
        bindings.extend(fetch_query(query))
        print(f"Fetched {min(index + len(batch), len(ids))}/{len(ids)} entities", flush=True)
        time.sleep(1)
    return bindings


def normalize(bindings):
    records = {}
    for row in bindings:
        entity_url = value(row, "coaster")
        wikidata_id = entity_url.rsplit("/", 1)[-1]
        latitude, longitude = parse_point(value(row, "coordinates"))
        record = {
            "wikidata_id": wikidata_id,
            "name": value(row, "coasterLabel") or wikidata_id,
            "park": value(row, "parkLabel"),
            "country": value(row, "countryLabel"),
            "manufacturer": value(row, "manufacturerLabel"),
            "opened": (value(row, "opened") or "")[:10] or None,
            "height_m": value(row, "height", float),
            "length_m": value(row, "length", float),
            "speed_kmh": value(row, "speed", float),
            "capacity": value(row, "capacity", lambda x: int(float(x))),
            "inversions": value(row, "inversions", lambda x: int(float(x))),
            "image_url": value(row, "image"),
            "latitude": latitude,
            "longitude": longitude,
            "source_url": entity_url,
        }
        current = records.get(wikidata_id)
        if current is None or sum(v is not None for v in record.values()) > sum(v is not None for v in current.values()):
            records[wikidata_id] = record
    return list(records.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import rollercoasters from Wikidata")
    parser.add_argument("--write-seed", action="store_true", help="replace data/seed.json with the normalized catalogue")
    args = parser.parse_args()
    records = normalize(fetch())
    imported = upsert_many(records)
    if args.write_seed:
        seed_path = Path(__file__).resolve().parent.parent / "data" / "seed.json"
        seed_path.write_text(json.dumps(sorted(records, key=lambda item: item["name"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(records)} records to {seed_path}")
    print(f"Imported {imported} rollercoasters from Wikidata")

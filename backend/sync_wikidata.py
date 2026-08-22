import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError

from database import upsert_many

ENDPOINT = "https://query.wikidata.org/sparql"
QUERY = """
SELECT DISTINCT ?coaster ?coasterLabel ?parkLabel ?countryLabel
  ?manufacturerLabel ?opened ?height ?length ?speed ?capacity ?inversions
  ?image ?coordinates
WHERE {
  ?coaster wdt:P31 wd:Q204832.
  OPTIONAL { ?coaster wdt:P276 ?park. }
  OPTIONAL { ?park wdt:P17 ?country. }
  OPTIONAL { ?coaster wdt:P176 ?manufacturer. }
  OPTIONAL { ?coaster wdt:P571 ?opened. }
  OPTIONAL { ?coaster wdt:P2048 ?height. }
  OPTIONAL { ?coaster wdt:P2043 ?length. }
  OPTIONAL { ?coaster wdt:P2052 ?speed. }
  OPTIONAL { ?coaster wdt:P1083 ?capacity. }
  OPTIONAL { ?coaster wdt:P2670 ?inversions. }
  OPTIONAL { ?coaster wdt:P18 ?image. }
  OPTIONAL { ?coaster wdt:P625 ?coordinates. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 1000
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


def fetch():
    body = urllib.parse.urlencode({"query": QUERY, "format": "json"}).encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers={
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "User-Agent": "AirtimeAtlas/1.0 (https://github.com/simonbolton/rollercoaster-app)",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)["results"]["bindings"]
        except HTTPError as error:
            if error.code != 429 or attempt == 2:
                raise
            time.sleep(min(int(error.headers.get("Retry-After", "10")), 30))


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
    records = normalize(fetch())
    print(f"Imported {upsert_many(records)} rollercoasters from Wikidata")

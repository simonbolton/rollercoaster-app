import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

DATASET_URL = "https://www.kaggle.com/datasets/robikscube/rollercoaster-database"


def number(value):
    if not value:
        return None
    match = re.search(r"-?[\d,.]+", value.replace("\xa0", " "))
    if not match:
        return None
    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return None


def metric_from_text(value):
    if not value:
        return None
    metric = re.search(r"\(([\d,.]+)\s*m\)", value.replace("\xa0", " "), re.I)
    return number(metric.group(1)) if metric else None


def height_metres(row):
    metric = metric_from_text(row.get("Height"))
    if metric is not None:
        return metric
    height = number(row.get("height_value"))
    if height is None:
        return None
    return round(height * 0.3048, 2) if (row.get("height_unit") or "").lower() == "ft" else height


def speed_kmh(row):
    metric = re.search(r"([\d,.]+)\s*km/h", row.get("Speed") or "", re.I)
    if metric:
        return number(metric.group(1))
    mph = number(row.get("speed_mph"))
    return round(mph * 1.609344, 2) if mph is not None else None


def stable_id(row):
    identity = "|".join((row.get("coaster_name") or "", row.get("Location") or "", row.get("opening_date_clean") or ""))
    return "wiki-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]


def plausible(value, minimum, maximum):
    return value if value is not None and minimum <= value <= maximum else None


def point_in_ring(longitude, latitude, ring):
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        if (y1 > latitude) != (y2 > latitude):
            crossing = (x2 - x1) * (latitude - y1) / (y2 - y1) + x1
            if longitude < crossing:
                inside = not inside
        previous = current
    return inside


def load_countries(path):
    if not path:
        return []
    features = json.loads(path.read_text(encoding="utf-8"))["features"]
    countries = []
    for feature in features:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        countries.append((feature["properties"]["ADMIN"], feature.get("bbox"), polygons))
    return countries


def country_for(latitude, longitude, location, countries):
    if latitude is not None and longitude is not None:
        for name, bbox, polygons in countries:
            if bbox and not (bbox[0] <= longitude <= bbox[2] and bbox[1] <= latitude <= bbox[3]):
                continue
            if any(point_in_ring(longitude, latitude, polygon[0]) for polygon in polygons):
                return "United States" if name == "United States of America" else name
    location_folded = (location or "").casefold()
    for name, _, _ in countries:
        if name.casefold() in location_folded:
            return "United States" if name == "United States of America" else name
    return None


def normalize(row, countries):
    latitude, longitude = number(row.get("latitude")), number(row.get("longitude"))
    capacity = number(row.get("Capacity"))
    inversions = number(row.get("Inversions_clean"))
    return {
        "wikidata_id": stable_id(row),
        "name": (row.get("coaster_name") or "").strip(),
        "park": (row.get("Location") or "").strip() or None,
        "country": country_for(latitude, longitude, row.get("Location"), countries),
        "manufacturer": (row.get("Manufacturer") or "").strip() or None,
        "opened": (row.get("opening_date_clean") or "").strip() or None,
        "height_m": plausible(height_metres(row), 1, 250),
        "length_m": plausible(metric_from_text(row.get("Length")), 10, 10000),
        "speed_kmh": plausible(speed_kmh(row), 1, 300),
        "capacity": int(plausible(capacity, 1, 10000)) if plausible(capacity, 1, 10000) is not None else None,
        "inversions": int(plausible(inversions, 0, 20)) if plausible(inversions, 0, 20) is not None else None,
        "image_url": None,
        "image_source_url": None,
        "latitude": latitude,
        "longitude": longitude,
        "source_url": (row.get("Website") or "").strip() or DATASET_URL,
    }


def main():
    parser = argparse.ArgumentParser(description="Normalize the CC0 Wikipedia rollercoaster dataset")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "seed.json")
    parser.add_argument("--countries", type=Path, help="Natural Earth countries GeoJSON used for coordinate lookup")
    args = parser.parse_args()
    countries = load_countries(args.countries)
    with args.csv_path.open(encoding="utf-8-sig", newline="") as source:
        records_by_id = {}
        for row in csv.DictReader(source):
            if not (row.get("coaster_name") or "").strip():
                continue
            record = normalize(row, countries)
            current = records_by_id.get(record["wikidata_id"])
            if current is None or sum(value is not None for value in record.values()) > sum(value is not None for value in current.values()):
                records_by_id[record["wikidata_id"]] = record
        records = list(records_by_id.values())
    records.sort(key=lambda item: (item["name"].casefold(), item["park"] or ""))
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} worldwide coaster records to {args.output}")


if __name__ == "__main__":
    main()

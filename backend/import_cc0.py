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


def normalize(row):
    latitude, longitude = number(row.get("latitude")), number(row.get("longitude"))
    capacity = number(row.get("Capacity"))
    inversions = number(row.get("Inversions_clean"))
    return {
        "wikidata_id": stable_id(row),
        "name": (row.get("coaster_name") or "").strip(),
        "park": (row.get("Location") or "").strip() or None,
        "country": None,
        "manufacturer": (row.get("Manufacturer") or "").strip() or None,
        "opened": (row.get("opening_date_clean") or "").strip() or None,
        "height_m": plausible(height_metres(row), 1, 250),
        "length_m": plausible(metric_from_text(row.get("Length")), 10, 10000),
        "speed_kmh": plausible(speed_kmh(row), 1, 300),
        "capacity": int(plausible(capacity, 1, 10000)) if plausible(capacity, 1, 10000) is not None else None,
        "inversions": int(plausible(inversions, 0, 20)) if plausible(inversions, 0, 20) is not None else None,
        "image_url": None,
        "latitude": latitude,
        "longitude": longitude,
        "source_url": (row.get("Website") or "").strip() or DATASET_URL,
    }


def main():
    parser = argparse.ArgumentParser(description="Normalize the CC0 Wikipedia rollercoaster dataset")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "seed.json")
    args = parser.parse_args()
    with args.csv_path.open(encoding="utf-8-sig", newline="") as source:
        records_by_id = {}
        for row in csv.DictReader(source):
            if not (row.get("coaster_name") or "").strip():
                continue
            record = normalize(row)
            current = records_by_id.get(record["wikidata_id"])
            if current is None or sum(value is not None for value in record.values()) > sum(value is not None for value in current.values()):
                records_by_id[record["wikidata_id"]] = record
        records = list(records_by_id.values())
    records.sort(key=lambda item: (item["name"].casefold(), item["park"] or ""))
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} worldwide coaster records to {args.output}")


if __name__ == "__main__":
    main()

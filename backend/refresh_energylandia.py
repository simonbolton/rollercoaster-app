"""Refresh Energylandia records from the park's published roller-coaster list."""

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "seed.json"
PARK = "Energylandia"
COUNTRY = "Poland"
LATITUDE = 50.0019
LONGITUDE = 19.4031
LIST_URL = "https://energylandia.pl/en/attractions/rollercoasters/"


def key(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.lower())


# Statistics come from Energylandia's individual attraction pages. Opening dates
# are retained at day precision only where a published date is available.
RIDES = [
    ("Śmiejżelki Energuś", "Vekoma", "2015-05-01", 13, 335, 45, 20, None, "little-kids-zone/energus-roller-coaster/"),
    ("Circus Coaster", "Visa Rides", "2017-04-17", None, 32, 12, 16, None, "little-kids-zone/circus-coaster/"),
    ("RMF Dragon", "Vekoma", "2015-06-04", 20, 453, 75.6, 20, None, "family-zone/rmf-dragon-roller-coaster/"),
    ("Mars", "SBF Visa", "2014-01-01", 6, 150, 24.7, 24, None, "family-zone/mars-coaster/"),
    ("Happy Loops", "Visa Rides", "2017-01-01", 7, 90, 30, 16, None, "little-kids-zone/happy-loops/"),
    ("Draken", "Preston & Barbieri", "2019-07-20", 7.3, 140, 34.5, 20, None, "dragon-zone/draken/"),
    ("Frida", "Vekoma", "2019-07-20", 13, 247, 44.6, 16, None, "dragon-zone/frida/"),
    ("Frutti Loop", "SBF Visa", "2014-01-01", 3.7, 90, 20, 20, None, "family-zone/frutti-loop-coaster/"),
    ("Tidal Wave Twister", "Zamperla", "2021-01-01", None, 90, 51, 40, None, "aqualantis/tidal-wave-twister/"),
    ("Ekipa Light Explorers", "Vekoma", "2021-07-14", 24.2, 238, 60, None, None, "aqualantis/light-explorers/"),
    ("Abyssus", "Vekoma", "2021-07-14", 38.5, 1316, 99.9, None, 4, "aqualantis/abyssus/"),
    ("Boomerang", "Vekoma", "2018-01-01", 25, 200, 70, 20, None, "family-zone/boomerang/"),
    ("Zadra", "Rocky Mountain Construction", "2019-08-22", 62.8, 1316, 121, None, 3, "dragon-zone/zadra/"),
    ("Viking", "SBF Visa", "2014-07-14", 13, 320, 43, 4, None, "extreme-zone/viking-rollercoaster/"),
    ("Pepsi Hyperion", "Intamin", "2018-07-14", 77, 1450, 142, None, 2, "extreme-zone/hyperion/"),
    ("Mayan Zero Limitów", "Vekoma", "2015-09-12", 33.3, 689, 80, 20, 5, "extreme-zone/rollercoaster-mayan/"),
    ("Formuła", "Vekoma", "2016-06-25", 24.7, 560, 100, 16, 3, "extreme-zone/formula-1-roller-coaster/"),
    ("Speed", "Intamin", "2018-04-02", 60, None, 110, 10, None, "extreme-zone/water-coaster-speed/"),
    ("Honey Harbour", "Vekoma", "2024-04-27", 11.7, 254, 46, 20, None, "sweet-valley/honey-harbour/"),
    ("Choco Chip Creek", "Vekoma", "2024-04-27", 16.5, 1200, 55, 32, None, "sweet-valley/choco-chip-creek/"),
]

ALIASES = {
    "abyssus": "Abyssus",
    "formulaenergylandia": "Formuła",
    "hyperionrollercoaster": "Pepsi Hyperion",
    "zadrarollercoaster": "Zadra",
}


def main():
    catalogue = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    previous = {
        ALIASES.get(key(item["name"]), item["name"]): item
        for item in catalogue
        if (item.get("park") or "").casefold() == PARK.casefold()
    }
    catalogue = [
        item for item in catalogue
        if (item.get("park") or "").casefold() != PARK.casefold()
    ]

    for name, maker, opened, height, length, speed, capacity, inversions, path in RIDES:
        old = previous.get(name, {})
        catalogue.append({
            "wikidata_id": old.get("wikidata_id", f"energylandia-{key(name)}"),
            "name": name,
            "park": PARK,
            "country": COUNTRY,
            "manufacturer": maker,
            "opened": opened,
            "height_m": height,
            "length_m": length,
            "speed_kmh": speed,
            "capacity": capacity,
            "inversions": inversions,
            "image_url": old.get("image_url"),
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "source_url": f"https://energylandia.pl/en/attractions/{path}",
            "image_source_url": old.get("image_source_url"),
        })

    catalogue.sort(key=lambda item: (item["name"].casefold(), item["wikidata_id"]))
    SEED_PATH.write_text(
        json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Energylandia refreshed: {len(RIDES)} rides; catalogue: {len(catalogue)}")
    print(f"Official list: {LIST_URL}")


if __name__ == "__main__":
    main()

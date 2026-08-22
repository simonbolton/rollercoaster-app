import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://en.wikipedia.org/w/api.php"


def request_pages(titles):
    query = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "redirects": "1",
        "prop": "pageimages|info",
        "piprop": "original",
        "inprop": "url",
        "titles": "|".join(titles),
    })
    request = urllib.request.Request(f"{API}?{query}", headers={
        "User-Agent": "AirtimeAtlas/1.0 (https://github.com/simonbolton/rollercoaster-app)",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["query"]


def main():
    parser = argparse.ArgumentParser(description="Index representative coaster images from Wikipedia")
    parser.add_argument("seed", type=Path, nargs="?", default=Path(__file__).resolve().parent.parent / "data" / "seed.json")
    args = parser.parse_args()
    records = json.loads(args.seed.read_text(encoding="utf-8"))
    for record in records:
        record.setdefault("image_source_url", None)
    by_title = {record["name"]: record for record in records}
    titles = list(by_title)
    indexed = 0
    for offset in range(0, len(titles), 40):
        batch = titles[offset:offset + 40]
        result = request_pages(batch)
        aliases = {item["from"]: item["to"] for item in result.get("normalized", [])}
        aliases.update({item["from"]: item["to"] for item in result.get("redirects", [])})
        page_by_title = {page.get("title"): page for page in result.get("pages", [])}
        for title in batch:
            resolved = title
            while resolved in aliases:
                resolved = aliases[resolved]
            page = page_by_title.get(resolved, {})
            image = page.get("original", {}).get("source")
            if image:
                by_title[title]["image_url"] = image
                by_title[title]["image_source_url"] = page.get("fullurl")
                indexed += 1
        print(f"Checked {min(offset + len(batch), len(titles))}/{len(titles)} titles", flush=True)
        time.sleep(0.25)
    args.seed.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed images for {indexed}/{len(records)} coasters")


if __name__ == "__main__":
    main()

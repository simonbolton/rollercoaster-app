import json
import mimetypes
import os
import sqlite3
from difflib import SequenceMatcher
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from database import connect, seed_catalogue

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv("PORT", "8080"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=60")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return self.send_json({"status": "healthy"})
        if parsed.path == "/api/coasters":
            return self.list_coasters(parse_qs(parsed.query))
        if parsed.path == "/api/search":
            return self.search_coasters(parse_qs(parsed.query))
        if parsed.path == "/api/stats":
            return self.stats()
        if parsed.path.startswith("/api/coasters/"):
            return self.get_coaster(parsed.path.rsplit("/", 1)[-1])
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def list_coasters(self, params):
        search = params.get("q", [""])[0].strip()
        country = params.get("country", [""])[0].strip()
        limit = min(max(int(params.get("limit", ["100"])[0]), 1), 500)
        offset = max(int(params.get("offset", ["0"])[0]), 0)
        where, values = [], []
        if search:
            where.append("(name LIKE ? OR park LIKE ? OR manufacturer LIKE ?)")
            values.extend([f"%{search}%"] * 3)
        if country:
            where.append("country = ?")
            values.append(country)
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        with connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM coasters {clause}", values).fetchone()[0]
            rows = connection.execute(
                f"SELECT * FROM coasters {clause} ORDER BY name LIMIT ? OFFSET ?",
                [*values, limit, offset],
            ).fetchall()
        self.send_json({"total": total, "limit": limit, "offset": offset, "items": [dict(row) for row in rows]})

    def get_coaster(self, wikidata_id):
        with connect() as connection:
            row = connection.execute("SELECT * FROM coasters WHERE wikidata_id = ?", (wikidata_id,)).fetchone()
        self.send_json(dict(row) if row else {"error": "Coaster not found"}, 200 if row else 404)

    def search_coasters(self, params):
        query = params.get("q", [""])[0].strip().casefold()
        limit = min(max(int(params.get("limit", ["8"])[0]), 1), 20)
        if len(query) < 2:
            return self.send_json({"query": query, "items": []})

        with connect() as connection:
            rows = connection.execute("SELECT * FROM coasters").fetchall()

        ranked = []
        fields = (("name", 1.0), ("park", 0.86), ("manufacturer", 0.76), ("country", 0.68))
        for row in rows:
            best_score, matched_on = 0.0, "name"
            for field, weight in fields:
                candidate = (row[field] or "").casefold()
                if not candidate:
                    continue
                similarity = SequenceMatcher(None, query, candidate).ratio()
                if query in candidate:
                    similarity = max(similarity, 0.96 if candidate.startswith(query) else 0.9)
                else:
                    similarity = max(similarity, *(SequenceMatcher(None, query, word).ratio() for word in candidate.split()))
                score = similarity * weight
                if score > best_score:
                    best_score, matched_on = score, field
            if best_score >= 0.38:
                item = dict(row)
                item["match_score"] = round(best_score, 3)
                item["matched_on"] = matched_on
                ranked.append(item)

        ranked.sort(key=lambda item: (-item["match_score"], item["name"]))
        self.send_json({"query": query, "items": ranked[:limit]})

    def stats(self):
        with connect() as connection:
            row = connection.execute("""
              SELECT COUNT(*) AS coasters, COUNT(DISTINCT country) AS countries,
                     COUNT(DISTINCT park) AS parks, MAX(height_m) AS tallest_m,
                     MAX(speed_kmh) AS fastest_kmh
              FROM coasters
            """).fetchone()
        self.send_json(dict(row))

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    mimetypes.add_type("text/javascript", ".js")
    seed_catalogue()
    print(f"Airtime Atlas listening on http://0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

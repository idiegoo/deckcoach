"""
Local Scryfall card database from bulk data.
Downloads oracle_cards once, stores in SQLite for zero-RAM lookups.
Auto-refreshes every 7 days.
"""
import json
import os
import time
import gzip
import sqlite3
import requests
from typing import Optional, Dict, List

DB_DIR = os.environ.get("DECKCOACH_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_FILE = os.path.join(DB_DIR, "scryfall.db")
REFRESH_SECONDS = 7 * 86400


class CardDatabase:
    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        self._loaded = False

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            os.makedirs(DB_DIR, exist_ok=True)
            self._conn = sqlite3.connect(DB_FILE)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_loaded(self):
        if self._loaded:
            return

        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                name TEXT PRIMARY KEY,
                lower_name TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lower_name ON cards(lower_name)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        row = conn.execute("SELECT value FROM meta WHERE key = 'count'").fetchone()
        if row and int(row["value"]) > 0 and not self.should_refresh():
            self._loaded = True
            count = int(row["value"])
            print(f"[CardDB] SQLite ready: {count} cards")
            return

        self._download_and_build()

    def _download_and_build(self):
        print("[CardDB] Downloading Scryfall bulk data (~23MB)...")
        conn = self._get_conn()

        try:
            resp = requests.get(
                "https://api.scryfall.com/bulk-data",
                timeout=15,
                headers={"User-Agent": "DeckCoach/1.0", "Accept": "application/json"},
            )
            resp.raise_for_status()
            bulk_list = resp.json()

            oracle_entry = None
            for entry in bulk_list.get("data", []):
                if entry.get("type") == "oracle_cards":
                    oracle_entry = entry
                    break

            if not oracle_entry:
                print("[CardDB] oracle_cards bulk not found, falling back to API lookups")
                self._loaded = True
                return

            download_url = oracle_entry.get("jsonl_download_uri") or oracle_entry.get("download_uri")
            if not download_url:
                print("[CardDB] No download URL found")
                self._loaded = True
                return

            updated_at = oracle_entry.get("updated_at", "")

            # Download and parse
            print(f"[CardDB] Downloading...")
            resp = requests.get(
                download_url,
                timeout=300,
                stream=True,
                headers={"User-Agent": "DeckCoach/1.0"},
            )
            resp.raise_for_status()

            print("[CardDB] Parsing bulk data into SQLite...")
            conn.execute("DELETE FROM cards")
            conn.execute("DELETE FROM meta")

            decompressor = gzip.GzipFile(fileobj=resp.raw)
            count = 0
            batch = []
            batch_size = 5000

            for line in decompressor:
                line = line.strip()
                if not line:
                    continue
                try:
                    card = json.loads(line)
                    name = card.get("name", "")
                    if name:
                        data = json.dumps({
                            "name": name,
                            "cmc": card.get("cmc"),
                            "colors": card.get("colors"),
                            "color_identity": card.get("color_identity"),
                            "type_line": card.get("type_line"),
                            "oracle_text": card.get("oracle_text", ""),
                            "mana_cost": card.get("mana_cost") or (
                                (card.get("card_faces") or [{}])[0].get("mana_cost")
                                if card.get("card_faces") else None
                            ),
                            "layout": card.get("layout"),
                            "image_uris": card.get("image_uris") or None,
                            "card_faces": card.get("card_faces"),
                        })
                        # Store back face image for DFCs
                        faces = card.get("card_faces")
                        if faces and len(faces) >= 2:
                            back_uris = faces[1].get("image_uris")
                            if back_uris:
                                d = json.loads(data)
                                d["image_uris_back"] = back_uris
                                data = json.dumps(d)

                        batch.append((name, name.lower(), data))

                        # Also index front-face name for DFCs
                        if " // " in name:
                            front = name.split(" // ")[0]
                            batch.append((front, front.lower(), data))

                        count += 1

                        if len(batch) >= batch_size:
                            conn.executemany(
                                "INSERT OR REPLACE INTO cards (name, lower_name, data) VALUES (?, ?, ?)",
                                batch
                            )
                            batch = []
                except json.JSONDecodeError:
                    pass

            if batch:
                conn.executemany(
                    "INSERT OR REPLACE INTO cards (name, lower_name, data) VALUES (?, ?, ?)",
                    batch
                )
                batch = []

            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('count', ?)", (str(count),))
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updated_at', ?)", (updated_at,))
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('built_at', ?)", (str(time.time()),))
            conn.commit()

            self._loaded = True
            print(f"[CardDB] Database built: {count} cards")

        except Exception as e:
            print(f"[CardDB] Download failed: {e}, falling back to API lookups")
            self._loaded = True

    def get_card(self, name: str) -> Optional[dict]:
        self._ensure_loaded()
        row = self._get_conn().execute(
            "SELECT data FROM cards WHERE name = ?", (name,)
        ).fetchone()
        return json.loads(row["data"]) if row else None

    def get_cards(self, names: List[str]) -> Dict[str, Optional[dict]]:
        self._ensure_loaded()
        results: Dict[str, Optional[dict]] = {}
        conn = self._get_conn()
        # SQLite IN clause with parameterized query
        placeholders = ",".join("?" for _ in names)
        rows = conn.execute(
            f"SELECT name, data FROM cards WHERE name IN ({placeholders})",
            names
        ).fetchall()
        found = {r["name"]: json.loads(r["data"]) for r in rows}
        for name in names:
            results[name] = found.get(name)
        return results

    def fuzzy_get(self, name: str) -> Optional[dict]:
        self._ensure_loaded()
        row = self._get_conn().execute(
            "SELECT data FROM cards WHERE lower_name = ?", (name.lower(),)
        ).fetchone()
        if row:
            return json.loads(row["data"])
        return None

    def should_refresh(self) -> bool:
        conn = self._get_conn()
        row = conn.execute("SELECT value FROM meta WHERE key = 'built_at'").fetchone()
        if not row:
            return True
        try:
            return (time.time() - float(row["value"])) > REFRESH_SECONDS
        except Exception:
            return True


_card_db: Optional[CardDatabase] = None


def get_card_db() -> CardDatabase:
    global _card_db
    if _card_db is None:
        _card_db = CardDatabase()
    return _card_db

"""
Local Scryfall card database from bulk data.
Downloads oracle_cards once and serves lookups with zero HTTP requests.
Auto-refreshes every 7 days.
"""
import json
import os
import time
import gzip
import shutil
import requests
from typing import Optional, Dict, List

DB_DIR = os.environ.get("DECKCOACH_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_FILE = os.path.join(DB_DIR, "scryfall_db.json")
META_FILE = os.path.join(DB_DIR, "scryfall_db_meta.json")
REFRESH_SECONDS = 7 * 86400  # 7 days


class CardDatabase:
    def __init__(self):
        self._cards: Dict[str, dict] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        if os.path.exists(DB_FILE):
            self._load_from_disk()
        else:
            self._download_and_build()

    def _load_from_disk(self):
        print("[CardDB] Loading local database...")
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self._cards = json.load(f)
            self._loaded = True
            print(f"[CardDB] Loaded {len(self._cards)} cards from disk")
        except Exception as e:
            print(f"[CardDB] Failed to load from disk: {e}")
            self._download_and_build()

    def _download_and_build(self):
        print("[CardDB] Downloading Scryfall bulk data (~23MB)...")

        os.makedirs(DB_DIR, exist_ok=True)

        try:
            # Get bulk data info
            resp = requests.get(
                "https://api.scryfall.com/bulk-data",
                timeout=15,
                headers={"User-Agent": "DeckCoach/1.0", "Accept": "application/json"},
            )
            resp.raise_for_status()
            bulk_list = resp.json()

            # Find oracle_cards entry
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

            # Download the gzipped bulk file
            print(f"[CardDB] Downloading from {download_url}")
            resp = requests.get(
                download_url,
                timeout=300,
                stream=True,
                headers={"User-Agent": "DeckCoach/1.0"},
            )
            resp.raise_for_status()

            # Decompress and parse JSON Lines
            print("[CardDB] Parsing bulk data...")
            cards = {}
            # Scryfall bulk data is gzipped JSON Lines
            decompressor = gzip.GzipFile(fileobj=resp.raw)
            count = 0
            for line in decompressor:
                line = line.strip()
                if not line:
                    continue
                try:
                    card = json.loads(line)
                    name = card.get("name", "")
                    if name:
                        data = {
                            "name": name,
                            "cmc": card.get("cmc"),
                            "colors": card.get("colors"),
                            "color_identity": card.get("color_identity"),
                            "type_line": card.get("type_line"),
                            "oracle_text": card.get("oracle_text", ""),
                            "mana_cost": card.get("mana_cost") or ((card.get("card_faces") or [{}])[0].get("mana_cost") if card.get("card_faces") else None),
                            "layout": card.get("layout"),
                        }
                        # Only store image_uris if present (single-faced cards)
                        if card.get("image_uris"):
                            data["image_uris"] = card["image_uris"]
                        # Store card_faces for DFCs
                        faces = card.get("card_faces")
                        if faces and isinstance(faces, list):
                            data["card_faces"] = faces
                            if len(faces) >= 2:
                                face_data = faces[1].get("image_uris")
                                if face_data:
                                    data["image_uris_back"] = face_data
                        cards[name] = data
                        # For double-faced cards, also index by front face name
                        if " // " in name:
                            front = name.split(" // ")[0]
                            if front not in cards:
                                cards[front] = data
                        count += 1
                except json.JSONDecodeError:
                    pass

            print(f"[CardDB] Parsed {count} cards")

            # Save to disk
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(cards, f, ensure_ascii=False)

            # Save metadata
            with open(META_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "updated_at": oracle_entry.get("updated_at"),
                    "count": count,
                    "built_at": time.time(),
                }, f)

            self._cards = cards
            self._loaded = True
            print(f"[CardDB] Database built: {count} cards")

        except Exception as e:
            print(f"[CardDB] Download failed: {e}, falling back to API lookups")
            self._loaded = True

    def get_card(self, name: str) -> Optional[dict]:
        """Exact name lookup (case-sensitive)."""
        self._ensure_loaded()
        return self._cards.get(name)

    def get_cards(self, names: List[str]) -> Dict[str, Optional[dict]]:
        """Batch lookup by exact name."""
        self._ensure_loaded()
        results = {}
        for name in names:
            results[name] = self._cards.get(name)
        return results

    def fuzzy_get(self, name: str) -> Optional[dict]:
        """Case-insensitive + normalize lookup."""
        self._ensure_loaded()
        if name in self._cards:
            return self._cards[name]
        # Try lowercased match
        lower = name.lower()
        for n, data in self._cards.items():
            if n.lower() == lower:
                return data
        return None

    def should_refresh(self) -> bool:
        if not os.path.exists(META_FILE):
            return True
        try:
            with open(META_FILE, "r") as f:
                meta = json.load(f)
            return (time.time() - meta.get("built_at", 0)) > REFRESH_SECONDS
        except Exception:
            return True


# Singleton
_card_db: Optional[CardDatabase] = None


def get_card_db() -> CardDatabase:
    global _card_db
    if _card_db is None:
        _card_db = CardDatabase()
    return _card_db

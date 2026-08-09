import requests
import time
import json
import os
from typing import List, Optional, Dict
from .models import Card

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "scryfall_cache.json")

class ScryfallClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "DeckCoach/1.0 (https://github.com/deckcoach; deckcoach@example.com)",
            "Accept": "application/json"
        })
        self.cache: Dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
        except Exception:
            self.cache = {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _normalize_name(self, name: str) -> str:
        # Remove comments/set codes after // for split cards, use front face
        name = name.strip()
        if " // " in name:
            name = name.split(" // ")[0]
        return name

    def get_cards(self, names: List[str]) -> Dict[str, Optional[dict]]:
        results = {}
        to_fetch = []
        for n in names:
            key = self._normalize_name(n)
            if key in self.cache:
                results[key] = self.cache[key]
            else:
                to_fetch.append(key)

        if to_fetch:
            print(f"[Scryfall] Fetching {len(to_fetch)} unique cards...")

        # Scryfall collection endpoint allows max 75 identifiers per request
        chunk_size = 75
        for i in range(0, len(to_fetch), chunk_size):
            chunk = to_fetch[i:i+chunk_size]
            identifiers = [{"name": n} for n in chunk]
            try:
                resp = self.session.post(
                    "https://api.scryfall.com/cards/collection",
                    json={"identifiers": identifiers},
                    timeout=30
                )
            except Exception as e:
                print(f"[Scryfall] Connection error: {e}")
                for n in chunk:
                    results[n] = None
                # Don't cache failures - retry next time
                continue

            time.sleep(0.1)  # be polite
            if resp.status_code != 200:
                print(f"[Scryfall] Bulk endpoint returned {resp.status_code}: {resp.text[:200]}")
                # fallback to individual requests, results from _fetch_single are not cached on failure
                for n in chunk:
                    results[n] = self._fetch_single(n)
                continue
            data = resp.json()
            found = len(data.get("data", []))
            not_found = len(data.get("not_found", []))
            print(f"[Scryfall] Found {found}, not found {not_found}")
            for card in data.get("data", []):
                key = self._normalize_name(card.get("name", ""))
                self.cache[key] = card
                results[key] = card
            for err in data.get("not_found", []):
                key = err.get("name", "")
                self.cache[key] = None
                results[key] = None

        self._save_cache()
        return results

    def _fetch_single(self, name: str) -> Optional[dict]:
        try:
            resp = self.session.get(
                "https://api.scryfall.com/cards/named",
                params={"exact": name},
                timeout=10
            )
            time.sleep(0.1)
            if resp.status_code == 200:
                card = resp.json()
                self.cache[name] = card
                return card
            else:
                # Don't cache failures - retry next time
                return None
        except Exception:
            return None

    def to_card_model(self, name: str, quantity: int, raw: Optional[dict]) -> Card:
        if not raw:
            return Card(name=name, quantity=quantity)
        image = None
        if "image_uris" in raw:
            image = raw["image_uris"].get("normal")
        elif "card_faces" in raw and raw["card_faces"]:
            image = raw["card_faces"][0].get("image_uris", {}).get("normal")

        return Card(
            name=name,
            quantity=quantity,
            cmc=raw.get("cmc"),
            colors=raw.get("colors"),
            color_identity=raw.get("color_identity"),
            type_line=raw.get("type_line"),
            oracle_text=raw.get("oracle_text", ""),
            image_url=image,
            mana_cost=raw.get("mana_cost")
        )

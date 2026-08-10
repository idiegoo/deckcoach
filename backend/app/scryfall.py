import requests
import time
import json
import os
import threading
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
        self._db = None
        self._db_init_lock = threading.Lock()

    def _get_local_db(self):
        if self._db is not None:
            return self._db
        with self._db_init_lock:
            if self._db is not None:
                return self._db
            try:
                from .card_db import get_card_db
                self._db = get_card_db()
                self._db._ensure_loaded()
            except Exception as e:
                print(f"[Scryfall] Local DB init failed: {e}, using API only")
                self._db = False
            return self._db

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
        name = name.strip()
        if " // " in name:
            name = name.split(" // ")[0]
        return name

    def _rate_limit_wait(self):
        time.sleep(0.15)

    def _request_with_retry(self, method, url, timeout=10, **kwargs):
        for attempt in range(2):
            try:
                if method == "POST":
                    resp = self.session.post(url, timeout=timeout, **kwargs)
                else:
                    resp = self.session.get(url, timeout=timeout, **kwargs)
                self._rate_limit_wait()

                if resp.status_code == 429:
                    wait = min(3 * (attempt + 1), 10)
                    print(f"[Scryfall] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    time.sleep(1)
                    continue
                return resp
            except Exception as e:
                if attempt == 0:
                    time.sleep(1)
                    continue
                print(f"[Scryfall] Connection error: {e}")
        return None

    def get_cards(self, names: List[str]) -> Dict[str, Optional[dict]]:
        results = {}
        to_fetch = []
        for n in names:
            key = self._normalize_name(n)
            if key in self.cache:
                results[key] = self.cache[key]
            else:
                to_fetch.append(key)

        if not to_fetch:
            return results

        # Try local database first (instant, no HTTP)
        db = self._get_local_db()
        if db:
            local_results = db.get_cards(to_fetch)
            still_missing = []
            for name in to_fetch:
                card = local_results.get(name)
                if not card:
                    # Try fuzzy in local DB too
                    card = db.fuzzy_get(name)
                if card:
                    self.cache[name] = card
                    results[name] = card
                else:
                    still_missing.append(name)

            if not still_missing:
                print(f"[Scryfall] All {len(to_fetch)} cards resolved from local DB")
                self._save_cache()
                return results

            print(f"[Scryfall] Local DB: {len(to_fetch) - len(still_missing)}/{len(to_fetch)} found, {len(still_missing)} need API")
            to_fetch = still_missing

        # Fall back to API for remaining cards
        if to_fetch:
            self._api_resolve(to_fetch, results)
        else:
            self._save_cache()

        return results

    def _api_resolve(self, to_fetch: List[str], results: Dict[str, Optional[dict]]):
        print(f"[Scryfall] API fetching {len(to_fetch)} unique cards...")

        chunk_size = 75
        unresolved = []

        for i in range(0, len(to_fetch), chunk_size):
            chunk = to_fetch[i:i+chunk_size]
            identifiers = [{"name": n} for n in chunk]

            resp = self._request_with_retry(
                "POST",
                "https://api.scryfall.com/cards/collection",
                timeout=30,
                json={"identifiers": identifiers},
            )

            if resp is None or resp.status_code != 200:
                for n in chunk:
                    results[n] = None
                continue

            data = resp.json()
            found = data.get("data", [])
            not_found = data.get("not_found", [])
            print(f"[Scryfall] Chunk {i//chunk_size + 1}: found {len(found)}, not found {len(not_found)}")

            for card in found:
                key = self._normalize_name(card.get("name", ""))
                self.cache[key] = card
                results[key] = card

            for err in not_found:
                unresolved.append(err.get("name", ""))

        if unresolved:
            print(f"[Scryfall] Fuzzy-resolving {len(unresolved)} not-found cards...")
            for name in unresolved:
                card = self._fuzzy_lookup(name)
                if card:
                    self.cache[name] = card
                    results[name] = card
                else:
                    self.cache[name] = None
                    results[name] = None

        self._save_cache()

    def _fuzzy_lookup(self, name: str) -> Optional[dict]:
        resp = self._request_with_retry(
            "GET",
            "https://api.scryfall.com/cards/named",
            timeout=10,
            params={"fuzzy": name},
        )
        if resp and resp.status_code == 200:
            card = resp.json()
            print(f"[Scryfall] Fuzzy: '{name}' → '{card.get('name', '?')}'")
            return card
        return None

    def _fetch_single(self, name: str) -> Optional[dict]:
        return self._fuzzy_lookup(name)

    def to_card_model(self, name: str, quantity: int, raw: Optional[dict]) -> Card:
        if not raw:
            return Card(name=name, quantity=quantity)
        image = None
        image_back = None
        if raw.get("image_uris"):
            image = raw["image_uris"].get("normal")
        elif raw.get("card_faces"):
            faces = raw["card_faces"]
            if len(faces) >= 2:
                image = faces[0].get("image_uris", {}).get("normal")
                image_back = faces[1].get("image_uris", {}).get("normal")
            elif faces:
                image = faces[0].get("image_uris", {}).get("normal")

        return Card(
            name=name,
            quantity=quantity,
            cmc=raw.get("cmc"),
            colors=raw.get("colors"),
            color_identity=raw.get("color_identity"),
            type_line=raw.get("type_line"),
            oracle_text=raw.get("oracle_text", ""),
            image_url=image,
            image_url_back=image_back,
            mana_cost=raw.get("mana_cost") or ((raw.get("card_faces") or [{}])[0].get("mana_cost") if raw.get("card_faces") else None),
        )

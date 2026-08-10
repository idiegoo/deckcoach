import requests
import re
import time
import json
import os
from typing import Dict, Optional, List, Tuple

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "edhrec")
CACHE_TTL = 86400  # 24 hours


def _commander_to_slug(name: str) -> str:
    """Convert commander name to EDHREC URL slug."""
    slug = name.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


def _cache_path(slug: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{slug}.json")


def _load_cache(slug: str) -> Optional[dict]:
    path = _cache_path(slug)
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > CACHE_TTL:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(slug: str, data: dict):
    path = _cache_path(slug)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def get_edhrec_data(commander_name: str) -> Optional[dict]:
    """Fetch EDHREC data for a commander. Returns None on failure. Uses 24h cache."""
    slug = _commander_to_slug(commander_name)

    cached = _load_cache(slug)
    if cached:
        return cached

    url = f"https://json.edhrec.com/pages/commanders/{slug}.json"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "DeckCoach/1.0 (https://github.com/deckcoach; deckcoach@example.com)"
        })
        if resp.status_code == 200:
            data = resp.json()
            _save_cache(slug, data)
            return data
        else:
            print(f"[EDHREC] HTTP {resp.status_code} for {url}")
            return None
    except Exception as e:
        print(f"[EDHREC] Connection error: {e}")
        return None


def get_tag_counts(commander_name: str) -> Dict[str, int]:
    """Extract and return tag_counts for a commander. Empty dict on failure."""
    data = get_edhrec_data(commander_name)
    if not data:
        return {}
    tc = data.get("tag_counts", {})
    if isinstance(tc, dict):
        return {k: v for k, v in tc.items() if isinstance(v, (int, float))}
    return {}


# Mapping from EDHREC tag names to our internal archetype names
# EDHREC name → internal name (None = skip this tag)
EDHREC_TAG_MAP: Dict[str, Optional[str]] = {
    "Tokens": "Tokens",
    "+1/+1 Counters": "+1/+1 Counters",
    "Artifacts": "Artifacts",
    "Combo": "cEDH / Combo",
    "Aggro": "Aggro",
    "Lifegain": "Lifegain",
    "Spellslinger": "Spellslinger",
    "Reanimator": "Reanimator",
    "Aristocrats": "Aristocrats",
    "Lands Matter": "Lands / Landfall",
    "Control": "Control / Stax",
    "Burn": "Burn",
    "Equipment": "Equipment",
    "Ramp": "Big Mana",
    "Enchantress": "Enchantress",
    "Voltron": "Voltron",
    "Midrange": "General / Midrange",
    "Mill": "Mill",
    "Treasure": "Treasure",
    "cEDH": "cEDH / Combo",
    "Sacrifice": "Sacrifice",
    "Blink": "Blink / ETB",
    "Wheels": "Wheels",
    "Auras": "Auras",
    "Legends": "Historic",
    "Discard": "Discard",
    "Graveyard": "Graveyard",
    "Clones": "Clones",
    "Flying": "Flying",
    "Card Draw": None,  # Not an archetype, skip
    "Landfall": "Lands / Landfall",
    "Group Slug": "Group Slug",
    "Stax": "Control / Stax",
    "Historic": "Historic",
    "Storm": "Storm",
    "Infect": "Infect",
    "Extra Combats": "+ExtrA TurnS",
    "Big Mana": "Big Mana",
    "Theft": "Theft",
    "Self-Mill": "Self-Mill",
    "Good Stuff": None,  # Skip, too generic
    "Group Hug": "Group Hug",
    "Birthing Pod": "Toolbox",
    "Chaos": "Chaos",
    "Planeswalkers": "Superfriends",
    "Forced Combat": "Forced Combat",
    "Vehicles": "Vehicles",
    "X Spells": "X Spells",
    "Commander Matters": None,  # Skip
    "Cantrips": "Cantrips",
    "Exile": "Exile",
    "Toolbox": "Toolbox",
    "Cascade": "Cascade / Discover",
    "Lifedrain": "Lifedrain",
    "-1/-1 Counters": "-1/-1 Counters",
    "Pillow Fort": "Pillow Fort",
    "Hatebears": "Hatebears",
    "Topdeck": "Topdeck",
    "Tempo": None,  # Skip, play pattern not archetype
    "Toughness Matters": "Toughness Matters",
    "Spell Copy": "Spell Copy",
    "Extra Turns": "+ExtrA TurnS",
    "Stompy": "Stompy",
    "Dredge": "Dredge",
    "ETB": "Blink / ETB",
    "Energy": "Energy",
    "Ninjutsu": "Ninjutsu",
    "Self-Damage": "Self-Damage",
    "Proliferate": "Proliferate",
    "Populate": None,  # Subset of tokens
    "Sagas": "Sagas",
    "Land Destruction": "Land Destruction",
    "Attack Triggers": None,  # Skip
    "Affinity": "Artifacts",
    "Food": "Food",
    "Clues": "Clues / Investigate",
    "Monarch": "Monarch",
    "Defenders": "Defenders",
    "Morph": "Morph / Manifest",
    "Cycling": "Cycling",
    "Counterspells": None,  # Subset of interaction
    "Deathtouch": None,  # Skip
    "Anthems": "Weenies",
    "Snow": None,  # Skip
    "Devotion": None,  # Skip
    "Pingers": "Pingers",
    "Politics": "Politics / Voting",
    "Tap / Untap": "Tap / Untap",
    "Activated Abilities": "Activated Abilities",
    "Mutate": "Mutate",
    "Prowess": "Prowess",
    "Unnatural": None,  # Skip
    "Modified Creatures": "Modified Creatures",
    "Dungeon": "Dungeon / Venture",
    "Unblockable": "Unblockable",
    "Discover": "Cascade / Discover",
    "Fight": "Fight",
    "Flash": "Flash",
    "Flashback": None,  # Skip
    "Bounce": "Bounce",
    "Weenies": "Weenies",
    "Power Matters": "Power Matters",
    "Eggs": "Eggs",
    "Adventures": "Adventures",
    "Shrines": "Shrines",
    "Impulse Draw": "Impulse Draw",
    "Modular": "Modular",
    "Coin Flip": "Coin Flip",
    "Scry": "Scry",
    "Guildgates": "Guildgates",
    "Surveil": "Surveil",
    "Polymorph": "Polymorph",
    "Glass Cannon": "Glass Cannon",
    "Creatureless": "Creatureless",
    "Hellbent": "Hellbent",
    "Suspend": "Suspend",
    # Tribal tags map to specific archetypes
    "Dragons": "Dragons",
    "Goblins": "Goblins",
    "Elves": "Elves",
    "Zombies": "Zombies",
    "Slivers": "Slivers",
    "Eldrazi": "Eldrazi",
    "Dinos": "Dinos",
    "Angels": None,  # Falls under Tribal/Typal general
    "Demons": None,
    "Cats": None,
    "Vampires": None,
    "Humans": None,
    "Merfolk": None,
    "Pirates": None,
    "Knights": None,
    "Rats": None,  # Rat Colony is too specific
    "Spirits": None,
    "Wizards": None,
    "Warriors": None,
    "Squirrels": None,
    "Birds": None,
    "Faeries": None,
    "Druids": None,
    "Sphinxes": None,
    "Gods": None,
    "Phoenixes": None,
    "Hydras": None,
    "Dinosaurs": "Dinos",
    "Samurai": None,
    "Ninjas": None,
    "Constructs": None,
    "Phyrexians": None,
    "Horrors": None,
    "Kithkin": None,
    "Clerics": None,
    "Shamans": None,
    "Minotaurs": None,
    "Gorgons": None,
    "Monks": None,
    "Golems": None,
    "Allies": None,
    "Scarecrows": None,
    "Myr": None,
    "Sea Creatures": None,
    "Beasts": None,
    "Frogs": None,
    "Oozes": None,
    "Fungi": None,
    "Spiders": None,
    "Saprolings": None,
    "Snakes": None,
    "Wolves": None,
    "Werewolves": None,
    "Treefolk": None,
    "Giants": None,
    "Wurms": None,
    "Griffins": None,
    "Lhurgoyfs": None,
    "Illusions": None,
    "Atogs": None,
    "Mutants": None,
    "Rabbits": None,
    "Mice": None,
    "Otters": None,
    "Lizards": None,
    "Dwarves": None,
    "Bears": None,
    "Apes": None,
    "Raccoons": None,
    "Turtles": None,
    "Bats": None,
    "Crabs": None,
    "Dogs": None,
    "Horses": None,
    "Unicorns": None,
    "Foxes": None,
    "Badgers": None,
    "Moles": None,
    "Goats": None,
    "Sheep": None,
    "Insects": None,
    "Mammoths": None,
}


def edhrec_tags_to_weights(tag_counts: Dict[str, int]) -> Dict[str, float]:
    """Convert EDHREC tag_counts → normalized weights using internal names."""
    weights: Dict[str, float] = {}
    total = sum(tag_counts.values())
    if total == 0:
        return weights

    for tag, count in tag_counts.items():
        internal = EDHREC_TAG_MAP.get(tag)
        if internal is None:
            continue
        if internal not in weights:
            weights[internal] = 0.0
        weights[internal] += count / total

    return weights


# ── pyedhrec-powered functions (new features) ──────────────────────────────

from pyedhrec import EDHRec

_pyedhrec: Optional[EDHRec] = None


def _get_pyedhrec() -> EDHRec:
    global _pyedhrec
    if _pyedhrec is None:
        _pyedhrec = EDHRec()
    return _pyedhrec


def _pyedhrec_disk_path(slug: str, kind: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{slug}_{kind}.json")


def _pyedhrec_load_disk(slug: str, kind: str) -> Optional[dict]:
    path = _pyedhrec_disk_path(slug, kind)
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > CACHE_TTL:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _pyedhrec_save_disk(slug: str, kind: str, data: dict):
    path = _pyedhrec_disk_path(slug, kind)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _extract_card_name(cv: dict) -> str:
    """Extract card name from a pyedhrec cardview dict (flexible field names)."""
    for key in ("name", "card_name", "card"):
        val = cv.get(key)
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            n = val.get("name")
            if n:
                return n
    return cv.get("header", "")


def _compute_inclusion_pct(cv: dict) -> float:
    """Compute inclusion percentage from pyedhrec cardview (num_decks / potential_decks * 100)."""
    num = cv.get("num_decks", 0)
    pot = cv.get("potential_decks", 0)
    if pot and num:
        return round(num / pot * 100, 1)
    return 0.0


def _extract_card_score(cv: dict) -> float:
    """Extract a score from cardview — prefer synergy, fallback to inclusion %."""
    synergy = cv.get("synergy")
    if isinstance(synergy, (int, float)) and synergy != 0:
        return round(float(synergy), 4)
    return _compute_inclusion_pct(cv)


def get_all_cardlists(commander_name: str) -> Dict[str, list]:
    """
    Fetch ALL cardlists from EDHREC for a commander using pyedhrec.
    Returns {section_name: [{name, score}, ...]}
    Uses disk cache (24h TTL).
    """
    slug = _commander_to_slug(commander_name)

    cached = _pyedhrec_load_disk(slug, "cardlists")
    if cached:
        return cached

    try:
        edh = _get_pyedhrec()
        raw = edh.get_commander_cards(commander_name)
    except Exception as e:
        print(f"[pyedhrec] Error fetching cardlists for {commander_name}: {e}")
        return {}

    if not raw:
        return {}

    result: Dict[str, list] = {}
    for header, cardviews in raw.items():
        cards = []
        if isinstance(cardviews, list):
            for cv in cardviews:
                name = _extract_card_name(cv)
                if name:
                    cards.append({
                        "name": str(name),
                        "score": _extract_card_score(cv),
                        "inclusion_pct": _compute_inclusion_pct(cv),
                        "num_decks": cv.get("num_decks", 0),
                    })
        if cards:
            result[str(header)] = cards

    _pyedhrec_save_disk(slug, "cardlists", result)
    return result


def get_top_cards_by_category(commander_name: str) -> Dict[str, list]:
    """
    Returns top cards organized by functional category.
    Keys like 'Creatures', 'Instants', 'Sorceries', 'Artifacts',
    'Enchantments', 'Planeswalkers', 'Lands', 'Mana Artifacts', 'Utility Lands'.
    """
    all_cards = get_all_cardlists(commander_name)
    # Filter to known category headers
    category_filters = [
        "Creatures", "Instants", "Sorceries",
        "Mana Artifacts", "Utility Artifacts", "Artifacts",
        "Enchantments",
        "Planeswalkers", "Battles",
        "Utility Lands", "Lands",
        "Top Cards",
    ]
    result: Dict[str, list] = {}
    for header, cards in all_cards.items():
        for cat in category_filters:
            if cat.lower() in header.lower():
                result[cat] = cards
                break
    return result


def get_high_synergy_for_commander(commander_name: str) -> list:
    """Returns high synergy cards for a commander."""
    all_cards = get_all_cardlists(commander_name)
    for header, cards in all_cards.items():
        if "high synergy" in header.lower() or "synergy" in header.lower():
            return cards
    return []


def get_new_for_commander(commander_name: str) -> list:
    """Returns recently trending/new cards for a commander."""
    all_cards = get_all_cardlists(commander_name)
    for header, cards in all_cards.items():
        if "new card" in header.lower() or "new" in header.lower():
            return cards
    return []


def get_average_decklist(commander_name: str, budget: Optional[str] = None) -> Optional[dict]:
    """
    Returns the average decklist from EDHREC.
    budget: None = normal, 'budget' = budget version, 'expensive' = expensive version.
    Returns {'commander': str, 'cards': [{name, quantity}]}
    """
    slug = _commander_to_slug(commander_name)
    kind = f"avgdeck_{budget or 'normal'}"

    cached = _pyedhrec_load_disk(slug, kind)
    if cached:
        return cached

    try:
        edh = _get_pyedhrec()
        if budget:
            raw = edh.get_commanders_average_deck(commander_name, budget)
        else:
            raw = edh.get_commanders_average_deck(commander_name)
    except Exception as e:
        print(f"[pyedhrec] Error fetching avg deck for {commander_name}: {e}")
        return None

    if not raw:
        return None

    deck_data = raw.get("decklist") or raw.get("deck") or {}
    # pyedhrec wraps: {commander, decklist: {commander, cards: {Artifact: [[name,qty]...], ...}}}
    inner = deck_data if isinstance(deck_data, dict) else {}
    cards_dict = inner.get("cards", {})
    
    cards = []
    if isinstance(cards_dict, dict):
        # cards is {type_name: [[name, qty], ...]}
        for type_name, card_list in cards_dict.items():
            if isinstance(card_list, list):
                for entry in card_list:
                    if isinstance(entry, list) and len(entry) >= 2:
                        cards.append({
                            "name": str(entry[0]),
                            "quantity": int(entry[1]),
                            "type": type_name.lower(),
                        })
                    elif isinstance(entry, str):
                        cards.append({"name": entry, "quantity": 1, "type": type_name.lower()})
    elif isinstance(cards_dict, list):
        for entry in cards_dict:
            if isinstance(entry, dict):
                name = entry.get("name") or entry.get("card", "")
                qty = entry.get("quantity") or entry.get("count", 1)
                cards.append({"name": str(name), "quantity": int(qty) if qty else 1})
            elif isinstance(entry, str):
                cards.append({"name": entry, "quantity": 1})

    result = {"commander": raw.get("commander", commander_name), "cards": cards}
    _pyedhrec_save_disk(slug, kind, result)
    return result

    for tag, count in tag_counts.items():
        internal = EDHREC_TAG_MAP.get(tag)
        if internal is None:
            continue
        if internal not in weights:
            weights[internal] = 0.0
        weights[internal] += count / total

    return weights

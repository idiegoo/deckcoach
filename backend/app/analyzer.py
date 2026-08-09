import re
from typing import List, Dict, Any, Optional
from .models import Card, Deck
from .scryfall import ScryfallClient
from .edhrec import get_tag_counts, edhrec_tags_to_weights

client = ScryfallClient()

# Heuristic keywords
def _has_oracle(text: str, keywords: List[str]) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in keywords)

RAMP_KEYWORDS = [
    "add {c}", "add {w}", "add {u}", "add {b}", "add {r}", "add {g}", "add one mana",
    "add two mana", "add three mana", "search your library for a land", "put a land",
    "search your library for a basic land", "tap for mana", "mana of any color",
    "each player may put", "land from your library onto the battlefield"
]
DRAW_KEYWORDS = [
    "draw a card", "draw two cards", "draw three cards", "draw x cards",
    "draw that many cards", "draw cards equal"
]
REMOVAL_KEYWORDS = [
    "destroy target creature", "destroy target artifact", "destroy target enchantment",
    "exile target creature", "exile target artifact", "exile target enchantment",
    "deals damage to target", "-x/-x until end of turn", "-1/-1 counter"
]
WIPE_KEYWORDS = [
    "destroy all", "exile all", "each creature gets", "each player sacrifices",
    "destroy each", "exile each", "return all"
]
TUTOR_KEYWORDS = [
    "search your library for a", "search your library for an"
]
INTERACTION_KEYWORDS = [
    "counter target", "return target", "tap target", "stifle"
]
GRAVEYARD_KEYWORDS = [
    "graveyard", "return from your graveyard", "reclaim", "recur",
    "from any graveyard", "dredge"
]

class CategoryStats:
    def __init__(self):
        self.land = 0
        self.creature = 0
        self.artifact = 0
        self.enchantment = 0
        self.instant = 0
        self.sorcery = 0
        self.planeswalker = 0
        self.battle = 0
        self.ramp = 0
        self.draw = 0
        self.removal = 0
        self.wipe = 0
        self.tutor = 0
        self.interaction = 0
        self.graveyard = 0

    def to_dict(self):
        return {
            "lands": self.land,
            "creatures": self.creature,
            "artifacts": self.artifact,
            "enchantments": self.enchantment,
            "instants": self.instant,
            "sorceries": self.sorcery,
            "planeswalkers": self.planeswalker,
            "battles": self.battle,
            "ramp": self.ramp,
            "draw": self.draw,
            "removal": self.removal,
            "wipes": self.wipe,
            "tutors": self.tutor,
            "interaction": self.interaction,
            "graveyard": self.graveyard,
        }

def parse_decklist(text: str) -> List[tuple]:
    lines = text.strip().splitlines()
    cards = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue
        # Match quantity + card name (ignore set info/comments)
        m = re.match(r"^(\d+)\s+(.+?)(?:\s+#.*)?$", line)
        if not m:
            # assume 1 copy if no number
            cards.append((1, line))
        else:
            qty = int(m.group(1))
            name = m.group(2).strip()
            # remove trailing set info like (SET) 123
            name = re.sub(r"\s+\(\w+\)\s*\d*\s*$", "", name)
            name = re.sub(r"\s+\*\w+\*?$", "", name) # remove Moxfield asterisks
            cards.append((qty, name))
    return cards

def split_commander_from_deck(text: str) -> tuple[List[tuple], Optional[str]]:
    """Returns (deck_cards, commander_name) auto-detecting commander from list."""
    raw = text.strip()

    # Strategy 1: // Commander section header
    cmdr_match = re.search(r"(?im)^\s*//\s*Commander\s*$", raw, re.MULTILINE)
    if cmdr_match:
        main = raw[:cmdr_match.start()].strip()
        cmdr_section = raw[cmdr_match.end():].strip()
        cmdr_lines = cmdr_section.splitlines()
        for line in cmdr_lines:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            m = re.match(r"^(\d+)?\s*(.+?)(\s+\*[CM]+\*|\s+\(Commander\))?\s*$", line)
            if m:
                name = m.group(2).strip()
                name = re.sub(r"\s+\(\w+\)\s*\d*\s*$", "", name)
                name = re.sub(r"\s+\*\w+\*?$", "", name)
                return parse_decklist(main), name

    # Strategy 2: blank line separator (Moxfield default)
    parts = re.split(r"\n\s*\n", raw)
    if len(parts) >= 2:
        main = "\n".join(parts[:-1])
        cmdr_section = parts[-1].strip()
        cmdr_lines = cmdr_section.splitlines()
        for line in cmdr_lines:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            m = re.match(r"^(\d+)?\s*(.+?)(\s+\*[CM]+\*|\s+\(Commander\)|\s+#!Commander)?\s*$", line)
            if m:
                name = m.group(2).strip()
                name = re.sub(r"\s+\(\w+\)\s*\d*\s*$", "", name)
                name = re.sub(r"\s+\*\w+\*?$", "", name)
                return parse_decklist(main), name

    # Strategy 3: marked commander inline (*CMDR*, *F*, (Commander), #!Commander)
    lines = raw.splitlines()
    deck_cards = []
    commander_name = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue
        is_cmdr = bool(re.search(r"\*CMDR\*|\*F\*|\(Commander\)|#!Commander", line))
        m = re.match(r"^(\d+)\s+(.+?)(?:\s+#.*)?$", line)
        if not m:
            name = line
            name = re.sub(r"\s+\*CMDR\*|\s+\*F\*|\s+\(Commander\)|\s+#!Commander", "", name)
            name = re.sub(r"\s+\(\w+\)\s*\d*\s*$", "", name)
            name = re.sub(r"\s+\*\w+\*?$", "", name)
            if is_cmdr:
                commander_name = name
            else:
                deck_cards.append((1, name))
        else:
            qty = int(m.group(1))
            name = m.group(2).strip()
            name = re.sub(r"\s+\(\w+\)\s*\d*\s*$", "", name)
            name = re.sub(r"\s+\*\w+\*?$", "", name)
            name = re.sub(r"\s+\*CMDR\*|\s+\*F\*|\s+\(Commander\)|\s+#!Commander", "", name)
            if is_cmdr:
                commander_name = name
            else:
                deck_cards.append((qty, name))

    if commander_name:
        return deck_cards, commander_name

    # Strategy 4: no commander found - return all as deck
    return parse_decklist(raw), None

def fetch_deck(cards_raw: List[tuple]) -> List[Card]:
    unique_names = list({n for _, n in cards_raw})
    scryfall_data = client.get_cards(unique_names)
    result = []
    for qty, name in cards_raw:
        raw = scryfall_data.get(name)
        result.append(client.to_card_model(name, qty, raw))
    return result

def categorize(card: Card) -> CategoryStats:
    s = CategoryStats()
    tl = (card.type_line or "").lower()
    ot = card.oracle_text or ""
    if "land" in tl:
        s.land = card.quantity
    elif "creature" in tl:
        s.creature = card.quantity
    elif "artifact" in tl:
        s.artifact = card.quantity
    elif "enchantment" in tl:
        s.enchantment = card.quantity
    elif "instant" in tl:
        s.instant = card.quantity
    elif "sorcery" in tl:
        s.sorcery = card.quantity
    elif "planeswalker" in tl:
        s.planeswalker = card.quantity
    elif "battle" in tl:
        s.battle = card.quantity

    # Ramp (non-land cards that add mana; lands already counted as lands)
    if s.land == 0 and _has_oracle(ot, RAMP_KEYWORDS):
        s.ramp = card.quantity
    # Lands that ramp (like Evolving Wilds, fetchlands, etc) could be double counted if not careful.
    # We'll count them as lands only, but note "mana fixing" separately later.

    if _has_oracle(ot, DRAW_KEYWORDS):
        s.draw = card.quantity
    if _has_oracle(ot, REMOVAL_KEYWORDS):
        s.removal = card.quantity
    if _has_oracle(ot, WIPE_KEYWORDS):
        s.wipe = card.quantity
    if _has_oracle(ot, TUTOR_KEYWORDS):
        s.tutor = card.quantity
    if _has_oracle(ot, INTERACTION_KEYWORDS):
        s.interaction = card.quantity
    if _has_oracle(ot, GRAVEYARD_KEYWORDS):
        s.graveyard = card.quantity
    return s

def analyze_deck(deck: Deck) -> Dict[str, Any]:
    stats = CategoryStats()
    cmc_values = []
    color_counts = {}
    commander_cid = set(deck.commander.color_identity or [])
    illegal_cards = []
    nonland_mana_sources = 0
    total_cards = sum(c.quantity for c in deck.cards)
    category_cards: Dict[str, List[str]] = {
        "ramp": [], "draw": [], "removal": [], "wipes": [],
        "tutors": [], "interaction": [], "graveyard": [],
    }

    for card in deck.cards:
        cat = categorize(card)
        stats.land += cat.land
        stats.creature += cat.creature
        stats.artifact += cat.artifact
        stats.enchantment += cat.enchantment
        stats.instant += cat.instant
        stats.sorcery += cat.sorcery
        stats.planeswalker += cat.planeswalker
        stats.battle += cat.battle
        stats.ramp += cat.ramp
        stats.draw += cat.draw
        stats.removal += cat.removal
        stats.wipe += cat.wipe
        stats.tutor += cat.tutor
        stats.interaction += cat.interaction
        stats.graveyard += cat.graveyard

        name = card.name
        ot = card.oracle_text or ""
        if cat.ramp > 0:
            category_cards["ramp"].append(name)
        if cat.draw > 0:
            category_cards["draw"].append(name)
        if cat.removal > 0:
            category_cards["removal"].append(name)
        if cat.wipe > 0:
            category_cards["wipes"].append(name)
        if cat.tutor > 0:
            category_cards["tutors"].append(name)
        if cat.interaction > 0:
            category_cards["interaction"].append(name)
        if cat.graveyard > 0:
            category_cards["graveyard"].append(name)

        if card.cmc is not None and cat.land == 0:
            cmc_values.extend([card.cmc] * card.quantity)

        # Color identity legality
        card_cid = set(card.color_identity or [])
        if card_cid - commander_cid:
            illegal_cards.append(card.name)

        # Mana producers that are lands (for fixing count)
        if cat.land > 0 and _has_oracle(card.oracle_text or "", ["add {", "add one mana", "add two mana"]):
            nonland_mana_sources += 0  # they are lands, counted in land
        if cat.ramp > 0:
            nonland_mana_sources += card.quantity

    # Curve buckets
    curve = {"0-1": 0, "2-3": 0, "4-5": 0, "6+": 0}
    for v in cmc_values:
        if v <= 1:
            curve["0-1"] += 1
        elif v <= 3:
            curve["2-3"] += 1
        elif v <= 5:
            curve["4-5"] += 1
        else:
            curve["6+"] += 1

    avg_cmc = round(sum(cmc_values) / len(cmc_values), 2) if cmc_values else 0

    commander_info = {
        "name": deck.commander.name,
        "mana_cost": deck.commander.mana_cost,
        "cmc": deck.commander.cmc,
        "color_identity": deck.commander.color_identity,
        "type": deck.commander.type_line,
        "oracle_text": deck.commander.oracle_text,
    }

    archetype, archetype_thresholds, archetypes_list = detect_archetype(deck, stats)

    return {
        "total_cards": total_cards,
        "categories": stats.to_dict(),
        "category_cards": category_cards,
        "curve": curve,
        "average_cmc": avg_cmc,
        "commander": commander_info,
        "illegal_cards": illegal_cards,
        "ramp_nonland": nonland_mana_sources,
        "archetype": archetype,
        "archetype_thresholds": archetype_thresholds,
        "archetypes": archetypes_list,
    }


# ─── Archetype detection (EDHRec tags) ───────────────────────────────────

# Format: "Tag Name": {"ramp":[good], "draw":[good], "removal":[good], "wipes":[good], "tutors":[good], "interaction":[good], "lands":[ideal], "cmc":[ideal]}
ARCHETYPE_THRESHOLDS: Dict[str, Dict[str, List[int]]] = {
    "cEDH / Combo":       {"ramp": [8, 12],  "draw": [10, 16], "removal": [4, 7],   "wipes": [0, 2],  "tutors": [8, 14],   "interaction": [10, 16], "lands": [27, 30], "cmc": [1.5, 2.2]},
    "Spellslinger":       {"ramp": [8, 12],  "draw": [12, 18], "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [32, 36], "cmc": [2.0, 2.8]},
    "Tribal / Typal":     {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Voltron":            {"ramp": [8, 12],  "draw": [6, 10],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [2.0, 2.8]},
    "Lands / Landfall":   {"ramp": [14, 22], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [4, 8],   "lands": [38, 45], "cmc": [2.5, 3.5]},
    "Reanimator":         {"ramp": [8, 12],  "draw": [10, 15], "removal": [6, 10],  "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Artifacts":          {"ramp": [12, 18], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [30, 35], "cmc": [2.0, 2.8]},
    "Enchantress":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [3, 6],    "interaction": [6, 10],  "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Tokens":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "+1/+1 Counters":     {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Aristocrats":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [2.0, 2.8]},
    "Control / Stax":     {"ramp": [8, 12],  "draw": [8, 12],  "removal": [8, 14],  "wipes": [3, 6],  "tutors": [3, 6],    "interaction": [10, 16], "lands": [35, 38], "cmc": [2.5, 3.2]},
    "Group Hug":          {"ramp": [10, 16], "draw": [12, 18], "removal": [4, 7],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [35, 38], "cmc": [2.5, 3.5]},
    "Lifegain":           {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Storm":              {"ramp": [6, 10],  "draw": [12, 18], "removal": [2, 5],   "wipes": [0, 2],  "tutors": [3, 6],    "interaction": [6, 10],  "lands": [28, 32], "cmc": [1.2, 2.0]},
    "Mill":               {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Blink / ETB":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Wheels":             {"ramp": [8, 12],  "draw": [14, 20], "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [32, 36], "cmc": [2.2, 3.0]},
    "Burn":               {"ramp": [8, 12],  "draw": [8, 12],  "removal": [10, 16], "wipes": [2, 4],  "tutors": [1, 3],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.0, 2.8]},
    "Group Slug":         {"ramp": [8, 12],  "draw": [8, 12],  "removal": [8, 14],  "wipes": [2, 4],  "tutors": [1, 3],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Equipment":          {"ramp": [8, 12],  "draw": [6, 10],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [2.0, 2.8]},
    "Infect":             {"ramp": [6, 10],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [0, 2],  "tutors": [2, 4],    "interaction": [6, 10],  "lands": [32, 36], "cmc": [1.8, 2.5]},
    "Treasure":           {"ramp": [12, 18], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [32, 36], "cmc": [2.5, 3.2]},
    "Superfriends":       {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [3, 6],  "tutors": [3, 6],    "interaction": [6, 10],  "lands": [35, 39], "cmc": [2.8, 3.5]},
    "Chaos":              {"ramp": [10, 14], "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [1, 3],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.8, 3.8]},
    "Stompy":             {"ramp": [12, 18], "draw": [6, 10],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [1, 3],    "interaction": [2, 5],   "lands": [33, 38], "cmc": [2.8, 4.0]},
    "Pillow Fort":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [3, 6],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [35, 39], "cmc": [2.5, 3.5]},
    "Forced Combat":      {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Theft":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.8, 3.5]},
    "Discard":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.2, 3.0]},
    "Self-Mill":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Vehicles":           {"ramp": [8, 12],  "draw": [6, 10],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.2]},
    "Big Mana":           {"ramp": [16, 24], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [35, 40], "cmc": [3.0, 4.5]},
    "Sacrifice":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [2.0, 2.8]},
    "X Spells":           {"ramp": [12, 18], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [2.5, 3.5]},
    "Aggro":              {"ramp": [6, 10],  "draw": [6, 10],  "removal": [4, 8],   "wipes": [1, 3],  "tutors": [1, 3],    "interaction": [4, 8],   "lands": [30, 35], "cmc": [1.5, 2.5]},
    "+ExtrA TurnS":       {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [8, 14],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Toolbox":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [6, 12],   "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Energy":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.2]},
    "Politics / Voting":  {"ramp": [8, 12],  "draw": [10, 15], "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [35, 38], "cmc": [2.5, 3.5]},
    "Cascade / Discover": {"ramp": [10, 14], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.8, 4.0]},
    "Cycling":            {"ramp": [8, 12],  "draw": [10, 15], "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.0, 3.0]},
    "Dredge":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [1.8, 2.8]},
    "Hatebears":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [8, 14],  "lands": [34, 38], "cmc": [2.0, 3.0]},
    "Lifedrain":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Food":               {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Monarch":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Clues / Investigate": {"ramp": [8, 12], "draw": [10, 15], "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Cantrips":           {"ramp": [8, 12],  "draw": [12, 18], "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [33, 37], "cmc": [1.5, 2.5]},
    "-1/-1 Counters":     {"ramp": [8, 12],  "draw": [8, 12],  "removal": [8, 14],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Land Destruction":   {"ramp": [10, 16], "draw": [6, 10],  "removal": [6, 10],  "wipes": [3, 6],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [36, 42], "cmc": [2.8, 3.8]},
    "Clones":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.8, 3.8]},
    "Dragons":            {"ramp": [12, 18], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [35, 40], "cmc": [3.0, 4.5]},
    "Goblins":            {"ramp": [6, 10],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [1, 3],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [32, 36], "cmc": [1.8, 2.8]},
    "Elves":              {"ramp": [12, 18], "draw": [8, 12],  "removal": [4, 8],   "wipes": [1, 3],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [30, 34], "cmc": [1.8, 2.8]},
    "Zombies":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [4, 8],   "lands": [33, 37], "cmc": [2.5, 3.2]},
    "Slivers":            {"ramp": [8, 12],  "draw": [6, 10],  "removal": [4, 8],   "wipes": [1, 3],  "tutors": [3, 6],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.0, 3.0]},
    "Eldrazi":            {"ramp": [12, 18], "draw": [6, 10],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [3.5, 5.5]},
    "Dinos":              {"ramp": [10, 16], "draw": [6, 10],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [3.0, 4.2]},
    "Ninjutsu":           {"ramp": [6, 10],  "draw": [10, 15], "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [32, 36], "cmc": [2.5, 4.0]},
    "Mutate":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.8, 4.5]},
    "Morph / Manifest":   {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Sagas":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Dungeon / Venture":  {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Toughness Matters":  {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Spell Copy":         {"ramp": [8, 12],  "draw": [10, 15], "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Madness":            {"ramp": [8, 12],  "draw": [10, 15], "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Topdeck":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Convoke":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Party":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Exile":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [8, 14],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Flash":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [8, 14],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Proliferate":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Battles":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Defenders":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Kicker":             {"ramp": [10, 16], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [3.0, 4.5]},
    "Fight":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [8, 14],  "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Unblockable":        {"ramp": [6, 10],  "draw": [10, 15], "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [32, 36], "cmc": [2.0, 3.0]},
    "Self-Damage":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Auras":              {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [3, 6],    "interaction": [6, 10],  "lands": [34, 37], "cmc": [2.0, 2.8]},
    "Historic":           {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Graveyard":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [3, 6],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.2]},
    "Flying":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Pingers":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [8, 14],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.0, 2.8]},
    "Tap / Untap":        {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Activated Abilities": {"ramp": [8, 12], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Prowess":            {"ramp": [8, 12],  "draw": [10, 15], "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [33, 37], "cmc": [1.8, 2.5]},
    "Bounce":             {"ramp": [8, 12],  "draw": [8, 12],  "removal": [6, 10],  "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Weenies":            {"ramp": [6, 10],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [1, 3],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [32, 36], "cmc": [1.5, 2.5]},
    "Power Matters":      {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Eggs":               {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.0, 2.8]},
    "Tron":               {"ramp": [12, 18], "draw": [6, 10],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [3.0, 5.0]},
    "Adventures":         {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Shrines":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Impulse Draw":       {"ramp": [8, 12],  "draw": [10, 15], "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.5, 3.2]},
    "Modular":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Coin Flip":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [2, 4],    "interaction": [4, 8],   "lands": [34, 38], "cmc": [2.5, 3.5]},
    "Scry":               {"ramp": [8, 12],  "draw": [10, 15], "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 37], "cmc": [2.0, 2.8]},
    "Guildgates":         {"ramp": [10, 14], "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 6],    "interaction": [4, 8],   "lands": [38, 44], "cmc": [2.5, 3.5]},
    "Surveil":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 37], "cmc": [2.2, 3.0]},
    "Polymorph":          {"ramp": [8, 12],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [6, 10],  "lands": [34, 37], "cmc": [2.5, 3.5]},
    "Glass Cannon":       {"ramp": [6, 10],  "draw": [8, 12],  "removal": [4, 8],   "wipes": [2, 4],  "tutors": [4, 8],    "interaction": [6, 10],  "lands": [33, 37], "cmc": [2.0, 2.8]},
    "Creatureless":       {"ramp": [10, 14], "draw": [10, 15], "removal": [8, 14],  "wipes": [3, 6],  "tutors": [4, 8],    "interaction": [10, 16], "lands": [35, 40], "cmc": [2.5, 3.5]},
    "Hellbent":           {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [4, 8],   "lands": [34, 37], "cmc": [2.2, 3.0]},
    "Suspend":            {"ramp": [8, 12],  "draw": [8, 12],  "removal": [5, 9],   "wipes": [2, 4],  "tutors": [2, 5],    "interaction": [6, 10],  "lands": [34, 38], "cmc": [2.5, 3.8]},
    "General / Midrange": {"ramp": [10, 14], "draw": [10, 15], "removal": [8, 14],  "wipes": [2, 5],  "tutors": [2, 6],    "interaction": [6, 12],  "lands": [35, 38], "cmc": [2.5, 3.5]},
}

# commander_kw = matched against commander oracle+type (score ×5 per hit)
# deck_kw     = matched against all cards oracle+names (score ×1.5 per hit, capped 6)
# type_bias   = boost score based on % of that card type in deck (capped 8 points)
# subtag_of   = if this tag is a subtag of a larger parent archetype (shown below as secondary)
ARCHETYPE_SIGNATURES: Dict[str, Dict[str, List[str]]] = {
    "cEDH / Combo": {
        "commander_kw": ["you win the game", "whenever you cast", "tutor", "ad nauseam", "thassa's oracle"],
        "deck_kw": ["mana crypt", "mox", "lion's eye diamond", "ad nauseam", "demonic consultation", "tainted pact", "gilded drake", "underworld breach"],
        "type_bias": {},
    },
    "Spellslinger": {
        "commander_kw": ["whenever you cast an instant or sorcery", "instant and sorcery", "copy target instant", "flashback", "whenever you cast or copy", "prowess"],
        "deck_kw": ["storm", "copy target", "past in flames", "grapeshot", "brain freeze", "guttersnipe"],
        "type_bias": {"instant": 1.5, "sorcery": 1.5},
    },
    "Tribal / Typal": {
        "commander_kw": ["other goblin", "other elf", "other merfolk", "other zombie", "other vampire", "other human",
                         "goblin", "elf", "merfolk", "zombie", "vampire", "human", "dragon", "sliver", "angel", "demon",
                         "cat", "dog", "rat", "pirate", "ninja", "samurai", "warrior", "rogue", "wizard", "spirit",
                         "soldier", "knight", "dinosaur", "hydra", "elemental", "god", "sphinx", "bird", "faerie",
                         "eldrazi", "construct", "phyrexian", "horror", "beast", "giant", "griffin", "kithkin",
                         "cleric", "druid", "shaman", "scarecrow", "minotaur", "centaur", "gorgon", "monk",
                         "artifact creature", "all sliver", "other dragon", "other angel"],
        "deck_kw": [],
        "type_bias": {"creature": 2.0},
    },
    "Voltron": {
        "commander_kw": ["equipped creature", "whenever ~ deals combat damage", "double strike", "whenever this creature attacks",
                         "enchant creature", "enchant permanent", "attach", "equip", "whenever you cast an equipment",
                         "equipment spell", "whenever this creature deals", "commander damage"],
        "deck_kw": ["sword of", "batterskull", "colossus hammer", "helm of the host", "whispersilk cloak", "lightning greaves", "swiftfoot boots"],
        "type_bias": {},
    },
    "Lands / Landfall": {
        "commander_kw": ["landfall", "whenever a land enters", "lands you control", "search your library for a land",
                         "land card from", "land from your graveyard", "untap target land", "play an additional land",
                         "land card in your graveyard", "whenever you play a land"],
        "deck_kw": ["landfall", "scute swarm", "avenger of zendikar", "lotus cobra", "oracle of mul daya", "azusa"],
        "type_bias": {"land": 3.0},
    },
    "Reanimator": {
        "commander_kw": ["return target creature card from your graveyard", "from your graveyard to the battlefield",
                         "whenever a creature card is put into your graveyard", "discard a card", "whenever a creature dies",
                         "reanimate", "entomb", "from your graveyard"],
        "deck_kw": ["reanimate", "entomb", "buried alive", "animate dead", "necromancy", "dance of the dead", "persist", "living death"],
        "type_bias": {"graveyard": 2.0},
    },
    "Artifacts": {
        "commander_kw": ["artifact", "improvise", "whenever you cast an artifact", "other artifact", "affinity",
                         "noncreature artifact", "artificer", "artifact creature"],
        "deck_kw": ["improvise", "affinity", "mycosynth", "scrap", "cranial plating", "thopter"],
        "type_bias": {"artifact": 2.5},
    },
    "Enchantress": {
        "commander_kw": ["enchantment", "constellation", "whenever you cast an enchantment", "enchantress",
                         "shrine", "enchant", "whenever an enchantment enters"],
        "deck_kw": ["enchantress", "constellation", "sterling grove", "hallowed haunting", "sigil of the empty throne"],
        "type_bias": {"enchantment": 2.5},
    },
    "Tokens": {
        "commander_kw": ["create a", "token", "create x", "create three", "twice that many", "whenever a creature token",
                         "for each token you control", "populate", "fabricate", "treasure token", "food token", "clue token"],
        "deck_kw": ["cathars' crusade", "parallel lives", "anointed procession", "doubling season", "divine visitation", "impact tremors", "purphoros"],
        "type_bias": {},
    },
    "+1/+1 Counters": {
        "commander_kw": ["+1/+1 counter", "put a +1/+1 counter", "whenever you put", "proliferate", "modular",
                         "with a +1/+1 counter", "for each +1/+1 counter", "hardened scales", "whenever a creature you control with"],
        "deck_kw": ["hardened scales", "ozolith", "winding constrictor", "doubling season", "conclave mentor", "corpsejack menace"],
        "type_bias": {},
    },
    "Aristocrats": {
        "commander_kw": ["whenever a creature dies", "sacrifice a creature", "whenever another creature dies",
                         "sacrifice this creature", "whenever you sacrifice", "when a creature you control dies"],
        "deck_kw": ["blood artist", "zulaport cutthroat", "bastion of remembrance", "pitiless plunderer", "grave pact", "dictate of erebos", "ashnod's altar", "phyrexian altar"],
        "type_bias": {"creature": 1.2},
    },
    "Control / Stax": {
        "commander_kw": ["opponents can't", "players can't", "counter target", "unless they pay", "stax",
                         "enters tapped", "enter the battlefield tapped", "only during their turn", "can't cast"],
        "deck_kw": ["drannith magistrate", "rule of law", "winter orb", "static orb", "trinisphere", "rhystic study", "smothering tithe", "grand arbiter augustin"],
        "type_bias": {"interaction": 2.0},
    },
    "Group Hug": {
        "commander_kw": ["each player draws", "all players", "each player may", "each opponent draws",
                         "each opponent may", "you and target opponent", "everyone", "each player creates"],
        "deck_kw": ["howling mine", "tempting contract", "temple bell", "rites of flourishing", "dictate of kruphix", "font of mythos"],
        "type_bias": {},
    },
    "Lifegain": {
        "commander_kw": ["you gain life", "whenever you gain life", "soul warden", "life total",
                         "whenever a creature enters the battlefield under your control, you gain", "lifelink"],
        "deck_kw": ["soul warden", "essence warden", "soul's attendant", "ajani's pridemate", "aetherflux reservoir", "bolas's citadel"],
        "type_bias": {},
    },
    "Storm": {
        "commander_kw": ["storm", "grapeshot", "brain freeze", "tendrils", "empty the warrens",
                         "past in flames", "mind's desire", "thousand-year"],
        "deck_kw": ["ritual", "mox", "lotus petal", "past in flames", "underworld breach", "lion's eye diamond", "brain freeze"],
        "type_bias": {"instant": 1.5, "sorcery": 1.5},
    },
    "Mill": {
        "commander_kw": ["mill", "put the top", "into their graveyard", "from the top of", "into your graveyard from",
                         "target player mills", "each opponent mills", "whenever you mill", "dimir", "from the top of your library"],
        "deck_kw": ["bruvac", "fraying sanity", "maddening cacophony", "traumatize", "mind crank", "duskmantle guildmage", "painters servant", "grindstone"],
        "type_bias": {},
    },
    "Blink / ETB": {
        "commander_kw": ["exile target creature, then return", "blink", "flicker", "whenever another creature enters",
                         "exile another", "enter the battlefield", "when ~ enters", "when this creature enters", "panharmonicon", "eerie interlude"],
        "deck_kw": ["ephemerate", "teleportation circle", "conjurer's closet", "brago", "yorion", "thassa deep-dwelling", "panharmonicon", "eerie interlude"],
        "type_bias": {},
    },
    "Wheels": {
        "commander_kw": ["discard your hand", "draw seven", "draw that many cards", "discard their hand",
                         "each player discards", "shuffle", "wheel of fortune", "windfall"],
        "deck_kw": ["wheel of fortune", "windfall", "magus of the wheel", "echo of eons", "valakut awakening", "days undoing", "notion thief", "narset parter of veils"],
        "type_bias": {},
    },
    "Burn": {
        "commander_kw": ["deals damage to each opponent", "whenever you cast an instant or sorcery", "deals damage to target player",
                         "purphoros", "torbran", "fiery emancipation", "whenever an opponent is dealt", "impact tremors", "zo-zu"],
        "deck_kw": ["fiery emancipation", "dictate of the twin gods", "furnace of rath", "torbran", "purphoros", "zo-zu", "manabarbs", "sulfuric vortex"],
        "type_bias": {},
    },
    "Group Slug": {
        "commander_kw": ["each opponent loses life", "loses life", "each opponent sacrifices", "each player loses",
                         "each player sacrifices", "whenever an opponent", "damage to each opponent"],
        "deck_kw": ["manabarbs", "zo-zu", "spellshock", "sulfuric vortex", "price of glory", "ankh of mishra", "tainted aether", "tainted remedy"],
        "type_bias": {},
    },
    "Equipment": {
        "commander_kw": ["equipment", "equipped creature", "attach", "equip", "whenever an equipped", "for each equipment"],
        "deck_kw": ["sword of", "colossus hammer", "argentum armor", "hammer of nazahn", "sigarda's aid", "puresteel paladin", "stoneforge mystic", "stonehewer giant"],
        "type_bias": {},
    },
    "Infect": {
        "commander_kw": ["infect", "poison counter", "proliferate", "whenever a creature you control deals combat damage to a player"],
        "deck_kw": ["grafted exoskeleton", "phyresis", "triumph of the hordes", "blightsteel colossus", "tainted strike"],
        "type_bias": {},
    },
    "Treasure": {
        "commander_kw": ["treasure", "create a treasure", "whenever you sacrifice", "whenever an opponent sacrifices",
                         "for each treasure", "sacrifice a treasure", "whenever you create a treasure"],
        "deck_kw": ["dockside extortionist", "goldspan dragon", "xorn", "academy manufactor", "professional face-breaker", "bootleggers' stash", "old gnawbone"],
        "type_bias": {},
    },
    "Superfriends": {
        "commander_kw": ["planeswalker", "whenever you activate a loyalty", "loyalty counters", "each planeswalker you control",
                         "you may activate loyalty abilities", "oath of", "proliferate", "commander tax"],
        "deck_kw": ["atraxa", "doubling season", "deepglow skate", "oath of teferi", "vorinclex monstrous raider", "ichormoon gauntlet", "chain veil", "evolution sage", "narset parter"],
        "type_bias": {"planeswalker": 3.0},
    },
    "Sacrifice": {
        "commander_kw": ["sacrifice a creature", "whenever you sacrifice a permanent", "whenever a player sacrifices",
                         "sacrifice another", "sacrifice an artifact", "sacrifice a nontoken"],
        "deck_kw": ["grave pact", "dictate of erebos", "ashnod's altar", "phyrexian altar", "altar of dementia", "butcher of malakir", "grave betrayal", "it that betrays"],
        "type_bias": {},
    },
    "Stompy": {
        "commander_kw": ["creatures you control get", "creatures you control have", "tap: add", "mana equal to",
                         "creature spells you cast cost", "where x is the greatest power among", "power 4 or greater", "power 5 or greater"],
        "deck_kw": ["craterhoof behemoth", "pathbreaker ibex", "finale of devastation", "overwhelming stampede", "triumph of the hordes", "garruk's uprising", "goreclaw"],
        "type_bias": {"creature": 1.5},
    },
    "Pillow Fort": {
        "commander_kw": ["opponents can't attack you", "can't attack you", "creatures can't attack you",
                         "unless they pay", "whenever a creature attacks you", "whenever an opponent attacks you",
                         "propaganda", "ghostly prison", "sphere of safety", "you have hexproof"],
        "deck_kw": ["propaganda", "ghostly prison", "sphere of safety", "norn's annex", "windborn muse", "crawlspace", "ensnaring bridge", "silent arbiter", "maze of ith", "glacial chasm"],
        "type_bias": {},
    },
    "Forced Combat": {
        "commander_kw": ["goad", "each creature attacks", "creatures attack each combat", "must attack",
                         "can't attack you", "whenever a creature an opponent controls attacks"],
        "deck_kw": ["disrupt decorum", "bloodthirsty blade", "marisi breaker of the coil", "kardur doomscourge", "firkraag cunning instigator", "death kiss"],
        "type_bias": {},
    },
    "Theft": {
        "commander_kw": ["gain control of target", "gain control of target creature", "gain control of target permanent",
                         "you control enchanted", "you control equipped", "play cards exiled with", "stolen"],
        "deck_kw": ["agent of treachery", "bribery", "blatant thievery", "control magic", "treachery", "gilded drake", "mass manipulation", "mind control"],
        "type_bias": {},
    },
    "Discard": {
        "commander_kw": ["discard a card", "each opponent discards", "target player discards", "discards a card",
                         "whenever you discard", "whenever an opponent discards", "madness", "hellbent"],
        "deck_kw": ["waste not", "bottomless pit", "necrogen mists", "oppression", "megrim", "liliana's caress", "fell specter", "waste not"],
        "type_bias": {},
    },
    "Self-Mill": {
        "commander_kw": ["put the top card of your library into your graveyard", "mill", "into your graveyard from",
                         "dredge", "whenever you mill", "surveil", "from the top of your library into your graveyard"],
        "deck_kw": ["mesmeric orb", "hedron crab", "stinkweed imp", "golgari grave-troll", "life from the loam", "splinterfright", "kessig cagebreakers", "syr konrad"],
        "type_bias": {},
    },
    "Big Mana": {
        "commander_kw": ["add {c}{c}", "add {c}{c}{c}", "add an amount of {c}", "mana equal to the number of lands",
                         "whenever you tap a land for mana", "tap for an additional", "your lands produce",
                         "add {g}{g}{g}", "lands you control have", "untap all lands", "add {w}{u}{b}{r}{g}", "nyxbloom"],
        "deck_kw": ["mana reflection", "caged sun", "gauntlet of power", "extraplanar lens", "zendikar resurgent", "nyxbloom ancient", "nykthos shrine to nyx", "cabal coffers", "urborg"],
        "type_bias": {"land": 1.5},
    },
    "Aggro": {
        "commander_kw": ["haste", "whenever this creature attacks", "creatures you control have haste",
                         "whenever a creature you control attacks", "first strike", "double strike"],
        "deck_kw": ["shock", "lightning bolt", "goblin guide", "monastery swiftspear", "signal pest", "bomat courier", "burning-tree emissary", "vexing devil", "ball lightning"],
        "type_bias": {"creature": 1.5},
    },
    "+ExtrA TurnS": {
        "commander_kw": ["take an extra turn", "extra turn after this one", "extra combat", "additional combat phase",
                         "whenever you cast", "beginning of your end step, you may"],
        "deck_kw": ["time warp", "temporal manipulation", "capture of jingzhou", "time stretch", "expropriate", "nexus of fate", "narset enlightened master", "edric spymaster of trest"],
        "type_bias": {},
    },
    "Toolbox": {
        "commander_kw": ["search your library for a creature card", "search your library for an", "reveal cards from",
                         "birthing pod", "survival of the fittest", "chord of calling", "green sun's zenith", "summoner's pact",
                         "whenever you cast a creature spell search", "survival"],
        "deck_kw": ["birthing pod", "chord of calling", "green sun's zenith", "finale of devastation", "worldly tutor", "eladamri's call", "captain sisay", "yisan the wanderer bard"],
        "type_bias": {},
    },
    "Energy": {
        "commander_kw": ["energy counter", "get {e}", "pay {e}", "whenever you get", "energy"],
        "deck_kw": ["aetherworks marvel", "aether hub", "harnessed lightning", "bristling hydra", "rogue refiner", "whirler virtuoso", "aethertide whale"],
        "type_bias": {},
    },
    "Politics / Voting": {
        "commander_kw": ["will of the council", "council's dilemma", "vote", "each player votes", "starting with you, each player",
                         "tempting offer", "join forces", "you may vote an additional time", "goad"],
        "deck_kw": ["council's judgment", "expropriate", "plea for power", "breena the demagogue", "shadrix silverquill"],
        "type_bias": {},
    },
    "Cascade / Discover": {
        "commander_kw": ["cascade", "discover", "whenever you cast your first spell", "exile cards from the top",
                         "cast it without paying its mana cost", "mana value less than"],
        "deck_kw": ["maelstrom wanderer", "apex devastator", "the first sliver", "bloodbraid elf", "shardless agent", "brass's tunnel-grinder", "geological appraiser"],
        "type_bias": {},
    },
    "Cycling": {
        "commander_kw": ["cycling", "discard this card", "whenever you cycle", "whenever you discard a card",
                         "draw a card", "cycle or discard"],
        "deck_kw": ["astral slide", "astral drift", "archfiend of ifnir", "fluctuator", "new perspectives", "zenith flare", "gavi nest warden"],
        "type_bias": {},
    },
    "Dredge": {
        "commander_kw": ["dredge", "put the top", "cards of your library into your graveyard", "from your graveyard",
                         "whenever a creature card is put into your graveyard", "narcomeba", "prized amalgam"],
        "deck_kw": ["stinkweed imp", "golgari grave-troll", "life from the loam", "dakmor salvage", "narcomeba", "prized amalgam", "creeping chill", "golgari thug"],
        "type_bias": {},
    },
    "Hatebears": {
        "commander_kw": ["opponents can't", "players can't", "creatures your opponents control enter tapped",
                         "whenever an opponent", "tax", "cost more to cast", "unless they pay"],
        "deck_kw": ["thalia guardian of thraben", "gaddock teeg", "collector ouphe", "hushbringer", "drannith magistrate", "aven mindcensor", "kataki war's wage", "containment priest", "eidolon of rhetoric"],
        "type_bias": {},
    },
    "Lifedrain": {
        "commander_kw": ["lose life and you gain that much", "each opponent loses life and you gain", "drain",
                         "loses life", "you gain that much life", "lose that much life"],
        "deck_kw": ["exsanguinate", "torment of hailfire", "debt to the deathless", "gray merchant of asphodel", "blood artist", "zulaport cutthroat", "pontiff of blight", "vito thorn of the dusk rose"],
        "type_bias": {},
    },
    "Food": {
        "commander_kw": ["food", "create a food token", "whenever you sacrifice a food", "for each food",
                         "whenever a food enters", "sacrifice a food"],
        "deck_kw": ["trail of crumbs", "feasting hobbit", "gilded goose", "cauldron familiar", "witch's oven", "peregrin took", "samwise gamgee"],
        "type_bias": {},
    },
    "Monarch": {
        "commander_kw": ["monarch", "you're the monarch", "you become the monarch", "whenever you become the monarch",
                         "at the beginning of your end step if you're the monarch"],
        "deck_kw": ["court of", "palace jailer", "throne of the high city", "archon of coronation", "embodiment of agonies", "marchesa's decree", "skyline despot"],
        "type_bias": {},
    },
    "Clues / Investigate": {
        "commander_kw": ["clue", "investigate", "create a clue", "whenever you investigate", "sacrifice a clue",
                         "for each clue", "draw a card", "sacrifice two clues"],
        "deck_kw": ["march of the machine", "tireless tracker", "briarbridge patrol", "confirm suspicions", "fleeting memories", "ongoing investigation", "tamiyo's journal"],
        "type_bias": {},
    },
    "Cantrips": {
        "commander_kw": ["draw a card", "scry", "whenever you cast an instant or sorcery", "whenever you cast your first",
                         "cantrip", "whenever you draw", "instant and sorcery spells"],
        "deck_kw": ["opt", "ponder", "preordain", "brainstorm", "serum visions", "sleight of hand", "gitaxian probe", "consider", "thought scour"],
        "type_bias": {"instant": 1.0, "sorcery": 1.0},
    },
    "-1/-1 Counters": {
        "commander_kw": ["-1/-1 counter", "put a -1/-1 counter", "with -1/-1 counters", "for each -1/-1 counter",
                         "whenever you put a -1/-1 counter", "wither", "infect"],
        "deck_kw": ["hapatra vizier of poisons", "blowfly infestation", "crumbling ashes", "nest of scarabs", "scorpion god", "skinrender", "contagion engine", "black sun's zenith"],
        "type_bias": {},
    },
    "Land Destruction": {
        "commander_kw": ["destroy target land", "sacrifice a land", "each player sacrifices a land",
                         "lands can't", "land enters tapped", "players can't search", "search their library"],
        "deck_kw": ["strip mine", "wasteland", "stone rain", "blood moon", "magus of the moon", "ruination", "back to basics", "tsabo's web", "price of glory"],
        "type_bias": {},
    },
    "Clones": {
        "commander_kw": ["copy of target creature", "you may have ~ enter as a copy", "becomes a copy",
                         "copy of any creature", "clone", "copies of target", "create a token that's a copy"],
        "deck_kw": ["clone", "clever impersonator", "spark double", "phantasmal image", "phyrexian metamorph", "mirror box", "helm of the host", "sakashima of a thousand faces", "vesuvan duplimancy"],
        "type_bias": {},
    },
    "Dragons": {
        "commander_kw": ["dragon", "commander damage", "flying", "whenever a dragon", "for each dragon you control", "dragons you control"],
        "deck_kw": ["crux of fate", "dragon tempest", "utvara hellkite", "dragonlord", "lathliss dragon queen", "scourge of valkas", "atarka world render", "terror of the peaks", "balefire dragon"],
        "type_bias": {},
    },
    "Goblins": {
        "commander_kw": ["goblin", "krenko", "muxus", "goblins you control", "whenever a goblin", "for each goblin"],
        "deck_kw": ["goblin recruiter", "goblin warchief", "goblin chieftain", "goblin matron", "skirk prospector", "mogg war marshal", "goblin lackey", "conspicuous snoop", "goblin trashmaster"],
        "type_bias": {"creature": 1.2},
    },
    "Elves": {
        "commander_kw": ["elf", "elves", "elvish", "for each elf you control", "whenever you cast an elf", "tap an untapped elf"],
        "deck_kw": ["priest of titania", "elvish mystic", "llanowar elves", "ezuri renegade leader", "elvish archdruid", "wirewood symbiote", "heritage druid", "allosaurus shepherd", "craterhoof behemoth"],
        "type_bias": {"creature": 1.5},
    },
    "Zombies": {
        "commander_kw": ["zombie", "whenever a zombie", "for each zombie", "zombies you control", "you may cast zombie spells"],
        "deck_kw": ["gravecrawler", "zombie master", "cryptbreaker", "diregraf colossus", "rooftop storm", "lord of the accursed", "liliana untouched", "mikaeus the unhallowed", "geralf visionary stitcher"],
        "type_bias": {"creature": 1.2},
    },
    "Slivers": {
        "commander_kw": ["sliver", "all slivers", "slivers you control", "sliver creatures", "the first sliver", "sliver overlord", "sliver hivelord", "sliver legion", "sliver queen", "sliver gravemother"],
        "deck_kw": ["sliver", "crystalline sliver", "hibernation sliver", "gemhide sliver", "manaweft sliver", "harmonic sliver", "predatory sliver", "bonescythe sliver", "cloudshredder sliver"],
        "type_bias": {"creature": 2.0},
    },
    "Eldrazi": {
        "commander_kw": ["eldrazi", "colorless", "annihilator", "devoid", "cast this spell only if", "whenever you cast a colorless spell"],
        "deck_kw": ["eye of ugin", "eldrazi temple", "conduit of ruin", "endless one", "thought-knot seer", "reality smasher", "kozilek", "ulamog", "emrakul", "all is dust", "eldrazi conscription"],
        "type_bias": {},
    },
    "Dinos": {
        "commander_kw": ["dinosaur", "enrage", "whenever a dinosaur", "for each dinosaur", "dinosaurs you control", "discover"],
        "deck_kw": ["zacama primal calamity", "gishath sun's avatar", "polyraptor", "ranging raptors", "ripjaw raptor", "marauding raptor", "wrathful raptors", "regal behemoth", "quartzwood crasher"],
        "type_bias": {"creature": 1.5},
    },
    "Ninjutsu": {
        "commander_kw": ["ninjutsu", "whenever this creature deals combat damage to a player", "whenever a ninja",
                         "unblocked", "can't be blocked", "whenever you draw your second card", "ninja or rogue"],
        "deck_kw": ["ninja of the deep hours", "ingenious infiltrator", "fallen shinobi", "yuriko", "satoru umezawa", "silent-blade oni", "prosperous thief", "moon-circuit hacker", "biting-palm ninja", "ornithopter", "changeling outcast", "mist-syndicate naga"],
        "type_bias": {},
    },
    "Mutate": {
        "commander_kw": ["mutate", "whenever this creature mutates", "mutated creature", "for each time this creature has mutated"],
        "deck_kw": ["auspicious starrix", "gemrazer", "migratory greathorn", "parcelbeast", "pouncing shoreshark", "sea-dasher octopus", "otrimi", "brokkos", "nethroi apex of death", "ivy gleeful spellthief"],
        "type_bias": {},
    },
    "Morph / Manifest": {
        "commander_kw": ["morph", "face down", "manifest", "turn it face up", "whenever a creature is turned face up",
                         "you may look at face-down creatures", "disguise"],
        "deck_kw": ["willbender", "vesuvan shapeshifter", "brine elemental", "kadena slinking sorcerer", "ixidron", "thieving amalgam", "scroll of fate", "ugin's mastery", "primordial mist"],
        "type_bias": {},
    },
    "Sagas": {
        "commander_kw": ["saga", "whenever you put a lore counter", "lore counter", "sagas", "whenever a saga",
                         "when the final chapter", "each saga you control"],
        "deck_kw": ["binding the old gods", "elspeth conquers death", "fable of the mirror-breaker", "urza's saga", "birth of the imperium", "narci fable singer", "tom bombadil", "song of freyalise"],
        "type_bias": {},
    },
    "Dungeon / Venture": {
        "commander_kw": ["dungeon", "venture into the dungeon", "whenever you complete a dungeon", "take the initiative",
                         "when you venture", "whenever you venture"],
        "deck_kw": ["avernus", "lost mine of phandelver", "tomb of annihilation", "undercity", "barrowin of clan undurr", "nadaar selfless paladin", "elder brain", "seasoned dungeoneer", "radiant solar"],
        "type_bias": {},
    },
    "Toughness Matters": {
        "commander_kw": ["toughness", "assigns combat damage equal to its toughness", "base power and toughness",
                         "deal damage equal to its toughness", "whenever a creature with defender", "defender",
                         "walls you control", "creatures you control with defender"],
        "deck_kw": ["arcades the strategist", "doran the siege tower", "assault formation", "huatli the sun's heart", "high alert", "tower defense", "wall of reverence", "aegis of the heavens", "slagwurm armor"],
        "type_bias": {},
    },
    "Spell Copy": {
        "commander_kw": ["copy target instant", "copy target sorcery", "whenever you copy", "whenever you cast an instant or sorcery",
                         "copy that spell", "storms", "whenever you cast or copy", "magecraft"],
        "deck_kw": ["fork", "reverberate", "increasing vengeance", "bonus round", "twinning staff", "thousand-year storm", "double vision", "swarm intelligence", "hive mind", "krark the thumbless", "veyran voice of duality"],
        "type_bias": {},
    },
    "Madness": {
        "commander_kw": ["madness", "discard", "whenever you discard", "whenever you cycle or discard",
                         "discard a card", "hellbent", "whenever an opponent discards", "loot"],
        "deck_kw": ["archfiend of ifnir", "big game hunter", "fiery temper", "alms of the vein", "call to the netherworld", "dark withering", "terminal agony", "kitchen imp", "circular logic", "ancient grudge", "faithless looting", "burning inquiry"],
        "type_bias": {},
    },
    "Topdeck": {
        "commander_kw": ["scry", "look at the top card of your library", "top card of your library", "cards from the top",
                         "put it into your hand", "play with the top card", "you may play cards from the top",
                         "sensi's divining top", "future sight", "whenever you would draw a card"],
        "deck_kw": ["sensi's divining top", "scroll rack", "sylvan library", "mirri's guile", "bolas's citadel", "experimental frenzy", "elminster", "galadriel of lothlorien", "gandalf of the secret fire", "reality chip"],
        "type_bias": {},
    },
    "Convoke": {
        "commander_kw": ["convoke", "tap an untapped creature you control", "whenever you tap a creature for",
                         "creatures you control have convoke"],
        "deck_kw": ["chief engineer", "inspiring statuary", "stonybrook schoolmaster", "loxodon hierarch", "venerated loxodon", "march of the multitudes", "knight-errant of eos", "return triumphant", "hoarding broodlord"],
        "type_bias": {},
    },
    "Party": {
        "commander_kw": ["party", "full party", "cleric rogue warrior wizard", "whenever a creature you control with",
                         "party of creatures", "if you have a full party", "burakos", "najeela"],
        "deck_kw": ["spoils of adventure", "archpriest of iona", "journey to oblivion", "coveted prize", "linvala shield of sea gate", "najeela the blade-blossom", "tazri beacon of unity", "jazal goldmane", "zagras thief of heartbeats"],
        "type_bias": {},
    },
    "Exile": {
        "commander_kw": ["exile", "from exile", "played from exile", "cards you own in exile", "whenever you cast a spell from",
                         "whenever a card is put into exile", "processor", "impulse draw"],
        "deck_kw": ["prosper tome-bound", "opposition agent", "dauthi voidwalker", "loot dispute", "wild-magic sorcerer", "fevered suspicion", "robe of the archmagi", "delayed blast fireball", "voidwalker", "mindslaver"],
        "type_bias": {},
    },
    "Flash": {
        "commander_kw": ["flash", "as though they had flash", "instant speed", "on each player's turn",
                         "during each turn", "whenever you cast an instant", "during your turn cast", "may cast as though"],
        "deck_kw": ["vedalken orrery", "leyline of anticipation", "teferi mage of zhalfir", "yeva nature's herald", "raff capashen ship's mage", "surrak dragonclaw", "shimmer myr", "vivien champion of the wilds", "wavebreak hippocamp"],
        "type_bias": {},
    },
    "Proliferate": {
        "commander_kw": ["proliferate", "whenever you proliferate", "counter on a permanent", "move counters", "for each counter"],
        "deck_kw": ["evolution sage", "flux channeler", "inexorable tide", "contagion engine", "contagion clasp", "throne of geth", "planewide celebration", "staff of compleation", "experimental augury", "drown in ichor", "whisper of the dross"],
        "type_bias": {},
    },
    "Battles": {
        "commander_kw": ["battle", "siege", "defeat a battle", "target battle", "whenever a battle", "protect a battle"],
        "deck_kw": ["invasion of", "battle of", "defeat a battle", "siege veteran", "siege modification", "battle cry goblin"],
        "type_bias": {"battle": 2.5},
    },
    "Defenders": {
        "commander_kw": ["defender", "creatures you control with defender", "walls you control", "whenever a creature with defender",
                         "each creature you control assigns", "deal damage equal to its toughness"],
        "deck_kw": ["arcades the strategist", "wall of blossoms", "wall of omens", "wall of denial", "overgrown battlement", "axebane guardian", "colossus of akros", "fortified rampart", "jungle barrier", "towering titan", "tree of redemption"],
        "type_bias": {},
    },
    "Kicker": {
        "commander_kw": ["kicker", "if it was kicked", "when this spell was kicked", "when kicked", "multikicker"],
        "deck_kw": ["rite of replication", "vile aggregate", "hallar the firefletcher", "verazol the split current", "grunn the lonely king", "josu vess lich knight", "grow from the ashes", "sylvan awakening", "bloodchief's thirst"],
        "type_bias": {},
    },
    "Fight": {
        "commander_kw": ["fights target creature", "fight target creature", "whenever a creature you control fights",
                         "deals damage equal to its power to target", "bites", "fights up to one target"],
        "deck_kw": ["ram through", "bushwhack", "ulvenwald tracker", "voracious hydra", "gruul ragebeast", "apex altisaur", "thrash //", "ezuri's predation", "setessan tactics", "fall of the hammer", "warstorm surge"],
        "type_bias": {},
    },
    "Unblockable": {
        "commander_kw": ["can't be blocked", "unblockable", "can't be blocked except",
                         "whenever this creature deals combat damage to a player", "whenever a creature deals combat damage",
                         "skulk", "protection from creatures"],
        "deck_kw": ["whispersilk cloak", "trailblazer's boots", "aqueous form", "prowler's helm", "rogue's passage", "shadow spear", "key to the city", "cover of darkness", "dauthi embrace", "thassa god of the sea", "sun quan lord of wu"],
        "type_bias": {},
    },
    "Self-Damage": {
        "commander_kw": ["you lose life", "pay life", "deals damage to you", "as an additional cost pay",
                         "whenever you're dealt damage", "whenever you lose life", "life total becomes", "lose half your life"],
        "deck_kw": ["ad nauseam", "necropotence", "bolas's citadel", "toxic deluge", "dark confidant", "unspeakable symbol", "reanimate", "mana crypt", "ancient tomb", "phyrexian mana", "sylvan library", "dismember", "greed"],
        "type_bias": {},
    },
    "Auras": {
        "commander_kw": ["aura", "enchant creature", "enchant player", "enchanted creature", "whenever you cast an aura",
                         "whenever an aura enters", "whenever an aura becomes attached", "attached", "you control enchanted"],
        "deck_kw": ["ethereal armor", "all that glitters", "sram senior edificer", "light-paws emperor's voice", "kestia the cultivator", "timber wolf", "rancor", "spirit mantle", "shielded by faith", "sage's reverie", "flickering ward"],
        "type_bias": {},
    },
    "Historic": {
        "commander_kw": ["historic", "legendary", "artifact", "saga", "whenever you cast a historic spell",
                         "whenever a historic", "historic spells you cast", "legendaries"],
        "deck_kw": ["jhoira weatherlight captain", "teshar ancestor's apostle", "sisay weatherlight captain", "raff capashen ship's mage", "rograkh", "yama", "yomiji who bars the way", "niambi esteemed speaker"],
        "type_bias": {},
    },
    "Graveyard": {
        "commander_kw": ["graveyard", "from your graveyard", "whenever a creature card is put into your graveyard",
                         "cards in your graveyard", "from any graveyard", "into your graveyard"],
        "deck_kw": ["living death", "rise of the dark realms", "mass reanimate", "grave pact", "dictate of erebos", "syr konrad the grim", "mortuary", "volrath's stronghold", "oversold cemetery"],
        "type_bias": {},
    },
    "Flying": {
        "commander_kw": ["flying", "with flying", "creatures with flying", "whenever a creature with flying",
                         "whenever you attack with a creature with flying", "flying creatures"],
        "deck_kw": ["gravitational shift", "favorable winds", "emperor's vanguard", "windreader sphinx", "warden of evos isle", "sky hussar", "pride of the clouds", "thunderclap wyvern"],
        "type_bias": {},
    },
    "Pingers": {
        "commander_kw": ["deals 1 damage to", "deals damage to each opponent", "deals damage to any target",
                         "tap an untapped", "whenever you cast an instant or sorcery", "whenever you draw",
                         "whenever you draw a card", "noncombat damage", "whenever this creature deals damage to an opponent"],
        "deck_kw": ["thermo-alchemist", "firebrand archer", "guttersnipe", "electrostatic field", "kessig flamebreather", "fiery inscription", "erebor flamesmith", "niv-mizzet parun", "ophidian eye", "curiosity"],
        "type_bias": {},
    },
    "Tap / Untap": {
        "commander_kw": ["tap an untapped", "you may tap or untap", "untap target", "tap target",
                         "whenever you tap", "whenever a creature becomes tapped", "whenever you untap",
                         "creatures your opponents control enter the battlefield tapped", "doesn't untap"],
        "deck_kw": ["icy manipulator", "verity circle", "opposition", "glare of subdual", "sleep", "cryptolith rite", "earthcraft", "kelpie guide", "hylda of the icy crown"],
        "type_bias": {},
    },
    "Activated Abilities": {
        "commander_kw": ["activated abilities", "activated abilities of", "cost {1} less to activate",
                         "whenever you activate", "training grounds", "zirda the dawnwaker", "you may activate", "tap an untapped", "abilities of creatures", "abilities of artifacts"],
        "deck_kw": ["training grounds", "zirda the dawnwaker", "biomancer's familiar", "heartstone", "illusionist's bracers", "battlemage's bracers", "rings of brighthearth", "lithoform engine", "agatha of the vile cauldron"],
        "type_bias": {},
    },
    "Prowess": {
        "commander_kw": ["prowess", "whenever you cast an instant or sorcery", "whenever you cast a noncreature spell",
                         "this creature gets +1/+1", "monastery swiftspear", "whenever you cast or copy", "whenever you cast your first"],
        "deck_kw": ["soul-scar mage", "monastery swiftspear", "stormchaser mage", "balmor battlemage captain", "adeliz the cinder wind", "mizzix of the izmagnus", "nivix cyclops", "wee dragonauts"],
        "type_bias": {},
    },
    "Bounce": {
        "commander_kw": ["return target creature to its owner's hand", "return target permanent to its owner's hand",
                         "bounce", "return to hand", "whenever you return", "return target nonland", "return target spell",
                         "whenever a creature you control leaves the battlefield"],
        "deck_kw": ["cyclonic rift", "evacuation", "aetherize", "engulf the shore", "wash out", "wipe away", "hibernation", "token of the sky", "flood of tears", "into the roil", "blink of an eye"],
        "type_bias": {},
    },
    "Weenies": {
        "commander_kw": ["creatures with power 2 or less", "power 1 or less", "small creatures", "whenever a creature with power",
                         "creature tokens you control", "shadow", "each creature you control", "creatures you control get +1/+1"],
        "deck_kw": ["mentor of the meek", "welcoming vampire", "tocasia's welcome", "bennie bracks zoologist", "rumor gatherer", "idol of oblivion", "elesh norn mother of machines", "halo fountain", "castle ardenvale"],
        "type_bias": {},
    },
    "Power Matters": {
        "commander_kw": ["power 4 or greater", "power", "where x is the greatest power", "creatures with power",
                         "greatest power among creatures", "power 5 or greater", "whenever a creature you control with power"],
        "deck_kw": ["garruk's uprising", "elemental bond", "unnatural growth", "pathbreaker ibex", "ghalta primal hunger", "selvala heart of the wilds", "goreclaw terror of qal sisma", "greater good", "rishkar's expertise"],
        "type_bias": {},
    },
    "Eggs": {
        "commander_kw": ["egg", "whenever an egg", "sacrifice an artifact", "whenever you sacrifice", "whenever an artifact is put into",
                         "dies", "from the battlefield to your graveyard", "create a 0/1", "atla palani"],
        "deck_kw": ["chromatic star", "chromatic sphere", "conjurer's bauble", "terrarion", "guild globe", "prophetic prism", "ichor wellspring", "myr retriever", "scrap trawler", "krark-clan ironworks", "ashnod's altar", "atla palani"],
        "type_bias": {},
    },
    "Tron": {
        "commander_kw": ["urza's", "tron", "urza's mine", "urza's power plant", "whenever you assemble", "urza's tower",
                         "if you control an urza's", "cloudpost", "glimmerpost", "whenever you cast a colorless spell"],
        "deck_kw": ["urza's mine", "urza's power plant", "urza's tower", "expedition map", "sylvan scrying", "walking ballista", "wurmcoil engine", "karn liberated", "ugin the spirit dragon", "oblivion stone", "all is dust"],
        "type_bias": {},
    },
    "Adventures": {
        "commander_kw": ["adventure", "cast as an adventure", "creature spell cast from exile",
                         "whenever you cast a creature spell from exile", "adventurer", "whenever you cast a spell from anywhere"],
        "deck_kw": ["lucky clover", "edgewall innkeeper", "cliffgate", "leyline of the meek", "meeting of the five", "spirit of the dragon", "starheim unleashed", "greater gargaroth", "stormkeld vanguard"],
        "type_bias": {},
    },
    "Shrines": {
        "commander_kw": ["shrine", "whenever you cast a shrine", "for each shrine you control", "shrine you control",
                         "whenever a shrine enters", "go-shintai"],
        "deck_kw": ["sanctum of all", "honden of", "go-shintai of", "sanctum of tranquil light", "sanctum of fruitful harvest", "sanctum of shattersoul", "sanctum of calm waters", "sanctum of stone fangs", "sisay weatherlight captain"],
        "type_bias": {},
    },
    "Impulse Draw": {
        "commander_kw": ["exile the top card", "you may play cards exiled", "play cards from exile", "you may play that card",
                         "impulse", "you may look at the top", "you may play the top", "from exile this turn", "from exile until", "prosper tome-bound"],
        "deck_kw": ["visions of phyrexia", "outpost siege", "stolen strategy", "theater of horrors", "valki god of lies", "act on impulse", "commune with lava", "light up the stage", "rob the archives", "professional face-breaker"],
        "type_bias": {},
    },
    "Modular": {
        "commander_kw": ["modular", "+1/+1 counter", "whenever a creature you control with a +1/+1 counter dies",
                         "put a +1/+1 counter", "artifact creature", "zabaz", "whenever an artifact creature"],
        "deck_kw": ["arcbound ravager", "arcbound worker", "arcbound stinger", "arcbound crusher", "arcbound overseer", "hardened scales", "steel overseer", "the ozolith", "walking ballista", "hangarback walker"],
        "type_bias": {"artifact": 1.5},
    },
    "Coin Flip": {
        "commander_kw": ["flip a coin", "coin flip", "if you win the flip", "flip coins", "whenever you flip",
                         "whenever a player flips", "whenever you win a coin flip", "whenever a coin", "frenetic"],
        "deck_kw": ["krark's thumb", "chance encounter", "game of chaos", "impulsive maneuvers", "mirror march", "risky move", "squee's revenge", "stitch in time", "frenetic efreet", "frenetic sliver"],
        "type_bias": {},
    },
    "Scry": {
        "commander_kw": ["scry", "whenever you scry", "look at the top card", "top card of your library",
                         "whenever you would draw a card", "galadriel", "eligeth", "the temporal anchor"],
        "deck_kw": ["precognition field", "eyes everywhere", "sensi's divining top", "mystic speculation", "lost hours", "omen of the sea", "thassa god of the sea", "the temporal anchor", "eligeth crossroads augur", "sigiled starfish", "crystal ball"],
        "type_bias": {},
    },
    "Guildgates": {
        "commander_kw": ["gate", "guildgate", "for each gate", "gates you control", "whenever a gate enters",
                         "search your library for a gate", "nine-fingers keene", "maze's end"],
        "deck_kw": ["maze's end", "circuitous route", "gatecreeper vine", "guild summit", "gatebreaker ram", "district guide", "open the gates", "gond gate", "baldur's gate"],
        "type_bias": {},
    },
    "Surveil": {
        "commander_kw": ["surveil", "whenever you surveil", "look at the top", "scry", "surveil 2",
                         "put it into your graveyard", "whenever a creature card", "into your graveyard from your library"],
        "deck_kw": ["consider", "otherworldly gaze", "dimir spybug", "thoughtbound phantasm", "whispering snitch", "enhanced surveillance", "murmuring mystic", "dimir informant", "sinister sabotage", "disinformation campaign", "doom whisperer"],
        "type_bias": {},
    },
    "Polymorph": {
        "commander_kw": ["polymorph", "reveal cards from the top", "put a creature card from", "into play", "onto the battlefield",
                         "creature card at random", "put it into the battlefield", "cheats", "from your library onto the battlefield"],
        "deck_kw": ["polymorph", "mass polymorph", "divergent transformations", "lukka coppercoat outcast", "jalira master polymorphist", "transmogrify", "reweave", "proteus staff", "synthetic destiny"],
        "type_bias": {},
    },
    "Glass Cannon": {
        "commander_kw": ["sacrifice this creature", "at the beginning of the end step sacrifice", "when you control no other creatures",
                         "can't be blocked", "deals damage to", "double strike", "when this creature dies", "ball lightning",
                         "at the beginning of your end step", "it's sacrificed"],
        "deck_kw": ["ball lightning", "lightning skelemental", "thunderkin awakener", "groundbreaker", "blistering firecat", "hellspark elemental", "hell's thunder", "spark trooper", "nova chaser", "chandra's incinerator"],
        "type_bias": {},
    },
    "Creatureless": {
        "commander_kw": ["noncreature spells", "if you control no creatures", "for each noncreature spell",
                         "instant and sorcery spells", "noncreature sources", "whenever you cast an instant",
                         "whenever you cast a sorcery", "artifact spells"],
        "deck_kw": ["propaganda", "ghostly prison", "ensnaring bridge", "meekstone", "crawlspace", "portcullis", "silent arbiter", "noetic scales", "humility", "moat", "the abyss", "lethal vapors"],
        "type_bias": {"instant": 1.5, "sorcery": 1.5},
    },
    "Hellbent": {
        "commander_kw": ["hellbent", "if you have no cards in hand", "empty your hand", "when you have no cards in hand",
                         "discard your hand", "you have no cards in hand", "as long as you have no cards",
                         "discard all", "if you have one or fewer cards in hand"],
        "deck_kw": ["anthem of rakdos", "cackling imp", "drekavac", "gathan raiders", "pyromancy", "slaughterhouse bouncer", "wandering goblin", "skirk ridge exhumer", "rakdos pit dragon", "infernal tutor", "lions eye diamond"],
        "type_bias": {},
    },
    "Suspend": {
        "commander_kw": ["suspend", "time counters", "when you remove the last time counter", "when this card is unsuspended",
                         "whenever you remove a time counter", "suspend cards", "jhoira of the ghitu"],
        "deck_kw": ["jhoira of the ghitu", "deep-sea kraken", "greater gargaroth", "aeon chronicler", "detritivore", "rift bolt", "search for tomorrow", "the tenth doctor", "clock spinning", "timecrafting", "fury charm", "jhoira's timebug"],
        "type_bias": {},
    },
    "General / Midrange": {
        "commander_kw": [],
        "deck_kw": [],
        "type_bias": {},
    },
}

def detect_archetype(deck: Deck, stats: CategoryStats) -> tuple[str, Dict[str, List[int]], List[Dict[str, Any]]]:
    """Returns (primary_archetype, blended_thresholds, top_archetypes_list)."""
    cmdr_text = (deck.commander.oracle_text or "").lower()
    cmdr_type = (deck.commander.type_line or "").lower()

    all_oracle = " ".join((c.oracle_text or "").lower() for c in deck.cards)
    all_names = " ".join(c.name.lower() for c in deck.cards)

    # ── Deck keyword scores (existing system) ──
    kw_scores: Dict[str, float] = {}
    total_cards = max(sum(
        getattr(stats, t, 0) for t in ['land','creature','artifact','enchantment','instant','sorcery','planeswalker']
    ), 1)

    for arch, sig in ARCHETYPE_SIGNATURES.items():
        if arch == "General / Midrange":
            continue

        score = 0.0
        cmdr_kw_hits = 0
        for kw in sig.get("commander_kw", []):
            if kw in cmdr_text or kw in cmdr_type:
                cmdr_kw_hits += 1
        score += cmdr_kw_hits * 5.0

        for kw in sig.get("deck_kw", []):
            count = all_oracle.count(kw) + all_names.count(kw)
            score += min(count * 1.5, 6.0)

        for type_key, multiplier in sig.get("type_bias", {}).items():
            attr = getattr(stats, type_key, 0)
            ratio = attr / total_cards
            score += min(ratio * 100 * multiplier, 8.0)

        if score > 0:
            kw_scores[arch] = score

    # Normalize keyword scores to [0, 1] — use sigmoid-like: score / (score + 10)
    # This prevents 1-hit wonders from dominating; real archetypes need multiple keyword matches
    kw_norm = {k: v / (v + 10.0) for k, v in kw_scores.items()}

    # ── EDHREC community weights ──
    edhrec_weights: Dict[str, float] = {}
    try:
        edhrec_raw = get_tag_counts(deck.commander.name)
        edhrec_weights = edhrec_tags_to_weights(edhrec_raw)
    except Exception:
        pass  # fallback: EDHREC weights stay empty

    # ── Hybrid blending: 35% EDHREC community + 65% user's deck ──
    all_tags = set(kw_norm.keys()) | set(edhrec_weights.keys())
    scores: Dict[str, float] = {}
    for tag in all_tags:
        kw = kw_norm.get(tag, 0.0)
        ed = edhrec_weights.get(tag, 0.0) * 5  # scale EDHREC to match keyword score range
        scores[tag] = 0.35 * ed + 0.65 * kw

    if not scores:
        default = ARCHETYPE_THRESHOLDS["General / Midrange"]
        return "General / Midrange", default, [{"name": "General / Midrange", "weight": 1.0}]

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Compute weights via unit‑normalization (sum to 1)
    total_score = sum(s for _, s in ranked[:3])
    # take top 3 candidates for blending, but decide how many to keep
    raw_weights = [s / total_score for _, s in ranked[:3]]

    # Decision logic
    if raw_weights[0] > 0.70:
        kept = 1  # single dominant archetype
    elif raw_weights[0] + raw_weights[1] > 0.88:
        kept = 2  # two strong archetypes
    else:
        kept = 3  # three evenly balanced archetypes

    kept = min(kept, len(ranked))
    selected = ranked[:kept]
    kept_weights = [s / sum(s for _, s in selected) for _, s in selected]

    # Blend thresholds
    keys = ["ramp", "draw", "removal", "wipes", "tutors", "interaction", "lands", "cmc"]
    blended: Dict[str, List[int]] = {}
    for key in keys:
        lo = 0.0
        hi = 0.0
        for (arch, _), w in zip(selected, kept_weights):
            t = ARCHETYPE_THRESHOLDS.get(arch, ARCHETYPE_THRESHOLDS["General / Midrange"]).get(key, [10, 14])
            lo += t[0] * w
            hi += t[1] * w
        blended[key] = [round(lo), round(hi)]
    blended["lands"] = [round(blended["lands"][0]), round(blended["lands"][1])]
    blended["cmc"] = [round(blended["cmc"][0] * 10) / 10, round(blended["cmc"][1] * 10) / 10]

    primary = selected[0][0]

    archetypes_list = [
        {"name": arch, "weight": round(w, 2)}
        for (arch, _), w in zip(selected, kept_weights)
    ]

    return primary, blended, archetypes_list

import random
from typing import List, Dict, Any, Optional
from .models import Card, Deck
from .analyzer import categorize

class HandEvaluation:
    def __init__(self, hand: List[Card], commander: Card, partner: Optional[Card] = None):
        self.hand = hand
        self.commander = commander
        self.partner = partner
        self.lands = [c for c in hand if c.type_line and "land" in c.type_line.lower()]
        self.nonlands = [c for c in hand if c not in self.lands]
        self.land_count = len(self.lands)
        self.avg_cmc_nonlands = sum(c.cmc or 0 for c in self.nonlands) / max(len(self.nonlands), 1)

    def _mana_colors_available(self) -> set:
        colors = set()
        for c in self.lands:
            ot = c.oracle_text or ""
            mc = c.mana_cost or ""
            # Basic lands named detection
            name = c.name.lower()
            if "plains" in name:
                colors.add("W")
            if "island" in name:
                colors.add("U")
            if "swamp" in name:
                colors.add("B")
            if "mountain" in name:
                colors.add("R")
            if "forest" in name:
                colors.add("G")
            # Oracle text adds
            for color in ["W", "U", "B", "R", "G"]:
                if f"{{{color.lower()}}}" in ot or f"add {color.lower()}" in ot.lower():
                    colors.add(color)
            # Check color identity as fallback for duals (e.g., Azorius Guildgate)
            for col in (c.color_identity or []):
                colors.add(col)
        return colors

    def _can_cast_commander_by_turn(self, turn: int) -> bool:
        # Commander tax = 2 for each cast beyond first. First cast is base cost.
        # Assume turn N means N lands in play (simplified)
        cost = (self.commander.cmc or 0)
        # We assume first cast from command zone
        needed_lands = max(1, int(cost))
        return len(self.lands) >= needed_lands

    def stats(self) -> Dict[str, Any]:
        colors = list(self._mana_colors_available())
        return {
            "land_count": self.land_count,
            "nonland_count": len(self.nonlands),
            "avg_cmc_nonlands": round(self.avg_cmc_nonlands, 2),
            "colors_available": colors,
            "can_cast_commander_soon": self._can_cast_commander_by_turn(4),
            "has_ramp": any(
                categorize(c).ramp > 0 or (c.type_line and "artifact" in c.type_line.lower() and c.oracle_text and "add {" in c.oracle_text)
                for c in self.nonlands
            ),
            "has_draw": any(categorize(c).draw > 0 for c in self.nonlands),
            "has_removal": any(categorize(c).removal > 0 or categorize(c).wipe > 0 for c in self.nonlands),
            "has_interaction": any(categorize(c).interaction > 0 for c in self.nonlands),
            "cards": [c.name for c in self.hand]
        }

def simulate_opening_hands(deck: Deck, iterations: int = 1000) -> Dict[str, Any]:
    decklist = []
    for c in deck.cards:
        decklist.extend([c] * c.quantity)
    if len(decklist) != 99:
        # Normalize silently for simulation if count is off
        pass

    land_counts = []
    keep_count = 0
    mulligan_count = 0

    for _ in range(iterations):
        hand = random.sample(decklist, 7)
        ev = HandEvaluation(hand, deck.commander, deck.partner)
        land_counts.append(ev.land_count)
        # Simple heuristic for keep
        if 2 <= ev.land_count <= 5:
            keep_count += 1
        else:
            mulligan_count += 1

    avg_lands = sum(land_counts) / len(land_counts) if land_counts else 0
    return {
        "iterations": iterations,
        "average_lands": round(avg_lands, 2),
        "keep_rate": round(keep_count / iterations * 100, 1),
        "mulligan_rate": round(mulligan_count / iterations * 100, 1),
    }

def evaluate_specific_hand(deck: Deck, hand_names: List[str]) -> Dict[str, Any]:
    # Build lookup
    lookup = {}
    for c in deck.cards:
        lookup[c.name.lower()] = c

    hand = []
    missing = []
    for name in hand_names:
        key = name.strip().lower()
        if key in lookup:
            hand.append(lookup[key])
        else:
            missing.append(name)

    if len(hand) != 7:
        return {
            "valid": False,
            "error": f"Mano inválida. Cartas no encontradas en el mazo: {missing}",
        }

    ev = HandEvaluation(hand, deck.commander)
    st = ev.stats()
    st["valid"] = True
    st["missing"] = missing

    # Heuristic decision
    decision = "keep"
    confidence = "media"
    reasons = []

    if st["land_count"] <= 1:
        decision = "mulligan"
        confidence = "alta"
        reasons.append(f"Solo {st['land_count']} tierra(s): muy difícil jugar algo en los primeros turnos.")
    elif st["land_count"] >= 6:
        decision = "mulligan"
        confidence = "alta"
        reasons.append(f"{st['land_count']} tierras: riesgo de 'flood' y no tener acciones.")
    else:
        # 2-5 lands: nuanced
        if not st["has_ramp"] and st["avg_cmc_nonlands"] > 3.5:
            decision = "mulligan"
            confidence = "media"
            reasons.append("Cartas caras en mano pero sin aceleración de maná (ramp).")
        if st["land_count"] == 2 and not st["has_ramp"]:
            decision = "mulligan"
            confidence = "alta"
            reasons.append("Con solo 2 tierras y sin ramp, es probable no poder hacer tu tercer drop.")
        if st["land_count"] == 5 and st["avg_cmc_nonlands"] < 2.5 and st["has_ramp"]:
            # actually maybe keep if we can curve out and have action
            pass
        if not st["can_cast_commander_soon"] and st["land_count"] < 3:
            reasons.append("Costará mucho lanzar al comandante pronto.")
        if st["has_ramp"] and st["land_count"] >= 3:
            reasons.append("Tienes ramp: puedes compensar curva alta.")
        if not reasons:
            reasons.append("Balance razonable de tierras y acciones.")

    if not reasons:
        reasons.append("Mano balanceada.")

    st["heuristic_decision"] = decision
    st["heuristic_confidence"] = confidence
    st["heuristic_reasons"] = reasons
    return st

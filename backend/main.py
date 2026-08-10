import os
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# (models imports already exist above)
from fastapi.staticfiles import StaticFiles
from app.models import AnalyzeRequest, AnalyzeResponse, MulliganRequest, MulliganResponse, Deck
from app.analyzer import (
    parse_decklist, fetch_deck, analyze_deck, split_commander_from_deck,
    find_missing_staples, compare_to_average, detect_combos,
)
from app.simulator import simulate_opening_hands, evaluate_specific_hand
from app.ai_service import generate_deck_report, generate_mulligan_advice
from app.edhrec import get_high_synergy_for_commander, get_new_for_commander

app = FastAPI(title="DeckCoach API", version="1.0.0")

is_dev = os.getenv("DECKCOACH_ENV", "dev") == "dev"
cors_origins = [
    "http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173",
]
if not is_dev:
    cors_origins.append("https://deckcoach.fly.dev")
    cors_origins.append("https://deckcoach.up.railway.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        deck_raw, cmdr_name, partner_name = split_commander_from_deck(req.decklist)
        cmdr_name = req.commander.strip() or cmdr_name
        partner_name = req.partner.strip() or partner_name if req.partner else partner_name

        if not cmdr_name:
            return AnalyzeResponse(
                stats={}, 
                ai_report="No se detectó comandante. Asegúrate de que el comandante esté al final de la lista separado por un espacio en blanco, o marcado con *CMDR*."
            )

        commander_cards = fetch_deck([(1, cmdr_name)])
        commander = commander_cards[0] if commander_cards else None
        if not commander:
            return AnalyzeResponse(stats={}, ai_report=f"No se encontró '{cmdr_name}' en Scryfall.")

        partner_card = None
        if partner_name:
            partner_cards = fetch_deck([(1, partner_name)])
            partner_card = partner_cards[0] if partner_cards else None

        deck_cards = fetch_deck(deck_raw)
        deck_obj = Deck(commander=commander, partner=partner_card, cards=deck_cards)

        stats = analyze_deck(deck_obj)
        stats["opening_hand_simulation"] = simulate_opening_hands(deck_obj, iterations=1000)

        try:
            stats["suggestions"] = find_missing_staples(deck_obj, cmdr_name)
        except Exception as e:
            stats["suggestions"] = {}
            print(f"[suggestions] Error: {e}")

        try:
            stats["deck_comparison"] = compare_to_average(deck_obj, cmdr_name, budget=req.budget)
        except Exception as e:
            stats["deck_comparison"] = {}
            print(f"[deck_comparison] Error: {e}")

        try:
            stats["combos"] = detect_combos(deck_obj, cmdr_name)
        except Exception as e:
            stats["combos"] = []
            print(f"[combos] Error: {e}")

        try:
            stats["high_synergy"] = get_high_synergy_for_commander(cmdr_name)
        except Exception as e:
            stats["high_synergy"] = []
            print(f"[high_synergy] Error: {e}")

        try:
            stats["new_cards"] = get_new_for_commander(cmdr_name)
        except Exception as e:
            stats["new_cards"] = []
            print(f"[new_cards] Error: {e}")

        report = generate_deck_report(stats) if req.use_ai else ""
        return AnalyzeResponse(stats=stats, ai_report=report)
    except Exception as e:
        traceback.print_exc()
        return AnalyzeResponse(stats={"error": str(e)}, ai_report=f"Error interno: {e}")

@app.post("/api/mulligan")
def mulligan(req: MulliganRequest) -> MulliganResponse:
    deck_raw, cmdr_name, partner_name = split_commander_from_deck(req.decklist)
    cmdr_name = req.commander.strip() or cmdr_name

    if not cmdr_name:
        return MulliganResponse(decision="unknown", confidence="baja", reasoning="No se detectó comandante.", hand_stats={})

    commander_cards = fetch_deck([(1, cmdr_name)])
    commander = commander_cards[0] if commander_cards else None
    if not commander:
        return MulliganResponse(decision="unknown", confidence="baja", reasoning=f"No se encontró '{cmdr_name}' en Scryfall.", hand_stats={})

    partner_card = None
    if partner_name:
        partner_cards = fetch_deck([(1, partner_name)])
        partner_card = partner_cards[0] if partner_cards else None

    deck_cards = fetch_deck(deck_raw)
    deck_obj = Deck(commander=commander, partner=partner_card, cards=deck_cards)

    deck_stats = analyze_deck(deck_obj)

    hand_stats = evaluate_specific_hand(deck_obj, req.hand)
    if not hand_stats.get("valid"):
        return MulliganResponse(decision="invalid", confidence="baja", reasoning=hand_stats.get("error", ""), hand_stats=hand_stats)

    reasoning = generate_mulligan_advice(hand_stats, deck_stats) if req.use_ai else ""
    return MulliganResponse(
        decision=hand_stats["heuristic_decision"],
        confidence=hand_stats["heuristic_confidence"],
        reasoning=reasoning,
        hand_stats=hand_stats,
    )

# ── Serve built frontend in production ──
if not is_dev:
    dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.exists(dist_path):
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
        print(f"[DeckCoach] Serving frontend from {dist_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

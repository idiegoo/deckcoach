import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import AnalyzeRequest, AnalyzeResponse, MulliganRequest, MulliganResponse, Deck
from app.analyzer import parse_decklist, fetch_deck, analyze_deck, split_commander_from_deck
from app.simulator import simulate_opening_hands, evaluate_specific_hand
from app.ai_service import generate_deck_report, generate_mulligan_advice

app = FastAPI(title="DeckCoach API", version="1.0.0")

origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

import traceback

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        # Auto-detect commander from decklist
        deck_raw, cmdr_name = split_commander_from_deck(req.decklist)
        cmdr_name = req.commander.strip() or cmdr_name  # explicit commander overrides auto-detect

        if not cmdr_name:
            return AnalyzeResponse(
                stats={}, 
                ai_report="No se detectó comandante. Asegúrate de que el comandante esté al final de la lista separado por un espacio en blanco, o marcado con *CMDR*."
            )

        commander_cards = fetch_deck([(1, cmdr_name)])
        commander = commander_cards[0] if commander_cards else None
        if not commander:
            return AnalyzeResponse(stats={}, ai_report=f"No se encontró '{cmdr_name}' en Scryfall.")

        deck_cards = fetch_deck(deck_raw)
        deck_obj = Deck(commander=commander, cards=deck_cards)

        stats = analyze_deck(deck_obj)
        stats["opening_hand_simulation"] = simulate_opening_hands(deck_obj, iterations=1000)

        report = generate_deck_report(stats) if req.use_ai else ""
        return AnalyzeResponse(stats=stats, ai_report=report)
    except Exception as e:
        traceback.print_exc()
        return AnalyzeResponse(stats={"error": str(e)}, ai_report=f"Error interno: {e}")

@app.post("/api/mulligan")
def mulligan(req: MulliganRequest) -> MulliganResponse:
    deck_raw, cmdr_name = split_commander_from_deck(req.decklist)
    cmdr_name = req.commander.strip() or cmdr_name

    if not cmdr_name:
        return MulliganResponse(decision="unknown", confidence="baja", reasoning="No se detectó comandante.", hand_stats={})

    commander_cards = fetch_deck([(1, cmdr_name)])
    commander = commander_cards[0] if commander_cards else None
    if not commander:
        return MulliganResponse(decision="unknown", confidence="baja", reasoning=f"No se encontró '{cmdr_name}' en Scryfall.", hand_stats={})

    deck_cards = fetch_deck(deck_raw)
    deck_obj = Deck(commander=commander, cards=deck_cards)

    # Analyze deck for context
    deck_stats = analyze_deck(deck_obj)

    # Evaluate hand
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

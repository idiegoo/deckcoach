from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Card(BaseModel):
    name: str
    quantity: int = 1
    cmc: Optional[float] = None
    colors: Optional[List[str]] = None
    color_identity: Optional[List[str]] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    image_url: Optional[str] = None
    image_url_back: Optional[str] = None
    mana_cost: Optional[str] = None

class Deck(BaseModel):
    commander: Card
    partner: Optional[Card] = None
    cards: List[Card]

class AnalyzeRequest(BaseModel):
    decklist: str
    commander: str = ""
    partner: Optional[str] = None
    format: str = "commander"
    use_ai: bool = True
    budget: Optional[str] = None  # None = normal, "budget", "expensive"

class AnalyzeResponse(BaseModel):
    stats: Dict[str, Any]
    ai_report: str

class StapleSuggestion(BaseModel):
    name: str
    inclusion_pct: float
    category: str

class ComboInfo(BaseModel):
    combo_id: str
    description: str
    produces: List[str] = []
    cards_in_deck: List[str] = []
    missing_pieces: List[str] = []
    is_complete: bool = False
    mana_needed: str = ""
    bracket: str = ""
    prerequisites: str = ""

class MulliganRequest(BaseModel):
    decklist: str
    commander: str = ""
    hand: List[str]
    use_ai: bool = True

class MulliganResponse(BaseModel):
    decision: str
    confidence: str
    reasoning: str
    hand_stats: Dict[str, Any]

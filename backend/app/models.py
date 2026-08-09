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

class AnalyzeResponse(BaseModel):
    stats: Dict[str, Any]
    ai_report: str

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

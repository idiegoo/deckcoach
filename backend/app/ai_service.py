import os
import json
from openai import OpenAI
from typing import Dict, Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Allow None for graceful degradation (AI endpoints return placeholder)
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "Eres un coach paciente de Magic: The Gathering para jugadores novatos en formato Commander (EDH). "
    "Explicas en español de forma clara, coloquial y amigable. Evitas la jerga muy técnica a menos que la expliques. "
    "Usa analogías simples cuando sea útil. Sé conciso pero completo. Máximo 5-6 puntos clave."
)

DECK_ANALYSIS_PROMPT = """
Analiza el siguiente mazo de Commander para un jugador novato.

Datos duros del mazo (en JSON):
{stats}

El sistema ha detectado que este mazo probablemente es del arquetipo: **{archetype}**.
Los umbrales recomendados para este arquetipo son: {thresholds}

Basándote en esos datos, genera un reporte con:
1. Evaluación general (1 frase): ¿parece un mazo funcional para empezar? Si los números no coinciden con lo esperado para el arquetipo "{archetype}", menciónalo.
2. Curva de maná: ¿está bien distribuido o hay un cuello de botella en algún coste?
3. Base de maná: ¿suficientes tierras y fuentes de aceleración/ramp para el arquetipo?
4. Balance de cartas: ¿hay suficiente remoción, draw, y formas de recuperarse considerando que el mazo es "{archetype}"?
5. Comandante: ¿qué rol tiene el comandante y cómo encaja con la temática "{archetype}"?
6. 2-3 consejos prácticos y concretos para mejorar el mazo sin gastar mucho dinero, pensando en la estrategia del arquetipo.

Responde en español, tono amable y para novatos.
"""

MULLIGAN_PROMPT = """
Un jugador novato de Commander te pregunta si debe quedarse con su mano inicial o hacer mulligan.

Datos de su mano (en JSON):
{hand_stats}

Contexto del mazo:
- Commander: {commander_name} (coste: {commander_cost})
- Promedio de CMC del mazo: {avg_cmc}
- Total de tierras en mazo: {total_lands}
- Arquetipo detectado: {archetype}

Decisión heurística del sistema: {system_decision} (confianza: {system_confidence}). Razones del sistema: {system_reasons}

Tu tarea:
1. Di claramente "Quédate" o "Haz mulligan".
2. Explica por qué en 2-3 frases cortas, pensando en un novato.
3. Menciona qué buscaría en una mano ideal para este comandante, considerando que el arquetipo es "{archetype}".
4. Si hay una carta específica en su mano que es muy buena o mala en este contexto, menciónala.

Responde en español coloquial y amable.
"""


def generate_deck_report(stats: Dict[str, Any]) -> str:
    if client is None:
        return "[Modo sin API Key] No se puede generar análisis con IA. Configura OPENAI_API_KEY en el entorno."
    archetype = stats.get("archetype", "General / Midrange")
    thresholds = stats.get("archetype_thresholds", {})
    prompt = DECK_ANALYSIS_PROMPT.format(
        stats=json.dumps(stats, ensure_ascii=False, indent=2),
        archetype=archetype,
        thresholds=json.dumps(thresholds, ensure_ascii=False),
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"Error al contactar la IA: {str(e)}"


def generate_mulligan_advice(hand_stats: Dict[str, Any], deck_stats: Dict[str, Any]) -> str:
    if client is None:
        return "[Modo sin API Key] Configura OPENAI_API_KEY para consejos de IA."
    commander = deck_stats.get("commander", {})
    archetype = deck_stats.get("archetype", "General / Midrange")
    prompt = MULLIGAN_PROMPT.format(
        hand_stats=json.dumps(hand_stats, ensure_ascii=False, indent=2),
        commander_name=commander.get("name", "Comandante"),
        commander_cost=commander.get("mana_cost", "?"),
        avg_cmc=deck_stats.get("average_cmc", "?"),
        total_lands=deck_stats.get("categories", {}).get("lands", "?"),
        archetype=archetype,
        system_decision=hand_stats.get("heuristic_decision", "keep"),
        system_confidence=hand_stats.get("heuristic_confidence", "media"),
        system_reasons="; ".join(hand_stats.get("heuristic_reasons", []))
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"Error al contactar la IA: {str(e)}"

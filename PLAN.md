# Plan de Expansión — DeckCoach

## Features a agregar

| # | Feature | Fuente | Impacto |
|---|---------|--------|---------|
| 1 | **Staples faltantes** — cartas que le faltan al mazo según EDHREC | `pyedhrec` | ⭐⭐⭐⭐⭐ |
| 2 | **Comparación vs mazo promedio** — similitud, diferencias, curva vs avg | `pyedhrec` | ⭐⭐⭐⭐⭐ |
| 4 | **Detección de combos** — combos completos e incompletos | `commanderspellbook.com` API | ⭐⭐⭐⭐ |
| 5 | **Cartas de alta sinergia** — joyas ocultas para el comandante | `pyedhrec` | ⭐⭐⭐⭐ |
| 6 | **Cartas nuevas/trending** — recién populares | `pyedhrec` | ⭐⭐⭐ |
| 7 | **Versiones budget/expensive** — filtro por presupuesto | `pyedhrec` | ⭐⭐⭐ |
| B | **Partner commanders** — soporte real | (interno) | ⭐⭐⭐ |

---

## Fase 1 — Backend Foundations

### 1.1 `python main.py`
- Agregar `if __name__ == "__main__": uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)`

### 1.2 `requirements.txt`
- Agregar `pyedhrec`

### 1.3 Refactor `edhrec.py`
- Mantener `get_tag_counts()` vía `json.edhrec.com` (archetype detection)
- Agregar pyedhrec-powered functions con cache a disco:
  - `get_all_cardlists(commander)` — 1 call, extrae todo
  - `get_top_cards_by_category(commander)` → `{creatures: [...], ramp: [...], ...}`
  - `get_average_decklist(commander, budget=None)` → mazo promedio
  - `get_high_synergy_cards(commander)` → alta sinergia
  - `get_new_cards(commander)` → trending

### 1.4 Nuevos modelos (`models.py`)
- `StapleSuggestion(name, inclusion_pct, category)`
- `DeckComparison(similarity_pct, avg_lands, user_lands, ...)`
- `ComboInfo(combo_id, description, produces, cards_in_deck, missing_pieces, is_complete, ...)`
- `AnalyzeRequest.budget: Optional[str]`

### 1.5 Partner commanders
- `split_commander_from_deck()` → detectar 2+ cartas con `*CMDR*`
- `analyze_deck()` → color_identity combinada
- `detect_archetype()` → keywords de ambos
- `main.py` → crear `Card` de partner, pasar al `Deck`

---

## Fase 2 — Features Backend

### 2.1 Missing Staples (`analyzer.py: find_missing_staples()`)
- Top cards por categoría vía pyedhrec
- Cruzar vs mazo del usuario
- Retornar faltantes con % inclusión, agrupados por categoría

### 2.2 Deck Comparison (`analyzer.py: compare_to_average()`)
- Obtener mazo promedio (normal/budget/expensive)
- Jaccard similarity
- Comparar lands, curva, distribución

### 2.3 Combo Detection (`analyzer.py: detect_combos()`)
- POST a `https://backend.commanderspellbook.com/find-my-combos`
- Payload: `{"cards": [...todas las cartas...]}`
- Procesar `included` + `almostIncluded`

### 2.4 Integrar en `/api/analyze` (`main.py`)
- Ejecutar en parallel
- Agregar al dict `stats`

---

## Fase 3 — Frontend

### 3.1 Sistema de íconos (`SvgIcon.tsx`)
- SVGs de Magic para mana symbols, tipos de carta, habilidades
- Reemplazar `ManaCost.tsx` actual

### 3.2 Componentes nuevos
| Componente | Contenido |
|---|---|
| `StaplesPanel.tsx` | Faltantes por categoría con % |
| `DeckComparison.tsx` | % similitud, comparación lands/curva |
| `ComboPanel.tsx` | Combos completos + casi completos |
| `BudgetToggle.tsx` | Normal / Budget / Expensive |

### 3.3 Integrar en `AnalysisReport.tsx`
- Insertar nuevas secciones
- Partner en commander banner

---

## Fase 4 — Documentación

- README actualizado con nuevos features
- Instrucciones de setup detalladas

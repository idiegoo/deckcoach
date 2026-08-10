# 🧙 DeckCoach

Coach de Magic: The Gathering para jugadores de Commander (EDH). Analiza tu mazo con datos reales de EDHREC y Scryfall, detecta arquetipos, encuentra combos, sugiere mejoras y te ayuda a decidir si hacer mulligan.

## 🚀 Quick Start

### Requisitos

- **Python 3.10+** con `pip`
- **Node.js 20+** con `npm`
- API key de **OpenAI** (opcional — la app funciona con y sin IA)

### 1. Configurar API Key (opcional)

```bash
cd backend
cp .env.example .env
# Edita .env y pega tu OPENAI_API_KEY
```

Sin API key la app funciona igual: estadísticas, panel de diagnóstico, sugerencias, combos — todo sin IA.

### 2. Backend (Python/FastAPI)

```bash
cd backend

# Linux / WSL
python3 -m venv venv && source venv/bin/activate

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Opción A: Directo con Python (recomendado para desarrollo)
python main.py

# Opción B: Con uvicorn
uvicorn main:app --reload --port 8000
```

Backend en `http://localhost:8000`.

> En WSL/Linux: si `uvicorn` no se encuentra, activá el venv primero (`source venv/bin/activate`). No uses `apt install uvicorn`.

### 3. Frontend (React/Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend en `http://localhost:5173`.

---

## 📋 Cómo usar

### Pegar un mazo

Pega tu lista en el textarea. El comandante se detecta automáticamente:

- **Moxfield**: comandante al final, separado por blank line
- **Archidekt**: secciones `// Main` y `// Commander`
- **Inline**: marca el comandante con `*CMDR*` o `(Commander)`
- **Sideboard**: las secciones `SIDEBOARD:` y `MAYBEBOARD:` se ignoran automáticamente
- **Partners**: si hay dos comandantes marcados, el segundo se detecta como partner

### Lo que obtienes

| Feature | Descripción |
|---|---|
| **Curva de maná** | Barras por bucket (0-1, 2-3, 4-5, 6+) con CMC promedio |
| **Distribución de tipos** | 9 tipos: Tierras, Criaturas, Artifacts, Encant, Instants, Conjuros, Planesw., Battles, CMC |
| **Roles funcionales** | Ramp, draw, removal, wipes, tutores, interacción, graveyard — click expande la lista de cartas con imágenes |
| **Arquetipos** | 100+ arquetipos detectados con blending híbrido EDHREC (65%) + keywords del mazo (35%) |
| **Umbrales dinámicos** | Rangos óptimo/aceptable/mejorable calculados como promedio ponderado de arquetipos |
| **Simulación Monte Carlo** | 1000 manos iniciales, keep/mulligan rate |
| **Staples que te faltan** | Cartas populares agrupadas por tipo con % de inclusión, sidebar con íconos SVG |
| **Comparación vs promedio** | % similitud con el mazo promedio de EDHREC, cartas únicas y comunes ausentes |
| **Detección de combos** | Combos del comandante vía EDHREC + descripciones paso a paso de Commander Spellbook |
| **Cartas de alta sinergia** | Joyas ocultas con sinergia inusualmente alta para tu comandante |
| **Cartas nuevas/trending** | Qué está ganando popularidad recientemente |
| **Versiones budget/expensive** | Toggle para comparar contra mazo promedio budget, normal o caro |
| **Partners** | Color identity combinada, detección dual automática |
| **Cartas double-faced** | Click en la imagen para girarla (flip 3D), ver ambas caras |
| **Fullscreen** | Click en cualquier carta → modal a pantalla completa |
| **Links a Scryfall** | Click en nombre de carta → página de Scryfall |
| **Símbolos de maná** | Renderizados como SVGs oficiales de Magic |
| **Reporte IA** | GPT-4o-mini contextualizado por arquetipo (opcional, ~$0.0014/sesión) |
| **Responsive** | Sidebar horizontal en mobile, grids adaptativos |

---

## 🎯 Sistema de arquetipos

El sistema combina dos fuentes independientes para determinar los arquetipos:

| Fuente | Peso | Datos |
|---|---|---|
| **Deck keywords** | 65% | Análisis del texto de tus 99 cartas + comandante |
| **EDHREC** | 35% | `tag_counts` reales de la comunidad para ese comandante |

Los umbrales recomendados (ramp, draw, removal, etc.) se calculan como promedio ponderado de los arquetipos detectados. Si EDHREC no responde, se usa solo keywords del mazo.

---

## 📊 Fuentes de datos

| Fuente | Qué provee | Método |
|---|---|---|
| **Scryfall Local DB** | 38k cartas (oracle_cards) | Descarga única (~23MB), refresh cada 7 días, 0 HTTP en el 99% de consultas |
| **Scryfall API** | Cartas nuevas/raras | Fallback con fuzzy search para renames/UB |
| **EDHREC (json.edhrec.com)** | Tag counts para arquetipos | Cache 24h en `data/edhrec/` |
| **pyedhrec (NextJS API)** | Top cards, sinergia, trending, mazo promedio, combos | Cache 24h en disco |
| **Commander Spellbook** | Descripciones paso a paso de combos | Scraping del search page, cache 24h en `data/combos/` |
| **OpenAI (gpt-4o-mini)** | Reportes narrativos en español | Opcional, ~$0.0014/sesión |

---

## 📁 Estructura

```
deckcoach/
├── backend/
│   ├── main.py                    # FastAPI: /api/analyze, /api/mulligan
│   ├── .env.example               # OPENAI_API_KEY template
│   ├── requirements.txt           # Python deps
│   ├── app/
│   │   ├── models.py              # Pydantic: Card, Deck, AnalyzeRequest, ComboInfo, etc.
│   │   ├── scryfall.py            # Scryfall API client + local DB + retry/fuzzy
│   │   ├── card_db.py             # Local card database (oracle_cards bulk download)
│   │   ├── edhrec.py              # EDHREC: tag_counts + pyedhrec (top cards, sinergia, combos)
│   │   ├── analyzer.py            # Deck parsing, categorization, archetype detection + staples + combos
│   │   ├── simulator.py           # Monte Carlo hand simulation + mulligan evaluation
│   │   └── ai_service.py          # OpenAI integration (gpt-4o-mini)
│   └── data/
│       ├── scryfall_db.json       # Local card DB (63MB, auto-downloaded)
│       ├── scryfall_cache.json    # API response cache
│       ├── edhrec/                # EDHREC per-commander cache
│       └── combos/                # Combo data cache
├── frontend/
│   ├── public/svg/                # 300+ Magic: The Gathering SVG icons (Keyrune)
│   └── src/
│       ├── App.tsx                # Layout, tabs, toggle IA, budget
│       ├── components/
│       │   ├── DeckInput.tsx      # Decklist input + AI toggle
│       │   ├── AnalysisReport.tsx # Full report: stats, diagnostic, curve, simulation
│       │   ├── MulliganCoach.tsx  # Mulligan advisor
│       │   ├── StaplesPanel.tsx   # Missing staples with category sidebar + images
│       │   ├── DeckComparison.tsx # Average deck comparison
│       │   ├── ComboPanel.tsx     # Combo detection with CSB descriptions + card images
│       │   ├── BudgetToggle.tsx   # Normal/Budget/Expensive filter
│       │   ├── FlipCardImage.tsx  # Double-faced card flip animation (3D)
│       │   ├── CardModalContext.tsx # Global fullscreen card viewer
│       │   ├── ManaCost.tsx       # Mana symbols as colored SVGs
│       │   ├── ManaText.tsx       # Inline mana symbols in text ({2}{G}{U})
│       │   ├── SvgIcon.tsx        # Generic Magic SVG icon
│       │   └── Icons.tsx          # Wizard logo SVG
│       └── services/
│           └── api.ts             # Axios API client
├── Dockerfile                     # Multi-stage: Node build → Python runtime
├── fly.toml                       # Fly.io deployment config
├── railway.json                   # Railway deployment config
├── PLAN.md                        # Feature implementation plan
└── README.md                      # This file
```

---

## 🧠 IA y costos

La IA está **desactivada por defecto**. Activá el toggle "Análisis con IA" para obtener reportes narrativos.

| Acción | Modelo | Costo aprox |
|---|---|---|
| Análisis de mazo | gpt-4o-mini | $0.0008 |
| Consejo mulligan | gpt-4o-mini | $0.0006 |
| **Total sesión** | | **~$0.0014** |

La simulación de manos corre en Python puro. El LLM traduce datos y arquetipos a lenguaje natural.

---

## 🔮 Roadmap / Futuras features

- **Análisis con IA** — reportes narrativos del coach usando GPT-4o-mini para estadísticas, curva de maná y balance de cartas
- **Descripciones IA para combos** — generación automática de explicaciones paso a paso para combos que no tengan descripción en Commander Spellbook
- **Historial de análisis** — guardar mazos analizados y comparar evolución
- **Exportar análisis** — PDF o imagen del reporte para compartir
- **Modo multiplayer** — sesiones compartidas para revisar mazos en grupo

---

## ⚠️ Notas técnicas

- **Base de datos local**: descarga `oracle_cards` de Scryfall (~23MB comprimido, 38k cartas) → `scryfall_db.json` (63MB). Se refresca cada 7 días. El 99% de las consultas se resuelven sin HTTP.
- **Rate limiting Scryfall**: la DB local elimina los rate limits. Si la API falla (429), aplica retry con backoff suave.
- **Fuzzy search**: cartas con nombres alternativos (UB, silver-bordered, renames) se resuelven automáticamente.
- **Double-faced cards**: indexadas tanto por nombre completo como solo cara frontal. Imágenes de ambas caras disponibles.
- **Cachés**: todos los caches externos (EDHREC, CSB, pyedhrec) usan TTL de 24h en disco.
- **Sideboard**: detectado y filtrado automáticamente en `parse_decklist` y `split_commander_from_deck`.

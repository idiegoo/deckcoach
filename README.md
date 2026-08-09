# 🧙 DeckCoach

Coach de Magic: The Gathering para jugadores novatos de Commander (EDH). Analiza tu mazo, detecta automáticamente el comandante y los arquetipos temáticos con datos reales de EDHREC, ajusta las recomendaciones y te ayuda a decidir si hacer mulligan.

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

Sin API key la app funciona igual: estadísticas y panel de diagnóstico completo.

### 2. Backend (Python/FastAPI)

```bash
cd backend

# Linux / WSL
python3 -m venv venv && source venv/bin/activate

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend en `http://localhost:8000`.

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

Pega tu lista de 99 cartas en el textarea. **No necesitas escribir el comandante aparte** — el sistema lo detecta automáticamente:

- **Moxfield**: el comandante va al final, separado por un espacio en blanco
  ```
  1 Sol Ring
  1 Arcane Signet
  37 Plains

  1 Tivit, Seller of Secrets
  ```
- **Archidekt**: usa secciones `// Main` y `// Commander`
  ```
  // Main
  1 Sol Ring
  ...
  // Commander
  1 Krenko, Mob Boss
  ```
- **Inline**: marca el comandante con `*CMDR*` o `(Commander)`

### Lo que obtienes

- **Curva de maná** con barras y CMC promedio
- **Distribución de tipos** (criaturas, instants, artifacts, etc.)
- **Roles funcionales** detectados con heurísticas: ramp, draw, removal, wipes, tutores, interacción, graveyard
- **Clickea cualquier categoría** para ver exactamente qué cartas la componen (animación expand/colapse)
- **Detección de arquetipos** híbrida: tags reales de EDHREC + análisis de tu mazo
- **Umbrales dinámicos combinados**: los rangos "óptimo/aceptable/mejorable" son promedio ponderado de todos los arquetipos detectados
- **Tierras + CMC recomendados** según los arquetipos combinados (con estatus verde/amarillo/rojo)
- **Simulación Monte Carlo** de 1000 manos iniciales
- **Reporte del coach IA** (opcional, toggle) contextualizado a los arquetipos

### Coach de Mulligan

Pestaña **Mulligan**: escribí tu mano de 7 cartas (separadas por coma o una por línea). El sistema usará el mazo de la pestaña Análisis.

### Toggle de IA

| Modo | Sin IA | Con IA |
|------|--------|--------|
| Deck | Panel de diagnóstico + badges + lista de cartas | Reporte narrativo en español |
| Mulligan | Razones heurísticas del sistema | Consejo narrativo del coach |
| Costo | Gratis | ~$0.0014/sesión (gpt-4o-mini) |

---

## 🎯 Sistema de arquetipos — blending híbrido EDHREC + deck

### Dos fuentes de datos, un solo score

El sistema combina **dos fuentes independientes** para determinar los arquetipos de tu mazo:

| Fuente | Peso | Qué mide |
|--------|------|----------|
| **EDHREC** (`tag_counts`) | 35% | Cómo construye la comunidad ese comandante (datos reales de miles de decks) |
| **Deck keywords** | 65% | Qué sinergias elegiste VOS en tu mazo (análisis de tus 99 cartas) |

Esto significa que si tu mazo se desvía del arquetipo comunitario hacia una sinergia niche, el sistema lo detecta y ajusta los pesos. Ej: Y'shtola es "Control" en EDHREC, pero si armaste una versión Lifegain, Lifegain sube en el ranking aunque la comunidad no lo juegue tanto.

### Algoritmo de scoring

1. **Keyword matching del mazo**: cada arquetipo tiene `commander_kw` (×5 puntos por hit en texto del comandante) y `deck_kw` (×1.5 por hit en las 99 cartas, cap 6). El type bias suma hasta 8 puntos por proporción de tipos de carta.
2. **Normalización sigmoid**: `kw_score / (kw_score + 10)` — evita que un solo keyword domine, exige múltiples coincidencias para un score alto.
3. **EDHREC tag_counts**: se consulta `json.edhrec.com` → se obtienen los tags reales del comandante con conteos de decks → se normalizan a [0,1] y se escalan ×5.
4. **Blending**: `score[tag] = 0.35 × EDHREC + 0.65 × deck_keywords`
5. **Selección adaptativa**:
   - Arquetipo dominante > 70% → **1 arquetipo**
   - Top 2 suman > 88% → **2 arquetipos**
   - Caso contrario → **3 arquetipos balanceados**

### Blending de thresholds

Los umbrales recomendados se calculan como **promedio ponderado** de los thresholds de cada arquetipo detectado:

```
Deck 60% cEDH + 40% Spellslinger
Tierras: 0.6 × [27,30] + 0.4 × [32,36] = [29, 32]
Ramp:   0.6 × [8,12]  + 0.4 × [8,12]  = [8, 12]
```

### Visualización

En el banner del comandante y en el panel de diagnóstico se muestran **hasta 3 badges** con el nombre del arquetipo y su peso porcentual. El badge primario va resaltado en índigo, los secundarios en gris. Si hay un solo arquetipo dominante, se omite el porcentaje.

### Fallback

Si EDHREC no responde (sin conexión, rate limit), el sistema usa exclusivamente los keywords del mazo. El caché de EDHREC dura 24 horas para minimizar requests.

---

## 📊 Arquetipos detectados (100+ tags)

| Categoría | Arquetipos |
|-----------|-----------|
| **Estrategia** | cEDH / Combo, Control / Stax, Aggro, Midrange |
| **Mecánica** | Spellslinger, Storm, Reanimator, Blink / ETB, Mill, Wheels, Burn, Cascade / Discover, Cycling, Dredge, Cantrips, Extra Turns, X Spells, Toolbox, Sacrifice, Self-Mill, Spell Copy, Ninjutsu, Mutate, Morph, Flash, Bounce, Prowess, Madness, Hellbent, Suspend, Polymorph |
| **Temática** | Artifacts, Enchantress, Equipment, Voltron, Tokens, +1/+1 Counters, -1/-1 Counters, Aristocrats, Lifegain, Lifedrain, Group Hug, Group Slug, Politics / Voting, Monarch, Treasure, Food, Clues / Investigate, Energy, Superfriends, Auras, Sagas, Shrines, Adventures, Dungeon, Battles |
| **Control/Stax** | Pillow Fort, Hatebears, Land Destruction, Discard, Forced Combat, Theft, Chaos, Creatureless, Prison, Counterspells |
| **Ramp/Tierras** | Lands / Landfall, Big Mana, Stompy, Kicker, Tron, Guildgates |
| **Tribal** | Tribal / Typal, Dragons, Goblins, Elves, Zombies, Slivers, Eldrazi, Dinos, Clones, Party, Defenders, Weenies |
| **Especializados** | Pingers, Tap/Untap, Activated Abilities, Topdeck, Scry, Impulse Draw, Coin Flip, Modular, Eggs, Exile, Surveil, Proliferate, Self-Damage, Glass Cannon, Fight, Unblockable, Power Matters, Toughness Matters, Flying, Convoke, Graveyard, Histórico |
| **Fallback** | General / Midrange |

| Arquetipo | Ramp | Draw | Removal | Wipes | Tutores | Interacción | Tierras | CMC |
|-----------|------|------|---------|-------|---------|-------------|---------|-----|
| cEDH / Combo | 8–12 | 10–16 | 4–7 | 0–2 | 8–14 | 10–16 | 27–30 | 1.5–2.2 |
| Spellslinger | 8–12 | 12–18 | 6–10 | 2–4 | 2–5 | 6–10 | 32–36 | 2.0–2.8 |
| Voltron | 8–12 | 6–10 | 4–8 | 2–4 | 4–8 | 4–8 | 33–37 | 2.0–2.8 |
| Lands / Landfall | 14–22 | 8–12 | 5–9 | 2–4 | 2–6 | 4–8 | 38–45 | 2.5–3.5 |
| Artifacts | 12–18 | 8–12 | 5–9 | 2–4 | 4–8 | 4–8 | 30–35 | 2.0–2.8 |
| Enchantress | 8–12 | 8–12 | 5–9 | 2–4 | 3–6 | 6–10 | 34–37 | 2.5–3.5 |
| Tokens | 8–12 | 8–12 | 4–8 | 2–4 | 2–5 | 4–8 | 34–37 | 2.5–3.5 |
| Control / Stax | 8–12 | 8–12 | 8–14 | 3–6 | 3–6 | 10–16 | 35–38 | 2.5–3.2 |
| Dragons | 12–18 | 8–12 | 5–9 | 2–4 | 2–5 | 4–8 | 35–40 | 3.0–4.5 |
| Goblins | 6–10 | 8–12 | 4–8 | 1–3 | 2–5 | 4–8 | 32–36 | 1.8–2.8 |
| Elves | 12–18 | 8–12 | 4–8 | 1–3 | 4–8 | 4–8 | 30–34 | 1.8–2.8 |
| Eldrazi | 12–18 | 6–10 | 4–8 | 2–4 | 2–5 | 4–8 | 34–38 | 3.5–5.5 |
| Ninjutsu | 6–10 | 10–15 | 4–8 | 2–4 | 2–5 | 6–10 | 32–36 | 2.5–4.0 |
| Storm | 6–10 | 12–18 | 2–5 | 0–2 | 3–6 | 6–10 | 28–32 | 1.2–2.0 |
| Lifegain | 8–12 | 8–12 | 6–10 | 2–4 | 2–4 | 4–8 | 34–37 | 2.5–3.5 |
| Reanimator | 8–12 | 10–15 | 6–10 | 2–4 | 4–8 | 4–8 | 34–37 | 2.5–3.5 |
| Aristocrats | 8–12 | 8–12 | 6–10 | 2–4 | 2–6 | 4–8 | 33–37 | 2.0–2.8 |
| Superfriends | 8–12 | 8–12 | 6–10 | 3–6 | 3–6 | 6–10 | 35–39 | 2.8–3.5 |
| Politics / Voting | 8–12 | 10–15 | 4–8 | 2–4 | 2–4 | 4–8 | 35–38 | 2.5–3.5 |
| Infect | 6–10 | 8–12 | 4–8 | 0–2 | 2–4 | 6–10 | 32–36 | 1.8–2.5 |
| General / Midrange | 10–14 | 10–15 | 8–14 | 2–5 | 2–6 | 6–12 | 35–38 | 2.5–3.5 |

---

## 📁 Estructura

```
deckcoach/
├── backend/
│   ├── main.py                  # FastAPI app (/api/analyze, /api/mulligan)
│   ├── .env.example
│   ├── requirements.txt
│   ├── app/
│   │   ├── models.py            # Pydantic models
│   │   ├── scryfall.py          # Scryfall API client + card cache
│   │   ├── edhrec.py            # EDHREC client + 24h cache + tag mapping (80+ tags)
│   │   ├── analyzer.py          # Deck analysis, 100+ archetypes, hybrid EDHREC+deck blending
│   │   ├── simulator.py         # Monte Carlo hand simulation + mulligan evaluation
│   │   └── ai_service.py        # OpenAI integration (gpt-4o-mini, contextualizado por arquetipo)
│   └── data/
│       ├── scryfall_cache.json  # Auto-generated card cache
│       └── edhrec/              # EDHREC per-commander cache (24h TTL)
└── frontend/
    ├── public/
    │   └── Mana.svg             # Mana symbol sprite sheet
    └── src/
        ├── App.tsx              # Layout, tabs, toggle IA
        ├── components/
        │   ├── DeckInput.tsx    # Textarea de mazo + toggle IA
        │   ├── AnalysisReport.tsx # Stats, curva, diagnóstico interactivo, badges multi-arquetipo
        │   ├── MulliganCoach.tsx  # Input de mano + resultado mulligan
        │   ├── ManaCost.tsx     # Símbolos de maná estilizados (colores canónicos Magic)
        │   └── Icons.tsx        # SVG logo del wizard
        └── services/
            └── api.ts
```

---

## 🧠 IA y costos

| Acción | Modelo | Costo aprox |
|--------|--------|-------------|
| Análisis de mazo | gpt-4o-mini | $0.0008 |
| Consejo mulligan | gpt-4o-mini | $0.0006 |
| **Total sesión** | | **~$0.0014** |

La simulación de manos corre en Python puro. El LLM traduce datos y arquetipos a lenguaje natural.

---

## ⚠️ Notas

- **EDHREC**: la primera consulta de un comandante tarda ~1s (fetch HTTP a `json.edhrec.com`). Luego usa caché de 24h en `backend/data/edhrec/`. Si EDHREC no responde, el sistema usa exclusivamente keywords del mazo sin perder funcionalidad.
- **User-Agent**: tanto Scryfall como EDHREC requieren User-Agent personalizado. El cliente ya lo incluye (`DeckCoach/1.0`).
- **Caché Scryfall**: solo se guardan resultados exitosos. Fallos de red no se cachean para permitir reintentos.
- **Detección de comandante**: automática por blank line, `// Commander`, `*CMDR*` o `(Commander)`.
- **Heurísticas**: los roles funcionales (ramp, draw, removal) se detectan por keywords en el oracle text. Puede haber falsos positivos.
- **Alpha**: para desarrollo local. Sin autenticación, rate limiting ni base de datos.

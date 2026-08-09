# 🧙 DeckCoach

Coach de Magic: The Gathering para jugadores novatos de Commander (EDH). Analiza tu mazo, detecta automáticamente el comandante y el arquetipo temático, ajusta las recomendaciones y te ayuda a decidir si hacer mulligan.

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
  ```
  1 Tivit, Seller of Secrets *CMDR*
  ```

### Lo que obtienes

- **Curva de maná** con barras y CMC promedio
- **Distribución de tipos** (criaturas, instants, artifacts, etc.)
- **Roles funcionales** detectados con heurísticas: ramp, draw, removal, wipes, tutores, interacción, graveyard
- **Clickea cualquier categoría** para ver exactamente qué cartas la componen (animación expand/colapse)
- **Detección de arquetipo** basada en +300 tags de EDHRec (comandante + composición)
- **Umbrales dinámicos**: los rangos "óptimo/aceptable/mejorable" se ajustan al arquetipo detectado
- **Tierras + CMC recomendados** según el arquetipo (no expandibles, al final del diagnóstico)
- **Simulación Monte Carlo** de 1000 manos iniciales
- **Reporte del coach IA** (opcional) contextualizado al arquetipo

### Coach de Mulligan

Pestaña **Mulligan**: escribí tu mano de 7 cartas (separadas por coma o una por línea). El sistema usará el mazo de la pestaña Análisis.

### Toggle de IA

| Modo | Sin IA | Con IA |
|------|--------|--------|
| Deck | Panel de diagnóstico + badges + lista de cartas | Reporte narrativo en español |
| Mulligan | Razones heurísticas del sistema | Consejo narrativo del coach |
| Costo | Gratis | ~$0.0014/sesión (gpt-4o-mini) |

---

## 🎯 Multi-arquetipo con blending ponderado

El sistema detecta **hasta 3 arquetipos simultáneos** del mazo y los combina con pesos estadísticos. Esto refleja que los mazos reales de Commander rara vez son de una sola temática — un deck de Krenko es Goblins + Tokens + Tribal.

### Algoritmo de scoring

1. **Keyword matching**: cada arquetipo tiene `commander_kw` (keywords buscadas en el texto y tipo del comandante, ×5 puntos) y `deck_kw` (keywords en las 99 cartas, ×1.5 puntos c/u, cap 6)
2. **Type bias**: proporción de tipos de carta en el mazo (criaturas, artifacts, encantamientos, etc.) con multiplicador según arquetipo (cap 8 puntos)
3. **Normalización**: los scores de los top N arquetipos se normalizan para que sumen 1.0
4. **Selección adaptativa**:
   - Si el arquetipo dominante tiene peso > 70% → **1 arquetipo**
   - Si los 2 principales suman > 88% → **2 arquetipos**
   - Caso contrario → **3 arquetipos balanceados**

### Blending de thresholds

Los umbrales recomendados (ramp, draw, removal, wipes, tutores, interacción, tierras, CMC) se calculan como **promedio ponderado** de los thresholds de cada arquetipo detectado, usando sus pesos normalizados. Ejemplo:

- Deck 60% cEDH + 40% Spellslinger
- Tierras: `0.6 × [27,30] + 0.4 × [32,36] = [29, 32]`
- Ramp: `0.6 × [8,12] + 0.4 × [8,12] = [8, 12]`

Esto produce umbrales híbridos que reflejan la naturaleza mixta del mazo.

### Visualización

En el banner del comandante y en el panel de diagnóstico se muestran **hasta 3 badges** con el nombre del arquetipo y su peso porcentual (ej: `Goblins 47%`, `Tribal / Typal 30%`, `Tokens 23%`). El badge primario va resaltado, los secundarios en tono gris.

---

## 📊 Arquetipos detectados (100+ basados en EDHRec)

| Categoría | Arquetipos |
|-----------|-----------|
| **Estrategia** | cEDH / Combo, Control / Stax, Aggro, Tempo, Midrange |
| **Mecánica** | Spellslinger, Storm, Reanimator, Blink / ETB, Mill, Wheels, Burn, Cascade / Discover, Cycling, Dredge, Cantrips, Extra Turns, X Spells, Toolbox, Sacrifice, Self-Mill |
| **Temática** | Artifacts, Enchantress, Equipment, Voltron, Tokens, +1/+1 Counters, -1/-1 Counters, Aristocrats, Lifegain, Lifedrain, Group Hug, Group Slug, Politics / Voting, Monarch, Treasure, Food, Clues / Investigate, Energy, Superfriends |
| **Control** | Control / Stax, Pillow Fort, Hatebears, Land Destruction, Discard, Forced Combat, Theft, Chaos |
| **Ramp** | Lands / Landfall, Big Mana, Stompy |
| **Tribal** | Tribal / Typal, Dragons, Goblins, Elves, Zombies, Slivers, Eldrazi, Dinos, Clones |
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
| +1/+1 Counters | 8–12 | 8–12 | 6–10 | 2–4 | 2–5 | 4–8 | 34–38 | 2.5–3.5 |
| Aristocrats | 8–12 | 8–12 | 6–10 | 2–4 | 2–6 | 4–8 | 33–37 | 2.0–2.8 |
| Control / Stax | 8–12 | 8–12 | 8–14 | 3–6 | 3–6 | 10–16 | 35–38 | 2.5–3.2 |
| Group Hug | 10–16 | 12–18 | 4–7 | 2–4 | 2–4 | 4–8 | 35–38 | 2.5–3.5 |
| Lifegain | 8–12 | 8–12 | 6–10 | 2–4 | 2–4 | 4–8 | 34–37 | 2.5–3.5 |
| Storm | 6–10 | 12–18 | 2–5 | 0–2 | 3–6 | 6–10 | 28–32 | 1.2–2.0 |
| Reanimator | 8–12 | 10–15 | 6–10 | 2–4 | 4–8 | 4–8 | 34–37 | 2.5–3.5 |
| Dragons | 12–18 | 8–12 | 5–9 | 2–4 | 2–5 | 4–8 | 35–40 | 3.0–4.5 |
| Goblins | 6–10 | 8–12 | 4–8 | 1–3 | 2–5 | 4–8 | 32–36 | 1.8–2.8 |
| Elves | 12–18 | 8–12 | 4–8 | 1–3 | 4–8 | 4–8 | 30–34 | 1.8–2.8 |
| Eldrazi | 12–18 | 6–10 | 4–8 | 2–4 | 2–5 | 4–8 | 34–38 | 3.5–5.5 |
| Energy | 8–12 | 8–12 | 5–9 | 2–4 | 2–5 | 4–8 | 34–37 | 2.5–3.2 |
| Infect | 6–10 | 8–12 | 4–8 | 0–2 | 2–4 | 6–10 | 32–36 | 1.8–2.5 |
| Politics / Voting | 8–12 | 10–15 | 4–8 | 2–4 | 2–4 | 4–8 | 35–38 | 2.5–3.5 |
| Superfriends | 8–12 | 8–12 | 6–10 | 3–6 | 3–6 | 6–10 | 35–39 | 2.8–3.5 |
| General / Midrange | 10–14 | 10–15 | 8–14 | 2–5 | 2–6 | 6–12 | 35–38 | 2.5–3.5 |

+ Además: Auras, Historic, Graveyard, Flying, Pingers, Tap/Untap, Activated Abilities, Prowess, Bounce, Weenies, Power Matters, Eggs, Tron, Adventures, Shrines, Impulse Draw, Modular, Coin Flip, Scry, Guildgates, Surveil, Polymorph, Glass Cannon, Creatureless, Hellbent, Suspend, y todos los anteriores (60+ tags adicionales).

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
│   │   ├── scryfall.py          # Scryfall API client + cache
│   │   ├── analyzer.py          # Deck analysis, 100+ archetype tags, multi-archetype blending
│   │   ├── simulator.py         # Monte Carlo hand simulation + mulligan eval
│   │   └── ai_service.py        # OpenAI integration (gpt-4o-mini, contextualizado al arquetipo)
│   └── data/
│       └── scryfall_cache.json
└── frontend/
    ├── public/
    │   └── Mana.svg             # Sprite con símbolos de maná SVG
    └── src/
        ├── App.tsx              # Layout, tabs, toggle IA
        ├── components/
        │   ├── DeckInput.tsx    # Textarea de mazo + toggle IA
        │   ├── AnalysisReport.tsx # Stats, curva, diagnóstico interactivo, badges multi-arquetipo
        │   ├── MulliganCoach.tsx  # Input de mano + resultado mulligan
        │   ├── ManaCost.tsx     # Símbolos de maná estilizados (CSS gradients)
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

La simulación de manos corre en Python puro. El LLM traduce los datos y arquetipo a lenguaje natural.

---

## ⚠️ Notas

- **User-Agent**: Scryfall requiere User-Agent personalizado. El cliente lo incluye (`DeckCoach/1.0`).
- **Caché**: solo se guardan resultados exitosos en `scryfall_cache.json`. Fallos de red no persisten.
- **Detección de comandante**: automática por blank line, `// Commander`, `*CMDR*` o `(Commander)`. También podés pasar `commander` explícito en el JSON de la request.
- **Heurísticas**: los roles funcionales y arquetipos se detectan por keywords. Puede haber falsos positivos.
- **Alpha**: para desarrollo local. Sin auth, rate limiting ni DB.

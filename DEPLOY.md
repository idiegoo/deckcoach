# 🚀 Deploy — DeckCoach

Guía paso a paso para deployar DeckCoach en producción.

## Requisitos previos

- Cuenta en [Fly.io](https://fly.io) o [Railway](https://railway.app)
- API key de OpenAI (opcional, para reportes IA)
- Git con el código pusheado a un repo

---

## Opción 1: Fly.io (recomendado)

Fly.io soporta volúmenes persistentes, ideal para la DB de cartas.

### 1. Instalar Fly CLI

```bash
# Linux/WSL
curl -L https://fly.io/install.sh | sh

# macOS
brew install flyctl

# Login
fly auth signup
```

### 2. Crear volumen persistente

El volumen guarda `scryfall_db.json` (63MB) y todos los caches entre deploys.

```bash
fly volumes create deckcoach_data --size 1 --region gru
```

- `--size 1`: 1 GB
- `--region gru`: São Paulo. Cambia por `mia`, `dfw`, o el que prefieras.

### 3. Setear secretos

```bash
fly secrets set OPENAI_API_KEY=sk-tu-key-aqui
```

### 4. Deployar

```bash
fly launch   # Ya existe fly.toml
fly deploy
```

La primera vez descarga la DB de Scryfall (~15 segundos). Luego usa el volumen persistente.

### 5. Abrir

```bash
fly open
```

### Comandos útiles

```bash
fly logs          # Logs en tiempo real
fly status        # Estado de la máquina
fly ssh console   # Shell del contenedor
```

---

## Opción 2: Railway

### 1. Instalar Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Crear proyecto y volumen

```bash
railway init
railway volume add -m /app/data
```

### 3. Variables de entorno

En el dashboard de Railway:

```
OPENAI_API_KEY=sk-tu-key-aqui
PORT=8000
```

### 4. Deployar

```bash
railway up
```

Railway detecta `railway.json` y usa el `Dockerfile` automáticamente.

---

## Opción 3: Docker (manual)

### Build

```bash
docker build -t deckcoach .
```

### Run

```bash
docker run -d \
  --name deckcoach \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-tu-key-aqui \
  -v deckcoach_data:/app/data \
  deckcoach
```

### Sin Docker (VPS Linux)

```bash
git clone https://github.com/tu-usuario/deckcoach.git
cd deckcoach

# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Variables de entorno
export DECKCOACH_ENV=production
export OPENAI_API_KEY=sk-...
export DECKCOACH_DATA_DIR=/home/deckcoach/data

# Build frontend
cd ../frontend
npm install && npm run build

# Iniciar
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

En producción, FastAPI sirve el frontend compilado desde `frontend/dist/`.
No se necesita Node en runtime.

---

## Cómo funciona en producción

1. FastAPI arranca en `:8000` con `DECKCOACH_ENV=production`
2. Primera request: descarga `oracle_cards` de Scryfall (~23MB comprimido → 63MB) → `/app/data/scryfall_db.json`
3. Requests siguientes: 99% de consultas resueltas desde DB local (0 HTTP)
4. Cachés (EDHREC, Commander Spellbook, pyedhrec) persisten en `/app/data/` con TTL 24h
5. Frontend servido como archivos estáticos desde la misma instancia

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | (vacío) | API key de OpenAI para reportes IA |
| `DECKCOACH_ENV` | `dev` | `dev` o `production` |
| `DECKCOACH_DATA_DIR` | `backend/data` | Directorio para caches y DB local |
| `PORT` | `8000` | Puerto HTTP |

## Solución de problemas

### "No se encontró la carta X en Scryfall"

La DB local puede estar desactualizada. Borra el cache:

```bash
rm /app/data/scryfall_db.json
# Reinicia — se descarga automáticamente
```

### Rate limiting de Scryfall

La DB local elimina los rate limits. Si ves errores 429, es porque la DB no se cargó correctamente.

### Volumen no persiste en Fly.io

```bash
fly volumes list
# Si no existe, crealo:
fly volumes create deckcoach_data --size 1
```

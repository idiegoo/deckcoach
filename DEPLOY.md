# 🚀 Deploy — DeckCoach

## Opción gratuita: Cloudflare Tunnel

La forma más rápida de compartir tu app. Requiere que tu PC esté encendida.

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Tunnel (comparte esta URL)
cloudflared tunnel --url http://localhost:5173
```

Te da una URL tipo `https://xxx.trycloudflare.com`. La compartís y listo. Se muere al cerrar la terminal.

---

## Opción persistente: Fly.io

Fly.io tiene un **free allowance** que cubre una app pequeña sin costo. Solo requiere tarjeta para verificación (no te cobran si no excedés los límites).

### 1. Instalar Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth signup
```

### 2. Crear volumen (1GB)

```bash
fly volumes create deckcoach_data --size 1
```

### 3. Setear secretos

```bash
fly secrets set OPENAI_API_KEY=sk-...
```

### 4. Deployar

```bash
fly launch
fly deploy
```

### 5. Abrir

```bash
fly open
```

---

## Opción: Docker

```bash
docker build -t deckcoach .
docker run -d --name deckcoach -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -v deckcoach_data:/app/data \
  deckcoach
```

---

## Cómo funciona en producción

1. FastAPI arranca en `:8000` con `DECKCOACH_ENV=production`
2. Sirve el frontend compilado desde `frontend/dist/`
3. Primera request: descarga oracle_cards de Scryfall (~23MB) → **SQLite** (`scryfall.db`, ~94MB)
4. Requests siguientes: 99% de consultas resueltas desde SQLite (~0 RAM extra, <1ms)
5. Cachés persisten en volumen

### SQLite vs JSON (anterior)

| | JSON | SQLite |
|---|---|---|
| Cold start | ~2-3s parseando 63MB | ~0.1s |
| RAM extra | ~200MB | ~0MB |
| Lookup | 0ms (dict) | <1ms (B-tree) |

---

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | (vacío) | API key para reportes IA |
| `DECKCOACH_ENV` | `dev` | `dev` o `production` |
| `DECKCOACH_DATA_DIR` | `backend/data` | Directorio de datos |
| `PORT` | `8000` | Puerto HTTP |

---

## Troubleshooting

### "No se encontró la carta X"

DB desactualizada:

```bash
rm /app/data/scryfall.db
# Reinicia — se reconstruye automáticamente
```

### Rate limiting de Scryfall

La DB local elimina rate limits. Si ves 429, la DB no se cargó. Reinicia.

### Volumen no persiste en Fly.io

```bash
fly volumes list
fly volumes create deckcoach_data --size 1
```

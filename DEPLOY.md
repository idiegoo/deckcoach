# 🚀 Deploy — DeckCoach

## Opción recomendada: Render (gratis, sin tarjeta)

Render ofrece 512MB RAM, HTTPS, dominio `.onrender.com`. Totalmente gratis, no requiere tarjeta.

**Contra**: el servicio se duerme tras 15 min sin tráfico. Se soluciona con [UptimeRobot](https://uptimerobot.com) (ping cada 14 min, también gratis).

### 1. Buildear el frontend

Render no soporta builds multi-stage. Hay que buildear local y commitear `dist/`:

```bash
cd frontend
npm install
npm run build
cd ..

# Commitear el build para que Render lo sirva
git add frontend/dist/ -f
git commit -m "Add frontend build for Render"
git push
```

### 2. Crear Web Service en Render

1. Andá a https://dashboard.render.com → New → Web Service
2. Conectá tu repo de GitHub
3. Configurá:

   | Campo | Valor |
   |---|---|
   | **Root Directory** | `backend` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### 3. Variables de entorno

En el dashboard de Render → Environment:

```
DECKCOACH_ENV=production
DECKCOACH_DATA_DIR=/opt/render/project/src/data
PYTHON_VERSION=3.12.0
OPENAI_API_KEY=sk-...          (opcional)
PORT=8000
```

### 4. Mantenerlo despierto

Creá cuenta gratis en https://uptimerobot.com → New Monitor:

| Campo | Valor |
|---|---|
| **Monitor Type** | HTTP(s) |
| **URL** | `https://tu-app.onrender.com/api/health` |
| **Monitoring Interval** | 14 minutes |

Listo. Tu app corre 24/7 sin costo.

**Tips de velocidad en Render:**
- La DB se precarga al iniciar (`on_event("startup")`), no espera al primer request
- El Build Command descarga la DB durante el deploy, no en cada cold start
- Plan Starter ($7/mes) elimina cold starts por completo
- Para más workers: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT`

---

## Opción rápida: Cloudflare Tunnel

Ideal para compartir el link con amigos. Requiere que tu PC esté encendida.

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Tunnel
cloudflared tunnel --url http://localhost:5173
```

Compartí la URL `https://xxx.trycloudflare.com`. Se muere al cerrar la terminal.

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
4. Requests siguientes: 99% consultas desde SQLite (~0 RAM, <1ms)
5. Cachés persisten en `/app/data/`

---

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | (vacío) | API key para reportes IA |
| `DECKCOACH_ENV` | `dev` | `dev` o `production` |
| `DECKCOACH_DATA_DIR` | `backend/data` | Directorio de datos |
| `PORT` | `8000` | Puerto HTTP |

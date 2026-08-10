# 🚀 Deploy — DeckCoach

## Arquitectura recomendada: Vercel (frontend) + Render (backend)

Separar frontend y backend optimiza velocidad, evita OOM, y ambos son 100% gratis (sin tarjeta).

```
Usuario → Vercel (CDN global, estáticos) → api.ts → Render (Python/FastAPI)
```

---

## 1. Frontend en Vercel (gratis, sin tarjeta)

### 1.1 Preparar el código

El frontend ya está listo. La única configuración necesaria ya está hecha:

- `src/services/api.ts`: usa `VITE_API_URL` como baseURL (si no está definida, usa `/api` para dev local)
- `vite.config.ts`: proxy a `localhost:8000` en desarrollo

### 1.2 Deployar en Vercel

1. Andá a https://vercel.com → **New Project**
2. Importá tu repo de GitHub
3. Vercel detecta Vite. Verificá que la configuración sea:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (por defecto)
   - **Output Directory**: `dist` (por defecto)
4. **Variables de entorno** (Settings → Environment Variables):
   ```
   VITE_API_URL=https://tu-app.onrender.com
   ```
   Reemplazá `tu-app` por el nombre real de tu servicio en Render.
5. Click **Deploy**. Vercel te da un dominio `https://tu-app.vercel.app`.

> Si no sabés aún la URL de Render, deployá Vercel primero sin `VITE_API_URL`, luego agregala cuando tengas la URL de Render y redeployá.

---

## 2. Backend en Render (gratis, sin tarjeta)

### 2.1 Preparar el código

Ya está todo listo:
- `DECKCOACH_ENV=production` activa CORS para `*.vercel.app` y `*.onrender.com`
- La DB se precarga en startup (`on_event`)
- Art series/tokens se filtran al buildear la DB
- Timeout wrappers protegen contra cold starts lentos

### 2.2 Deployar en Render

1. Andá a https://dashboard.render.com → **New → Web Service**
2. Conectá tu repo de GitHub
3. Configurá:

   | Campo | Valor |
   |---|---|
   | **Root Directory** | `backend` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

4. **Variables de entorno** (Environment):

   ```
   DECKCOACH_ENV=production
   DECKCOACH_DATA_DIR=/opt/render/project/src/data
   PYTHON_VERSION=3.12.0
   PORT=8000
   ```

5. Click **Create Web Service**. Render te da `https://tu-app.onrender.com`.

### 2.3 Verificar

```bash
curl https://tu-app.onrender.com/api/health
# Debe devolver: {"status":"ok","db":"loaded"}
```

### 2.4 Mantener vivo

[UptimeRobot](https://uptimerobot.com) (gratis) → New Monitor:
- **Monitor Type**: HTTP(s)
- **URL**: `https://tu-app.onrender.com/api/health`
- **Interval**: 14 minutes

---

## 3. Variables de entorno

| Variable | Dónde | Default | Descripción |
|---|---|---|---|
| `VITE_API_URL` | Vercel | `/api` | URL del backend en Render |
| `DECKCOACH_ENV` | Render | `dev` | `production` para activar CORS |
| `DECKCOACH_DATA_DIR` | Render | `backend/data` | Directorio de datos |
| `OPENAI_API_KEY` | Render | (vacío) | API key para reportes IA |
| `PORT` | Render | `8000` | Puerto HTTP |

---

## 4. Troubleshooting

### 502 Bad Gateway en /api/analyze

El backend tardó más de 30s (timeout de Render) o crasheó por OOM.

1. Verificá el health: `curl https://tu-app.onrender.com/api/health`
2. Si responde `{"status":"ok","db":"loaded"}`, la DB está lista. El primer request de análisis puede tardar ~15s. Reintentá.
3. Si responde `{"status":"ok","db":"pending"}`, la DB no se cargó. Revisá los logs de Render (hay un botón "Logs" en el dashboard).
4. Si no responde nada, la app crasheó. Revisá los logs.

### OOM (Out of Memory)

Si ves `Ran out of memory` en los logs de Render:

1. Verificá que `PYTHON_VERSION=3.12.0` esté en las variables de entorno
2. Borrá el disco de Render y redeployá (el volumen puede tener archivos corruptos o muy grandes)
3. Si persiste, considerá el plan Starter ($7/mes, 1GB RAM)

### CORS errors en el navegador

Asegurate de que:
1. `DECKCOACH_ENV=production` esté en Render
2. `VITE_API_URL` en Vercel apunte a la URL correcta de Render
3. La URL de Vercel esté en los CORS origins de `main.py` (ya está: `*.vercel.app`)

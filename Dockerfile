# ── Stage 1: Build frontend ──
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python runtime ──
FROM python:3.12-slim
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Copy built frontend
COPY --from=frontend-build /build/dist ./frontend/dist

# Mount data volume
VOLUME /app/data

# Serve frontend + API from FastAPI
ENV DECKCOACH_ENV=production
ENV DECKCOACH_DATA_DIR=/app/data
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

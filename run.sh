#!/usr/bin/env bash
# Levanta backend (FastAPI :8000) y frontend (Next.js :3000) juntos.
# Uso:  ./run.sh
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Backend ─────────────────────────────────────────────
cd "$ROOT/backend"
if [ ! -d venv ]; then
  echo "▶ Creando entorno virtual (Python 3.12)…"
  python3.12 -m venv venv
  ./venv/bin/pip install -q --upgrade pip
  ./venv/bin/pip install -q -r requirements.txt
  ./venv/bin/python -m spacy download es_core_news_md
fi
echo "▶ Backend en http://localhost:8000"
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACK_PID=$!

# ── Frontend ────────────────────────────────────────────
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  echo "▶ Instalando dependencias del frontend…"
  npm install
fi
echo "▶ Frontend en http://localhost:3000"
npm run dev &
FRONT_PID=$!

trap "kill $BACK_PID $FRONT_PID 2>/dev/null" EXIT
wait

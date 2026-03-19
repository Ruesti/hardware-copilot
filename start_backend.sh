#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d "backend/.venv" ]; then
  echo "Fehler: backend/.venv nicht gefunden. Bitte zuerst ./bootstrap.sh ausführen."
  exit 1
fi

source backend/.venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
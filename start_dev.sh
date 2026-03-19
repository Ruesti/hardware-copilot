#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d "backend/.venv" ]; then
  echo "Fehler: backend/.venv nicht gefunden. Bitte zuerst ./bootstrap.sh ausführen."
  exit 1
fi

if ! command -v gnome-terminal >/dev/null 2>&1; then
  echo "Fehler: gnome-terminal nicht gefunden."
  echo "Starte dann separat mit:"
  echo "  ./start_backend.sh"
  echo "  ./start_tauri.sh"
  exit 1
fi

gnome-terminal -- bash -lc '
cd "'"$(pwd)"'"
source backend/.venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
exec bash
'

sleep 2

gnome-terminal -- bash -lc '
cd "'"$(pwd)"'"
npm run tauri dev
exec bash
'

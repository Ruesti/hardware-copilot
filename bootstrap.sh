#!/usr/bin/env bash
set -e

echo "==> Hardware Copilot bootstrap"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Fehler: python3 nicht gefunden"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Fehler: npm nicht gefunden"
  exit 1
fi

echo "==> Python virtual environment anlegen"
python3 -m venv backend/.venv

echo "==> Python dependencies installieren"
source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
deactivate

echo "==> Node dependencies installieren"
npm install

echo "==> Bootstrap abgeschlossen"

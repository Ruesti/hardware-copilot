#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d "backend/.venv" ]; then
  echo "Fehler: backend/.venv nicht gefunden. Bitte zuerst ./bootstrap.sh ausführen."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "node_modules nicht gefunden — führe 'npm install' aus..."
  npm install
fi

BACKEND_PID=""

cleanup() {
  echo
  echo "Beende Backend..."
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starte Backend (uvicorn) auf http://127.0.0.1:8000 ..."
(
  source backend/.venv/bin/activate
  exec uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

sleep 2

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Fehler: Backend konnte nicht gestartet werden."
  exit 1
fi

echo "Starte Tauri (npm run tauri dev) ..."

# VS Code Snap injiziert Snap-Pfade (GTK_PATH, LOCPATH, GIO_MODULE_DIR, ...),
# die native Linux-Binaries (z.B. Tauri) brechen. Original-Werte wiederherstellen
# bzw. die problematischen Variablen entfernen.
restore_or_unset() {
  local var="$1"
  local orig_var="${var}_VSCODE_SNAP_ORIG"
  if [ -n "${!orig_var+x}" ]; then
    if [ -z "${!orig_var}" ]; then
      unset "$var"
    else
      export "$var=${!orig_var}"
    fi
  else
    unset "$var"
  fi
}

for v in GTK_PATH GTK_EXE_PREFIX GTK_IM_MODULE_FILE GIO_MODULE_DIR \
         GSETTINGS_SCHEMA_DIR LOCPATH XDG_DATA_DIRS XDG_DATA_HOME \
         XDG_CONFIG_DIRS LD_LIBRARY_PATH GDK_BACKEND; do
  restore_or_unset "$v"
done

npm run tauri dev

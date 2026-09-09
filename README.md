## Hardware-Copilot

Hardware-Copilot ist das Cockpit einer KI-gestützten Elektronik-Werkstatt:
Die App zeigt den Bauteile-Bestand (Mengen, Fächer, Preise mit Datum,
Alternativen) und die Wissensbasis (belegte Regeln, Verified Blocks,
Lücken-Protokoll). Die KI-Arbeit — Schaltung entwerfen über Konnect/KiCad,
Regeln abfragen, Bestand pflegen — läuft über Claude Code mit den
MCP-Servern `wissensschicht/` und `bestand/`; die Panels lesen dieselbe
Datenschicht (`~/.hardware-copilot/bestand.db` + Wissens-Repo), nie den Chat.
Seit Etappe E4 gibt es den Chat auch direkt in der App: Der Tab „Chat"
spricht über die neutrale Motor-Schnittstelle (`backend/app/motor/`) mit
Claude übers Agent SDK — mit denselben MCP-Werkzeugen; Rückfragen
erscheinen als Karten im Panel, und Bestandsänderungen der KI spiegeln
sofort in den Bestand-Tab. Auth wie Claude Code: Der Chat nutzt dieselbe
Anmeldung — ist `ANTHROPIC_API_KEY` gesetzt, wird darüber abgerechnet;
für Abo-Betrieb die Variable nicht setzen.
Entwurf: `docs/superpowers/specs/2026-09-08-cockpit-bestand-leuchtregal-design.md`.

### Cockpit starten

```bash
# Backend (vom Repo-Root)
./start_backend.sh
# Frontend (zweites Terminal): Browser-Dev oder Tauri-Desktop
npm run dev          # bzw. npm run tauri dev
```

### Tests

```bash
python -m pytest backend/tests/ bestand/tests/ wissensschicht/tests/
npx vitest run && npm run build
```

### Local Development

Typical setup on a fresh machine:

```bash
git clone <repo>
cd hardware-copilot
./bootstrap.sh
./start_dev.sh
```

# 1. Voraussetzungen installieren

## Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  nodejs \
  npm \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

---

# 2. Rust installieren

Falls noch nicht vorhanden:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

---

# 3. Projekt vorbereiten (nur beim ersten Mal oder auf neuem Rechner)

```bash
./bootstrap.sh
```

Dieses Skript erledigt:

- Python virtual environment erzeugen
- Python-Abhängigkeiten installieren
- Node-Abhängigkeiten installieren

---

# 4. Entwicklung starten

```bash
./start_dev.sh
```

Dieses Skript startet:

- FastAPI Backend
- Tauri Frontend

---

# 5. Einzelstart falls nötig

## Backend

```bash
./start_backend.sh
```

## Tauri

```bash
./start_tauri.sh
```

---

# 6. Projektstruktur

```text
hardware-copilot/
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── .venv/
│
├── src/
├── src-tauri/
│
├── bootstrap.sh
├── start_backend.sh
├── start_tauri.sh
├── start_dev.sh
│
├── package.json
├── package-lock.json
├── README.md
└── .gitignore
```

---

# 7. Auf neuem Rechner weiterarbeiten

```bash
git clone <repo>
cd hardware-copilot
./bootstrap.sh
./start_dev.sh
```

---

# 8. Versionsprüfung

```bash
python3 --version
node -v
npm -v
rustc --version
cargo --version
```
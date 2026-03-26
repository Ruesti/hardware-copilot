## Development Status

Hardware Copilot is being built as a desktop-first engineering workbench for hardware-related design workflows.

The current direction is not to let an LLM generate raw KiCad files directly.
Instead, the intended pipeline is:

`Chat -> Spec -> Draft -> Validation -> Export Model -> KiCad Generator`

### Current Baseline

The project already includes a working technical foundation:

- Tauri desktop shell
- React + TypeScript + Vite frontend
- Python + FastAPI backend
- panel-based workbench UI
- selection-driven inspector interaction
- initial backend integration via `GET /project`
- reproducible local development scripts

So the project is already beyond pure mockup stage.

See:
- [`docs/status/current-baseline.md`](docs/status/current-baseline.md)

### Current Active Phase

**Phase 3.1 — Backend Model Hardening**

Current focus:
- introduce Pydantic models
- stabilize API response structures
- align backend models more closely with frontend types
- prepare the backend for persistence and domain growth

See:
- [`docs/roadmap/phases.md`](docs/roadmap/phases.md)

### Next Planned Steps

- expand the backend API beyond `/project`
- introduce SQLite persistence
- build a real component library screen
- expand validation logic
- connect the chat workflow to structured technical draft generation

### Local Development

Typical setup on a fresh machine:

```bash
git clone <repo>
cd hardware-copilot
./bootstrap.sh
./start_dev.sh

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
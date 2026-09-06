# Hardware Copilot

Hardware Copilot is a desktop-first engineering workbench for hardware design workflows: describe a device in chat, get a structured requirements spec, a block-level circuit draft with suggested components and connections, per-block schematic sketches, and AI-driven design validation.

The LLM never generates raw KiCad files directly. The intended pipeline is:

`Chat -> Spec -> Draft -> Validation -> Export Model -> KiCad Generator`

## Tech Stack

- **Desktop shell:** Tauri
- **Frontend:** React + TypeScript + Vite
- **Backend:** Python + FastAPI + SQLite
- **AI:** Anthropic Claude API (chat, circuit drafting, component/connection suggestions, schematic generation, validation, datasheet analysis)
- **Datasheets:** Nexar/Octopart API

## Current Status

**Phases 3.1–4 are complete.** The app is a working AI workbench:

- Persistent multi-project storage (SQLite), project-scoped REST API (~37 endpoints)
- Workbench tab: 3-column layout (Chat | Block diagram | Components by assembly) with resizable panels
- Streaming Claude chat with interview mode; the design (blocks, connections, components) refreshes automatically after every AI turn
- Block diagram (React Flow) with auto-layout, drag-to-reposition, and typed connections
- Per-block ASCII schematic sketches, generated in the background, with a manual "validated" flag that protects them from being overwritten
- Component suggestions including MCU support circuitry (decoupling, pull-ups, boot strapping, reset, crystal/USB-UART)
- Datasheet fetching via Nexar/Octopart with Claude PDF analysis
- AI design validation computed from the persisted project state
- Token/cost tracking per project (`GET /projects/{id}/usage`)
- **KiCad export**: `GET /projects/{id}/export/kicad` generates a self-contained KiCad 9 schematic scaffold (curated part library for pin facts, AI only supplies net semantics) plus a mapping report; export button in the Workbench tab

**Known gaps:**

- Backend has a pytest suite for the KiCad export (28 tests, `kicad-cli sch erc` as oracle); the rest of the backend and the frontend are still untested
- Datasheet-based pin-map extraction for unknown parts (phase 5.2) is not built yet — parts without a library entry appear in the export report instead

See [`docs/roadmap/phases.md`](docs/roadmap/phases.md) for the phase history and what's next, and [`docs/status/current-baseline.md`](docs/status/current-baseline.md) for a snapshot of what exists today.

## Setup

### 1. System prerequisites (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  nodejs npm \
  libwebkit2gtk-4.1-dev build-essential curl wget file \
  libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
```

Rust (required by Tauri), if not installed yet:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

### 2. API keys

All AI features require an Anthropic API key. Datasheet search additionally needs Nexar credentials (free registration at https://nexar.com/api).

```bash
cp backend/.env.example backend/.env
# then edit backend/.env and fill in the keys
```

### 3. Bootstrap (first time on a machine)

```bash
./bootstrap.sh
```

This creates the Python virtual environment and installs Python and Node dependencies.

### 4. Run

```bash
./start_dev.sh      # backend + Tauri frontend together
```

Or individually:

```bash
./start_backend.sh  # FastAPI backend only (http://127.0.0.1:8000)
./start_tauri.sh    # Tauri frontend only
```

## Project Structure

```text
hardware-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI routes (~37 endpoints)
│   │   ├── claude_service.py     # all Claude API calls + prompts
│   │   ├── datasheet_fetcher.py  # Nexar/Octopart integration
│   │   ├── repository.py         # SQLite data access
│   │   ├── db.py                 # schema + migrations
│   │   └── models.py             # Pydantic models
│   ├── data/                     # SQLite database (gitignored)
│   ├── requirements.txt
│   └── .env                      # API keys (gitignored, see .env.example)
├── src/                          # React frontend
├── src-tauri/                    # Tauri shell
└── docs/                         # roadmap, phase specs, status snapshots
```

## Version Check

```bash
python3 --version && node -v && npm -v && rustc --version && cargo --version
```

# Hardware Copilot – Current Baseline

**Snapshot date:** 2026-09-06 (verified against the code on `main`, last feature work 2026-05-26)

This document is a snapshot of what exists and works today. It is not a roadmap — see `docs/roadmap/phases.md` for that.

---

## Project Goal

Hardware Copilot is a desktop-first engineering workbench for hardware design. The LLM never generates raw KiCad files directly; the pipeline is:

`Chat -> Spec -> Draft -> Validation -> Export Model -> KiCad Generator`

Today the pipeline is implemented from Chat through Validation. Export Model and KiCad Generator do not exist yet.

---

## Architecture

- **Tauri** desktop shell around a **React + TypeScript + Vite** frontend
- **FastAPI** backend with **SQLite** persistence (`backend/data/hardware_copilot.db`, schema + idempotent migrations in `db.py`)
- **Claude API** integration centralized in `backend/app/claude_service.py` (streaming chat, interview mode, circuit drafting, component/connection suggestions, ASCII schematic generation, design validation, datasheet PDF analysis, token usage tracking)
- **Nexar/Octopart** datasheet fetcher in `backend/app/datasheet_fetcher.py`
- Frontend default view is the **Workbench tab**: 3-column layout (Chat | Block diagram via React Flow | Components by assembly), resizable, widths persisted in localStorage

---

## API Surface (~37 endpoints)

All domain routes are project-scoped under `/projects/{project_id}`:

- **Projects:** list/create/read/update/delete
- **Requirements, Blocks, Components:** full CRUD
- **Connections:** create/delete, plus `GET /diagram` and block position updates
- **Chat:** history, streaming chat, streaming interview mode, clear
- **AI actions:** `draft-circuit`, `suggest-components`, `suggest-connections`, `refresh-design` (atomic draft+suggest+connections, used after every AI turn), `describe-circuit` (ASCII schematic per block), `validate-schematic` flag
- **Validation:** `GET /validation` — computed live by Claude from the persisted project state
- **Datasheets:** search/fetch with Claude PDF analysis
- **Usage:** `GET /usage` — Claude token/cost tracking per project

---

## Known Limits

- **No automated tests** (backend or frontend)
- **No KiCad export** — the pipeline ends at per-block ASCII schematic sketches
- Validation is LLM-based, not deterministic/rule-based
- Claude model is pinned as a constant in `claude_service.py` (`MODEL`)
- No auth, no cloud sync, single-user local app (intentional for now)

---

## Where to Look First

| Concern | File |
|---|---|
| Routes | `backend/app/main.py` |
| Prompts + Claude calls | `backend/app/claude_service.py` |
| Data access | `backend/app/repository.py` |
| Schema/migrations | `backend/app/db.py` |
| Workbench UI | `src/App.tsx` + `src/components/` |
| API clients | `src/api/` |

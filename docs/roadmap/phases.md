# Hardware Copilot – Development Phases

Hardware Copilot is developed in clearly separated phases.

Rule:
- only one phase is active at a time
- side ideas move to backlog, side threads, or future phases
- completed phases remain as stable baseline unless explicitly reopened

---

## Current Status

The project already has a working technical baseline:

- Tauri desktop shell created
- React + TypeScript frontend active
- Python + FastAPI backend active
- core workbench UI implemented
- selection-driven UI interaction implemented
- initial backend integration working via `GET /project`

This means the project is no longer in concept stage.
The next steps build on an existing foundation.

---

## Phase 1 — Foundation Setup
**Status:** done / baseline

### Goal
Create the technical base for a desktop-first hardware workbench.

### Includes
- Tauri setup
- React + TypeScript + Vite frontend
- FastAPI backend
- local development scripts
- reproducible development environment

---

## Phase 2 — Workbench Shell
**Status:** done / baseline

### Goal
Build the first structured application shell.

### Includes
- Sidebar
- TopBar
- ChatPanel
- DesignTreePanel
- InspectorPanel
- ValidationPanel

---

## Phase 2.5 — Interactive Selection Layer
**Status:** done / baseline

### Goal
Move from static UI to interactive state-driven UI behavior.

### Includes
- selection state
- clickable design items
- inspector reacting to current selection

---

## Phase 3 — Initial Backend Integration
**Status:** done / baseline

### Goal
Connect the frontend to a real backend endpoint.

### Includes
- `GET /health`
- `GET /project`
- frontend loads project data from backend
- mock data is no longer the primary source

---

## Phase 3.1 — Backend Model Hardening
**Status:** active / next

### Goal
Stabilize the backend contract before feature growth.

### Includes
- Pydantic models
- validated response schemas
- cleaner API structure
- closer alignment between backend models and frontend types

---

## Phase 3.2 — Domain API Expansion
**Status:** planned

### Goal
Expand the backend from one project endpoint to domain-oriented APIs.

### Includes
- `/components`
- `/validation`
- later `/projects`

---

## Phase 4 — Persistence Layer
**Status:** planned

### Goal
Introduce persistent project and component storage.

### Includes
- SQLite integration
- persistent projects
- persistent components
- stored trust levels
- stored validation state

---

## Phase 5 — Component Library
**Status:** planned

### Goal
Turn the component area into a real engineering module.

### Includes
- component screen
- filtering by category
- filtering by trust level
- component detail views

---

## Phase 6 — Validation Center Expansion
**Status:** planned

### Goal
Turn validation into a core system instead of a passive display area.

### Includes
- errors
- warnings
- assumptions
- review-required states
- expandable validation logic

---

## Phase 7 — Structured Chat-to-Draft Workflow
**Status:** planned

### Goal
Convert requirements entered in chat into structured technical draft data.

### Includes
- requirement capture
- structured specification
- derived functional blocks
- backend-supported draft generation

---

## Phase 8 — Internal Export Model
**Status:** planned

### Goal
Create a deterministic internal model for later schematic generation.

### Includes
- internal JSON export model
- stable intermediate representation
- foundation for generator logic

---

## Phase 9 — KiCad Generator
**Status:** future

### Goal
Generate KiCad schematic output deterministically from the internal model.

### Includes
- `.kicad_sch` generation
- deterministic generation pipeline
- no direct freeform LLM schematic output

---

## Phase 10 — Rule Engine and Trust System
**Status:** future

### Goal
Make trust levels and engineering rules part of the core logic.

### Includes
- trust-aware reuse rules
- review logic
- validated templates
- component and topology confidence handling

---

## Phase 11 — Real Project Workflows
**Status:** future

### Goal
Support real engineering project workflows beyond a single demo project.

### Includes
- multiple projects
- project lifecycle handling
- decision tracking
- freeze states
- review workflows

---

## Long-Term Pipeline

`Chat -> Spec -> Draft -> Validation -> Export Model -> KiCad Generator`
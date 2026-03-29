# Hardware Copilot – Current Baseline

## Purpose

This document describes the current technical baseline of the Hardware Copilot project.

It is not a roadmap.
It is a snapshot of what already exists, what is wired up, and which parts are still placeholders or demo-level implementations.

Use this file to understand:
- what is already working
- which files currently matter most
- which assumptions the current architecture is based on
- where the current limits are

---

## Project Goal

Hardware Copilot is intended as a desktop-first engineering workbench for hardware-related development.

The current concept is based on:
- chat-based requirement input
- structured technical drafting instead of freeform output only
- component handling with trust levels
- validation-centered design workflow
- later deterministic KiCad generation from an internal model

The planned high-level pipeline is:

`Chat -> Spec -> Draft -> Validation -> Export Model -> KiCad Generator`

---

## Current Technical State

The project already has a working baseline across frontend and backend.

Currently working:
- the desktop shell exists
- the React frontend is running
- the FastAPI backend is running
- the frontend loads project data from the backend API
- the design workspace is interactive
- the inspector reacts to selected entities
- the backend exposes a typed project response model
- frontend and backend project fields are aligned in camelCase at the API boundary

This means the project has moved beyond static UI mockup stage.

---

## Technology Stack

### Desktop Shell
- Tauri

### Frontend
- React
- TypeScript
- Vite

### Styling
- currently mostly inline styles
- no consolidated design system yet

### Backend
- Python
- FastAPI
- Pydantic models for API responses

### Later / planned
- SQLite
- component database
- topology knowledge
- deterministic export model
- KiCad schematic generation

---

## Current Architectural Direction

The current architecture is intentionally not based on letting an LLM directly generate KiCad schematic files.

Instead, the intended system flow is:

1. collect requirements in chat
2. derive a structured specification
3. derive functional blocks
4. select components
5. add standard support circuits
6. validate assumptions and rules
7. produce an internal intermediate model
8. later generate KiCad files deterministically

This architectural assumption is central to the project.

---

## Current Project Structure

```text
hardware-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── models.py
│   ├── requirements.txt
│   └── .venv/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── WorkspaceLayout.tsx
│   │   ├── panels/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── DesignTreePanel.tsx
│   │   │   ├── InspectorPanel.tsx
│   │   │   └── ValidationPanel.tsx
│   │   └── ui/
│   │       ├── Panel.tsx
│   │       └── StatusBadge.tsx
│   ├── types/
│   │   └── project.ts
│   ├── App.tsx
│   └── main.tsx
├── src-tauri/
├── package.json
├── package-lock.json
├── README.md
├── bootstrap.sh
├── start_backend.sh
├── start_tauri.sh
├── start_dev.sh
└── .gitignore
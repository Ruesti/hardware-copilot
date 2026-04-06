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

## Project Direction

Hardware Copilot is intended as a desktop-first engineering workbench for hardware-related development.

It is not primarily a chat assistant.
Its core direction is to become a technical derivation and implementation system based on reliable engineering data.

The long-term goal is not only to discuss designs, but to support increasingly structured and later partially autonomous design implementation.

This implies:
- technical sources must become structured and reusable
- engineering decisions should be based on explicit data, rules, and validations
- design output should move from freeform text toward deterministic intermediate representations

---

## Core Architectural Principle

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

High-level pipeline:

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

The current system already demonstrates:
- a working desktop shell
- a working frontend/backend connection
- a typed backend contract
- a first separation between UI state and backend state

---

## Current Development Position

The project is currently beyond foundation setup and early backend connection work.

Completed baseline phases:
- Phase 1 — Foundation Setup
- Phase 2 — Workbench Shell
- Phase 2.5 — Interactive Selection Layer
- Phase 3 — Initial Backend Integration
- Phase 3.1 — Backend Model Hardening

Current active direction:
- Phase 3.2 — Domain API Expansion

This means the immediate next step is no longer generic UI work.
The immediate next step is to separate the backend into clearer engineering domains such as project data, component data, and validation data.

---

## What the System Can Do Today

At the current baseline, Hardware Copilot can:
- run as a desktop application shell
- display a structured workbench UI
- load a project from the backend
- show project requirements and blocks
- react to interactive selection in the design workspace
- show inspector content based on selected entities
- expose typed project data from the backend to the frontend

This is enough to prove the architectural foundation, but not yet enough to support real engineering workflows.

---

## What the System Cannot Do Yet

At the current baseline, Hardware Copilot does not yet provide:
- persistent project storage
- a real technical component knowledge base
- structured datasheet or application-note ingestion
- source-backed component comparison
- rule-backed engineering validation
- structured draft derivation from chat input
- deterministic export model generation
- KiCad schematic generation
- traceable technical decision history across real projects

These are still future capabilities.

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

## Current Architectural Direction in Practice

The practical implication of the current baseline is:

- chat is currently only an entry surface, not yet the engineering engine
- backend models are becoming the stable contract
- domain separation is beginning
- validation is present as a structural idea, but not yet a real engineering reasoning layer
- components are present as a concept, but not yet a trustworthy technical knowledge base

So the project is currently in the transition from:
- connected demo baseline

toward:
- structured engineering system

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

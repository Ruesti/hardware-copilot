# Hardware Copilot – Development Phases

Hardware Copilot is developed in clearly separated phases.

Rule:
- only one phase is active at a time
- side ideas move to backlog, side threads, or future phases
- completed phases remain as stable baseline unless explicitly reopened

---

## Architectural Direction

Hardware Copilot is not primarily a chat assistant.
It is a technical derivation and implementation system based on reliable engineering data.

Core requirement:
- the system must build and maintain a strong technical data foundation
- technical sources must be structured, reviewable, and reusable
- later design steps must be derived from explicit data, rules, and validations
- the long-term goal is not just explanation, but increasingly autonomous design implementation

This principle applies across all phases.

Each phase should strengthen at least one of the following:
- technical data foundation
- structured design derivation
- validation capability
- implementation readiness

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
**Status:** done / baseline

### Goal
Stabilize the backend contract before feature growth.

### Includes
- Pydantic models
- validated response schemas
- cleaner API structure
- closer alignment between backend models and frontend types
- frontend project state loaded from backend API
- mock-based root app state removed

---

## Phase 3.2 — Domain API Expansion
**Status:** active / next

### Goal
Expand the backend from one project endpoint to domain-oriented APIs.

### Includes
- `/components`
- `/validation`
- later `/projects`

### Phase requirement
This phase is not only API splitting.
It must prepare the backend for structured technical knowledge domains.

### Intended outcome
- project data separated from domain data
- components represented as explicit technical entities
- validation represented as explicit engineering feedback
- backend structure prepared for later source-backed design derivation

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

### Phase requirement
Persistence is not only for storage convenience.
It is the foundation for reusable technical knowledge and later autonomous design steps.

### Intended outcome
- technical entities can be stored and reused
- validation state is persisted
- trust-related metadata can later be attached to stored entities
- project state becomes reconstructable beyond a single runtime session

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

### Phase requirement
The component library is not only a browsing interface.
It is the beginning of the technical knowledge base.

### Intended outcome
- components carry structured technical metadata
- components can later reference datasheets, application notes, and trust state
- component reuse becomes part of the engineering workflow

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

### Phase requirement
Validation must evolve into an engineering decision layer, not remain a passive display.

### Intended outcome
- technical assumptions become explicit
- conflicts and review-required states become first-class entities
- validation prepares the system for design autonomy without hiding uncertainty

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

### Phase requirement
Chat input must be transformed into structured engineering data, not remain freeform conversation.

### Intended outcome
- requirements become structured specification elements
- structured specification can drive later component selection and validation
- the system moves from discussion toward derivation

---

## Phase 8 — Internal Export Model
**Status:** planned

### Goal
Create a deterministic internal model for later schematic generation.

### Includes
- internal JSON export model
- stable intermediate representation
- foundation for generator logic

### Phase requirement
The export model must become the stable internal representation for deterministic implementation.

### Intended outcome
- internal design intent is stored independently from chat wording
- downstream generator logic can operate on structured data
- later implementation becomes less dependent on freeform LLM output

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

### Phase requirement
Trust and engineering rules must become part of the core decision logic.

### Intended outcome
- the system can distinguish between strong, weak, and review-required technical basis
- rule-backed derivation becomes possible
- autonomous implementation is constrained by explicit engineering confidence

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
- project knowledge continuity
- traceable design evolution

---

## Phase Evaluation Rule

A phase is stronger if it improves the core memory / knowledge direction of the project.

For Hardware Copilot:
- does this phase improve technical data quality?
- does it improve structured design derivation?
- does it improve validation?
- does it improve implementation readiness?

---

## Long-Term Pipeline

`Chat -> Spec -> Draft -> Validation -> Export Model -> KiCad Generator`

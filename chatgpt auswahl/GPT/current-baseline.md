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
- the frontend loads project data from the backend
- the frontend loads requirements from a dedicated endpoint
- the frontend loads blocks from a dedicated endpoint
- the frontend loads components from a dedicated endpoint
- validation is available as a dedicated domain endpoint

Completed phases:
- Phase 3.1 — Backend Model Hardening
- Phase 3.2 — Domain API Expansion

Current major phase:
- Phase 4 — Persistent Projects with SQLite

Planned Phase 4 subphases:
- Phase 4.1 — SQLite Backend Foundation
- Phase 4.2 — Project-based Routing
- Phase 4.3 — Minimal Write API
- Phase 4.4 — Derived Validation

See:
- `docs/phases/phase-4-persistent-projects-with-sqlite.md`
- `docs/phases/phase-4-1-sqlite-backend-foundation.md`
- `docs/phases/phase-4-2-project-based-routing.md`
- `docs/phases/phase-4-3-minimal-write-api.md`
- `docs/phases/phase-4-4-derived-validation.md`

---

## Current API State

The current backend API exposes the following read endpoints:

- `GET /project`
- `GET /requirements`
- `GET /blocks`
- `GET /components`
- `GET /validation`

Current endpoint responsibilities:

### `/project`
Returns lightweight project-level data:
- `name`
- `phase`
- `chatMessages`

### `/requirements`
Returns:
- `items`

### `/blocks`
Returns:
- `items`

### `/components`
Returns:
- `items`

### `/validation`
Returns:
- `items`

This means the previous direct frontend dependency on a monolithic project payload has already been reduced.

The `/project` endpoint is now focused on project metadata and chat messages, while requirements, blocks, components, and validation are exposed as separate domain reads.

---

## Current Architecture Assumptions

The current implementation still assumes a demo-like single project state.

Important current characteristics:
- there is no database yet
- data is still effectively sample or in-memory driven
- the API shape is already domain-split
- the frontend no longer depends on `project.requirements` or `project.blocks`
- the system is still primarily read-oriented

This is the architectural handoff point into Phase 4.

---

## Current Limits

The current baseline is useful as a frontend/backend integration foundation, but it still has clear limits:

- no persistent project storage
- no explicit project identity
- no real multi-project model
- no minimal CRUD foundation for core entities
- validation is not yet fully derived from a persisted project state

These are intentional limits of the current baseline and are the basis for the next phase.

---

## Why the Current Baseline Matters

The current baseline is important because it already established:

- a running desktop shell
- a functioning frontend/backend integration
- a typed backend response model
- domain-level API separation
- a leaner project endpoint
- a frontend data flow that can now evolve toward persistent project-based storage

That means the next step does not need to redesign the whole application.
It needs to add persistence and project identity on top of the existing domain split.

---

## Immediate Next Architectural Step

The next architectural step is Phase 4, broken into four sequential subphases.

### Phase 4.1 — SQLite Backend Foundation
Introduce SQLite persistence beneath the current read API and move the backend source of truth from sample/in-memory structures to persistent storage.

### Phase 4.2 — Project-based Routing
Introduce explicit project identity and move from implicit single-project routing to project-scoped read routes.

### Phase 4.3 — Minimal Write API
Introduce the first create/update endpoints for persisted project entities.

### Phase 4.4 — Derived Validation
Turn validation into a computed domain derived from persisted project state.

This work is defined in:

- `docs/phases/phase-4-persistent-projects-with-sqlite.md`
- `docs/phases/phase-4-1-sqlite-backend-foundation.md`
- `docs/phases/phase-4-2-project-based-routing.md`
- `docs/phases/phase-4-3-minimal-write-api.md`
- `docs/phases/phase-4-4-derived-validation.md`

---

## End of Current Baseline

At the current baseline, Hardware Copilot has already outgrown a pure frontend mock/demo structure, but it has not yet reached a persistent application-grade project model.

That transition is the purpose of Phase 4.
# Hardware Copilot – Phases

This document tracks the current phased development structure of Hardware Copilot.

It is intentionally sequential.
The goal is to reduce drift, avoid unnecessary side branches, and keep the implementation aligned with the current architectural maturity of the project.

---

## Phase 3.1 — Backend Model Hardening

**Status:** done  
**Result:** baseline

### Goal
Stabilize the backend model and ensure the frontend consumes typed backend data instead of relying on local mock-only assumptions.

### Summary
Phase 3.1 established the first stable backend-driven project state.

Delivered:
- FastAPI backend running
- typed project response model
- `GET /project`
- frontend reads project data from backend
- trust level and validation data integrated into the UI model
- inspector behavior aligned with backend-driven state

This phase is completed.

---

## Phase 3.2 — Domain API Expansion

**Status:** done  
**Result:** baseline

### Goal
Split the previously larger project payload into separate domain read endpoints so the frontend can evolve away from a monolithic API shape.

### Summary
Phase 3.2 introduced dedicated domain endpoints and removed direct frontend coupling to `project.requirements` and `project.blocks`.

Delivered:
- `GET /project`
- `GET /requirements`
- `GET /blocks`
- `GET /components`
- `GET /validation`

Current endpoint responsibilities:
- `/project` returns project-level metadata and chat messages
- `/requirements` returns requirement items
- `/blocks` returns block items
- `/components` returns component items
- `/validation` returns validation items

Frontend changes:
- requirements loaded separately
- blocks loaded separately
- components loaded separately
- validation available as a dedicated domain read
- old direct accesses to `project.requirements` and `project.blocks` removed

This phase is completed.

---

## Phase 4 — Persistent Projects with SQLite

**Status:** active  
**Result:** current major phase

### Goal
Move from a demo-like in-memory single-project state to a persistent SQLite-backed project model while preserving the domain API split introduced in Phase 3.2.

### Summary
Phase 4 is the first persistence phase.

It is not about speculative expansion.
It is about turning the current API structure into a stable application foundation with:

- SQLite as persistent storage
- explicit project identity
- project-based routing
- minimal write capability
- validation derived from persistent project state

### Subphases

#### Phase 4.1 — SQLite Backend Foundation
Introduce SQLite underneath the current read API and move the backend source of truth from in-memory/sample data to persistent storage.

See:
- `docs/phases/phase-4-1-sqlite-backend-foundation.md`

#### Phase 4.2 — Project-based Routing
Move from implicit single-project access to explicit project identity and project-scoped read routes.

See:
- `docs/phases/phase-4-2-project-based-routing.md`

#### Phase 4.3 — Minimal Write API
Introduce the first minimal create/update endpoints for core project entities.

See:
- `docs/phases/phase-4-3-minimal-write-api.md`

#### Phase 4.4 — Derived Validation
Move validation from static/demo-style payloads to a computed domain derived from persisted project state.

See:
- `docs/phases/phase-4-4-derived-validation.md`

### Out of scope
Phase 4 does not include:
- PostgreSQL
- auth
- cloud sync
- collaboration
- KiCad export
- advanced AI implementation flows
- version history systems

### Detailed phase definition
See:

- `docs/phases/phase-4-persistent-projects-with-sqlite.md`
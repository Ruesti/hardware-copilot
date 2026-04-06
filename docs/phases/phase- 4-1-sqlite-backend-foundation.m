# Hardware Copilot – Phase 4.1

## Title

SQLite Backend Foundation

---

## Purpose

Phase 4.1 introduces SQLite as the first persistent storage layer for Hardware Copilot.

The goal of this phase is not to redesign the API or expand the product scope.
The goal is to replace the current sample/in-memory backend state with a persistent SQLite-backed source of truth while keeping the current read API behavior stable.

This phase is the foundation step for all later Phase 4 work:
- project identity
- project-based routing
- minimal write operations
- validation derived from stored state

Without this layer, later changes would still be built on temporary data structures.

---

## Relation to Previous Phases

### Phase 3.1 established
- typed backend project model
- frontend/backend integration
- backend-driven project loading

### Phase 3.2 established
- domain API split
- dedicated read endpoints:
  - `GET /project`
  - `GET /requirements`
  - `GET /blocks`
  - `GET /components`
  - `GET /validation`
- removal of direct frontend reliance on `project.requirements` and `project.blocks`

### Phase 4 established
- the architectural direction toward persistent projects with SQLite

### Phase 4.1 now focuses on
- introducing SQLite underneath the current domain read API
- keeping the system behavior stable while changing the data source

---

## Core Goal

Replace the current in-memory or static backend state with SQLite-backed persistence, without yet forcing the frontend into project-based routing changes.

---

## Scope

Phase 4.1 includes:

- adding SQLite to the backend
- defining the first persistent schema
- creating database initialization logic
- introducing a storage/repository layer
- seeding the current sample project into SQLite
- moving current read endpoints to SQLite-backed reads
- preserving the existing external endpoint shape during the migration

---

## Not in Scope

The following are explicitly out of scope for Phase 4.1:

- project-based routing
- `GET /projects`
- `GET /projects/{project_id}/...`
- create/update/delete APIs
- frontend project switching
- authentication
- cloud sync
- multi-user handling
- complex validation engine redesign
- KiCad export
- background jobs
- schema migration tooling beyond what is minimally needed for local development

Phase 4.1 is a storage foundation phase, not a full application restructuring phase.

---

## Main Principle

The backend should internally move to persistent storage while the API remains externally familiar.

That means:

- existing read endpoints should continue to work
- frontend disruption should be minimal
- SQLite becomes the source of truth
- current domain boundaries remain intact

This keeps the migration controlled and testable.

---

## Expected Result

After Phase 4.1:

- the backend no longer depends on hardcoded sample structures as its primary source of truth
- the current project state exists in SQLite
- requirements, blocks, components, and chat messages are loaded from SQLite
- existing read endpoints continue to respond with the expected shapes
- the system is ready for project identity in Phase 4.2

---

## Backend Design Direction

Phase 4.1 should introduce a simple backend layering model.

### Suggested layers

#### 1. API layer
FastAPI route handlers

Responsibility:
- receive HTTP requests
- call storage/repository functions
- return response models

#### 2. repository / storage layer
SQLite-facing functions or classes

Responsibility:
- read project data from SQLite
- compose domain responses
- isolate SQL details from route handlers

#### 3. schema / initialization layer
Database bootstrap and seed logic

Responsibility:
- create tables if missing
- seed initial development data
- ensure the local app can start from an empty database

This separation keeps Phase 4.1 maintainable and makes later routing changes easier.

---

## SQLite Introduction

SQLite is the persistence layer for Phase 4.

For Phase 4.1, it should be introduced in the simplest practical way:
- one local database file
- local development usage
- deterministic schema creation on startup or via explicit init function
- no external DB service dependency

The purpose is not database sophistication.
The purpose is stable persistent state.

---

## Suggested Persistent Schema

Phase 4.1 should already use a schema that aligns with later project-based routing, even if only one seeded project exists initially.

### projects
Stores project-level metadata.

Suggested fields:
- `id`
- `name`
- `phase`
- `created_at`
- `updated_at`

### chat_messages
Stores chat history for a project.

Suggested fields:
- `id`
- `project_id`
- `role`
- `content`
- `order_index`
- `created_at`

### requirements
Stores requirements for a project.

Suggested fields:
- `id`
- `project_id`
- `title`
- `description`
- `status`
- `order_index`

### blocks
Stores blocks for a project.

Suggested fields:
- `id`
- `project_id`
- `name`
- `description`
- `trust_level`
- `order_index`

### components
Stores components for a project.

Suggested fields:
- `id`
- `project_id`
- `block_id` nullable
- `name`
- `type`
- `description`
- `manufacturer`
- `mpn`
- `trust_level`
- `order_index`

### validation handling in Phase 4.1
Validation does not need a primary table yet.

For Phase 4.1, acceptable options are:

#### Option A
Keep validation temporarily assembled from existing logic while the main persisted entities move to SQLite.

#### Option B
Generate validation from persisted entities with simple derived logic.

For Phase 4.1, Option A is acceptable if it reduces migration risk.
The full derived validation step belongs to Phase 4.4.

---

## Seed Strategy

Phase 4.1 should include seed data so an empty development setup still starts with a usable project state.

The seed should reflect the current baseline project already used by the backend/frontend.

Recommended seed characteristics:
- one initial project
- representative requirements
- representative blocks
- representative components
- representative chat messages

The seed is a bootstrap mechanism, not the long-term authoring model.

---

## API Behavior During Phase 4.1

The current endpoint shape should stay stable:

- `GET /project`
- `GET /requirements`
- `GET /blocks`
- `GET /components`
- `GET /validation`

The important change is internal:
these endpoints should now read from SQLite-backed storage instead of static or in-memory backend state.

### Endpoint expectations

#### `GET /project`
Should return:
- `name`
- `phase`
- `chatMessages`

Loaded from:
- `projects`
- `chat_messages`

#### `GET /requirements`
Should return:
- `items`

Loaded from:
- `requirements`

#### `GET /blocks`
Should return:
- `items`

Loaded from:
- `blocks`

#### `GET /components`
Should return:
- `items`

Loaded from:
- `components`

#### `GET /validation`
Should return:
- `items`

Loaded from:
- temporary validation logic or simple derived logic based on persisted state

---

## Migration Strategy

Phase 4.1 should be implemented in a backend-first sequence.

### Recommended order

1. create SQLite database module
2. define schema creation logic
3. define seed logic
4. add repository/storage functions
5. move route handlers to repository usage
6. verify endpoint responses remain shape-compatible
7. verify frontend still loads without structural changes

This keeps the migration incremental and easier to debug.

---

## Suggested Technical Deliverables

Phase 4.1 should produce at least the following backend capabilities:

- a database file used by the backend
- schema creation on first run or explicit init
- a seeded initial project
- repository functions for:
  - reading project header + chat messages
  - reading requirements
  - reading blocks
  - reading components
- route handlers using repository-backed reads
- local verification that the frontend still works against the new storage source

---

## Suggested File-Level Direction

Exact filenames can vary, but the backend should begin moving toward a structure similar to:

- `app/main.py`
- `app/models.py`
- `app/db.py`
- `app/repositories/project_repository.py`
- `app/repositories/requirement_repository.py`
- `app/repositories/block_repository.py`
- `app/repositories/component_repository.py`

If the current backend is smaller, this can also start with fewer files.

The key point is not the exact folder count.
The key point is to avoid route handlers directly containing all SQL and seed logic.

---

## Design Constraints

Phase 4.1 must respect the following constraints:

- build directly on the completed Phase 3.2 API split
- do not add project-based routing yet
- do not expand into write APIs yet
- do not introduce unnecessary abstractions
- do not add a second database technology
- do not force a frontend redesign in this phase
- keep the data model aligned with later project-based routing

---

## Risks to Avoid

### 1. Mixing migration with too many new concepts
Phase 4.1 should not also try to solve:
- project switching
- editing
- deletion
- full validation redesign

### 2. Rebuilding the API shape unnecessarily
The current read API should stay externally stable for now.

### 3. Embedding SQL everywhere
A repository/storage layer should be introduced early, even if simple.

### 4. Seeding data in an ad-hoc way
Seed logic should be deterministic and repeatable.

---

## Acceptance Criteria

Phase 4.1 is complete when:

- SQLite is integrated into the backend
- the backend can initialize the required schema
- an initial project is seeded into SQLite
- `GET /project` reads its data from SQLite-backed storage
- `GET /requirements` reads its data from SQLite-backed storage
- `GET /blocks` reads its data from SQLite-backed storage
- `GET /components` reads its data from SQLite-backed storage
- `GET /validation` still returns a valid response compatible with the current frontend expectations
- the frontend continues to load successfully against the backend
- the previous static/in-memory data is no longer the backend source of truth

---

## Completion State

At the end of Phase 4.1, Hardware Copilot should still look similar from the outside, but internally it should have crossed an important boundary:

from:
- demo-like in-memory backend state

to:
- SQLite-backed persistent backend state

That is the required foundation for:
- Phase 4.2 — Project-based Routing
- Phase 4.3 — Minimal Write API
- Phase 4.4 — Derived Validation
# Hardware Copilot – Phase 4

## Title

Persistent Projects with SQLite

---

## Purpose

Phase 4 moves Hardware Copilot from a demo-like in-memory project state to a persistent project-based backend model.

Phase 3.2 separated the domain API into dedicated read endpoints:

- `/project`
- `/requirements`
- `/blocks`
- `/components`
- `/validation`

That split is now the basis for the next architectural step.

The goal of Phase 4 is to preserve that domain separation while introducing:

- persistent storage with SQLite
- explicit project identity
- project-based routing
- minimal write operations
- validation derived from persistent project state

Phase 4 is not about adding more speculative features.
It is about turning the current API shape into a stable application foundation.

---

## Why Phase 4 starts here

After Phase 3.2, the system already has:

- a running Tauri + React + TypeScript + Vite frontend
- a running FastAPI backend
- separate domain read endpoints
- a lightweight `/project` endpoint
- frontend loading logic no longer coupled to a monolithic `project.requirements` or `project.blocks`

Without persistence, further expansion would remain structurally weak:

- state is not durable
- multi-project handling is not possible in a clean way
- future write operations would target temporary data structures
- validation and later export would not rest on a stable stored project model

Phase 4 therefore introduces persistence first, before moving into more advanced design automation.

---

## Core Goal

Transform the current single in-memory project state into a persistent SQLite-backed project model while preserving the domain API split introduced in Phase 3.2.

---

## Scope

Phase 4 includes:

- introducing SQLite
- defining a persistent backend schema
- moving existing read endpoints from static/in-memory data to SQLite-backed reads
- introducing explicit project identity
- moving from implicit single-project routing to explicit project-based routing
- introducing minimal write endpoints for core domain entities
- deriving validation from persistent project state

---

## Not in Scope

The following are explicitly out of scope for Phase 4:

- PostgreSQL
- external database services
- authentication
- user accounts
- cloud sync
- collaboration
- real-time updates
- KiCad export
- AI-driven implementation flows
- advanced datasheet ingestion
- version history / event sourcing
- background job systems
- permission systems

SQLite is the first persistence step.
More advanced storage or collaboration concerns belong to later phases.

---

## Architectural Direction

Phase 4 introduces a clear distinction between:

### 1. Project metadata
Persistent metadata about a project, such as:

- id
- name
- phase
- timestamps

### 2. Domain entities
Persistent entities belonging to one project:

- requirements
- blocks
- components
- chat messages

### 3. Derived domain output
Computed output derived from persistent state:

- validation

Validation should initially be computed from stored project data rather than treated as a static stored example payload.

---

## Target Backend Model

### projects
Stores project-level metadata.

Suggested fields:

- `id`
- `name`
- `phase`
- `created_at`
- `updated_at`

### chat_messages
Stores chat history per project.

Suggested fields:

- `id`
- `project_id`
- `role`
- `content`
- `order_index`
- `created_at`

### requirements
Stores requirements per project.

Suggested fields:

- `id`
- `project_id`
- `title`
- `description`
- `status`
- `order_index`

### blocks
Stores design blocks per project.

Suggested fields:

- `id`
- `project_id`
- `name`
- `description`
- `trust_level`
- `order_index`

### components
Stores components per project.

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

### validation
Validation is initially treated as derived data.

Phase 4 assumption:

- validation is computed from persisted project state
- validation does not need its own primary persistence model yet unless a concrete reason appears later

---

## API Transition Goal

Phase 3.2 endpoint shape:

- `GET /project`
- `GET /requirements`
- `GET /blocks`
- `GET /components`
- `GET /validation`

Phase 4 target shape:

### Read API
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/requirements`
- `GET /projects/{project_id}/blocks`
- `GET /projects/{project_id}/components`
- `GET /projects/{project_id}/validation`

### Write API
- `POST /projects`
- `PATCH /projects/{project_id}`
- `POST /projects/{project_id}/requirements`
- `PATCH /projects/{project_id}/requirements/{requirement_id}`
- `POST /projects/{project_id}/blocks`
- `PATCH /projects/{project_id}/blocks/{block_id}`
- `POST /projects/{project_id}/components`
- `PATCH /projects/{project_id}/components/{component_id}`

Delete operations are not required at the start of Phase 4.

---

## Migration Principle

Phase 4 should be implemented in a controlled backend-first sequence.

Recommended order:

1. define SQLite schema
2. introduce storage/repository layer in backend
3. seed existing sample data into SQLite
4. move current read endpoints to SQLite-backed reads
5. introduce project-based routing
6. migrate frontend to explicit active-project loading
7. add minimal write endpoints
8. derive validation from stored project state

This avoids mixing too many moving parts at once.

---

## Subphases

## Phase 4.1 – SQLite Backend Foundation

### Goal
Introduce SQLite persistence underneath the existing domain read API.

### Includes
- SQLite setup
- database connection handling
- schema creation
- seed data
- storage/repository layer
- existing read endpoints served from SQLite instead of static/in-memory structures

### Result
The current API responses still work, but the source of truth is now SQLite.

---

## Phase 4.2 – Project-based Routing

### Goal
Move from implicit single-project API access to explicit project identity.

### Includes
- `GET /projects`
- `GET /projects/{project_id}`
- nested project domain routes
- backend support for selecting a project by ID
- frontend support for loading a selected/active project

### Result
The API is no longer shaped as if only one global project exists.

---

## Phase 4.3 – Minimal Write API

### Goal
Allow the frontend or test clients to create and update persistent project data.

### Includes
- create project
- update project metadata
- create/update requirements
- create/update blocks
- create/update components

### Result
The system becomes minimally state-editable instead of read-only.

---

## Phase 4.4 – Derived Validation

### Goal
Validation becomes a computed domain based on persisted project state.

### Includes
- validation generation logic
- endpoint returns validation derived from requirements / blocks / components
- removal of static validation example payloads as source of truth

### Result
Validation reflects actual stored project data.

---

## Design Constraints

Phase 4 must respect the following constraints:

- build on the current domain API split from Phase 3.2
- avoid unnecessary side branches
- do not introduce non-SQLite persistence
- do not introduce auth or cloud concerns
- do not redesign unrelated frontend areas
- keep the architecture understandable and incremental

---

## Acceptance Criteria

Phase 4 is considered complete when:

- SQLite is the persistent source of truth
- projects are stored and addressable by ID
- requirements, blocks, components, and chat messages belong to a persisted project
- read endpoints return project-specific data from SQLite
- minimal write endpoints exist for core project entities
- validation is derived from persisted project state
- the frontend can load data for an explicit project instead of relying on a single implicit global state

---

## End State of Phase 4

At the end of Phase 4, Hardware Copilot should no longer behave like a single seeded demo state.

It should behave like a real application foundation with:

- persistent projects
- explicit project identity
- domain-separated APIs
- editable core entities
- validation based on stored project data

That foundation then becomes the basis for later phases such as stronger validation logic, export models, and deterministic EDA/KiCad integration.
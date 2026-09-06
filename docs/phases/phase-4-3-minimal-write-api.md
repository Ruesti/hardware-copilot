# Hardware Copilot – Phase 4.3

## Title

Minimal Write API

---

## Purpose

Phase 4.3 introduces the first controlled write capabilities for persisted project data.

Up to this point, Hardware Copilot has:
- separated domain reads
- persistent SQLite storage
- project-based routing

What is still missing is a minimal ability to create and update core project entities through the backend API.

The purpose of Phase 4.3 is to establish that minimal write foundation without expanding into full application editing complexity.

---

## Relation to Previous Phases

### Phase 4.1 established
- SQLite as source of truth

### Phase 4.2 established
- explicit project identity
- project-scoped read routes

### Phase 4.3 now focuses on
- minimal create/update endpoints
- persistent changes to core project state
- a first real CRUD baseline for the domain model

---

## Core Goal

Introduce the smallest useful set of write endpoints required to create and update persisted project data.

---

## Why This Phase Exists

Without write capability, the system is still structurally read-oriented.
That is useful for inspection, but not enough for a real workbench.

The next application boundary is:
- not just reading projects
- but modifying them in a controlled and persisted way

This phase creates that boundary while keeping the scope intentionally narrow.

---

## Scope

Phase 4.3 includes:

- create project
- update project metadata
- create requirement
- update requirement
- create block
- update block
- create component
- update component

These operations should write to SQLite-backed persistent storage through the backend API.

---

## Not in Scope

The following are explicitly out of scope for Phase 4.3:

- delete operations
- bulk operations
- reorder endpoints
- undo/redo
- optimistic concurrency
- collaboration conflict handling
- advanced validation enforcement during writes
- attachment handling
- full chat authoring flows
- import/export workflows
- major frontend editor redesign

This phase is about a minimal write baseline, not full editing maturity.

---

## Main Principle

Write operations should be:
- explicit
- scoped to a project
- typed
- small in surface area
- easy to verify

The API should expose only the minimum needed to move from read-only state to basic persisted editing.

---

## Target Write API

### Projects
- `POST /projects`
- `PATCH /projects/{project_id}`

### Requirements
- `POST /projects/{project_id}/requirements`
- `PATCH /projects/{project_id}/requirements/{requirement_id}`

### Blocks
- `POST /projects/{project_id}/blocks`
- `PATCH /projects/{project_id}/blocks/{block_id}`

### Components
- `POST /projects/{project_id}/components`
- `PATCH /projects/{project_id}/components/{component_id}`

---

## Suggested Write Semantics

### `POST`
Used to create new entities.

Expected behavior:
- validate request payload
- write a new row to SQLite
- return created entity or created resource response model

### `PATCH`
Used for partial updates.

Expected behavior:
- update only provided fields
- preserve existing values for omitted fields
- return updated entity or refreshed response model

This keeps the API predictable and aligns with incremental UI editing later.

---

## Suggested Request/Response Direction

Exact models can vary, but the phase should establish clear typed input models for:

- project create
- project update
- requirement create
- requirement update
- block create
- block update
- component create
- component update

These should remain close to the domain read models rather than introducing unnecessary DTO complexity.

---

## Domain Expectations

### Projects
Initial fields likely include:
- `name`
- `phase`

### Requirements
Initial fields likely include:
- `title`
- `description`
- `status`
- `order_index` optional

### Blocks
Initial fields likely include:
- `name`
- `description`
- `trust_level`
- `order_index` optional

### Components
Initial fields likely include:
- `block_id` optional
- `name`
- `type`
- `description`
- `manufacturer`
- `mpn`
- `trust_level`
- `order_index` optional

The phase does not need a perfect final domain vocabulary.
It needs a consistent minimal writable one.

---

## Backend Responsibilities

Phase 4.3 should add backend support for:

- creating rows in `projects`
- updating project metadata
- creating rows in `requirements`
- updating requirement rows
- creating rows in `blocks`
- updating block rows
- creating rows in `components`
- updating component rows

The repository layer should remain the place where SQL write logic lives.

Route handlers should:
- validate input
- call repository methods
- return typed responses

---

## Frontend Responsibilities

Frontend work in this phase can remain minimal.

Acceptable options:
- expose write calls only through test clients initially
- add limited UI actions for one or two entity types
- add simple forms or buttons only where already natural

The critical outcome is backend write capability.
The frontend does not need full editing UX completeness in this phase.

---

## Suggested Incremental Implementation Order

1. add `POST /projects`
2. add `PATCH /projects/{project_id}`
3. add requirement create/update
4. add block create/update
5. add component create/update
6. verify reads reflect persisted writes
7. optionally expose one or two write paths in frontend UI

This reduces debugging complexity and keeps the phase controlled.

---

## Validation Interaction

Phase 4.3 should not attempt to fully redesign validation behavior.

However, writes should not destroy basic data integrity.

Minimum expectations:
- referenced `project_id` must exist
- referenced entity ID must exist for patch operations
- if `block_id` is provided for a component, it should resolve consistently
- invalid payloads should return clear HTTP errors

Advanced domain validation logic belongs mainly to Phase 4.4 and later phases.

---

## Suggested Technical Deliverables

Phase 4.3 should produce at least:

- create/update request models
- repository write methods for projects, requirements, blocks, components
- FastAPI create/update routes
- SQLite-backed persisted writes
- response models for created/updated entities
- endpoint-level verification for successful writes and subsequent reads

---

## Design Constraints

Phase 4.3 must respect the following constraints:

- build on project-scoped routing from Phase 4.2
- do not add delete flows yet
- do not add advanced workflow orchestration
- do not redesign the whole frontend editor
- do not introduce heavy domain rule engines into write paths
- keep the write surface minimal and explicit

---

## Risks to Avoid

### 1. Expanding CRUD scope too early
Delete, reorder, bulk edit, and advanced forms are separate concerns.

### 2. Embedding business logic directly in route handlers
Write logic should stay inside repository/service layers.

### 3. Making write APIs depend on unfinished validation logic
Basic integrity checks are enough for this phase.

### 4. Building too much UI before backend write behavior is stable
Backend stability comes first.

---

## Acceptance Criteria

Phase 4.3 is complete when:

- `POST /projects` exists and creates persisted projects
- `PATCH /projects/{project_id}` exists and updates persisted project metadata
- `POST /projects/{project_id}/requirements` exists
- `PATCH /projects/{project_id}/requirements/{requirement_id}` exists
- `POST /projects/{project_id}/blocks` exists
- `PATCH /projects/{project_id}/blocks/{block_id}` exists
- `POST /projects/{project_id}/components` exists
- `PATCH /projects/{project_id}/components/{component_id}` exists
- created and updated data is persisted in SQLite
- subsequent read endpoints reflect the written changes
- API input and output models remain typed and predictable

---

## Completion State

At the end of Phase 4.3, Hardware Copilot should no longer be only a project viewer.

It should be a minimally editable project system with:
- persistent project creation
- persistent project updates
- persistent core entity updates
- a basic CRUD foundation for future workflow expansion

That is the required basis for:
- Phase 4.4 — Derived Validation
- later export and structured design workflows
# Hardware Copilot – Phase 4.2

## Title

Project-based Routing

---

## Purpose

Phase 4.2 introduces explicit project identity into the backend API.

Up to this point, the system behaves as if one implicit global project exists.
That was acceptable for the earlier baseline and for Phase 4.1 storage migration, but it is not a stable long-term application model.

The purpose of Phase 4.2 is to move from implicit single-project access to explicit project-scoped routing while preserving the domain API separation introduced in Phase 3.2 and the SQLite persistence introduced in Phase 4.1.

---

## Relation to Previous Phases

### Phase 4.1 established
- SQLite-backed persistent storage
- persisted project data as backend source of truth
- current read endpoints still available in their existing shape

### Phase 4.2 now focuses on
- explicit project identity
- project list and project selection
- project-scoped domain endpoints
- frontend loading based on an active project

---

## Core Goal

Replace implicit global project access with explicit `project_id`-based API routing.

---

## Why This Phase Exists

A persistent database alone is not enough.
Without explicit project identity, the application still behaves like a single seeded demo state.

That would block:
- real multi-project handling
- controlled project creation flows
- future export targeting
- clean project-level write operations
- reliable validation per project

Phase 4.2 introduces the missing structural boundary:
all domain data must belong to a specific project.

---

## Scope

Phase 4.2 includes:

- introducing `GET /projects`
- introducing `GET /projects/{project_id}`
- introducing project-scoped read routes for:
  - requirements
  - blocks
  - components
  - validation
- backend lookup by explicit `project_id`
- frontend support for loading one selected project
- migration away from relying on implicit global read routes as the primary API path

---

## Not in Scope

The following are explicitly out of scope for Phase 4.2:

- create/update/delete APIs
- full project editing flows
- project duplication
- auth
- user ownership models
- collaboration
- advanced filtering and search
- major frontend redesign
- validation logic redesign
- export features

Phase 4.2 is about addressing project identity, not general feature expansion.

---

## Main Principle

After Phase 4.2, no core domain read should conceptually exist without a project context.

That means:
- requirements belong to a project
- blocks belong to a project
- components belong to a project
- chat messages belong to a project
- validation is resolved for a project

This is the shift from a demo-style state model to an application state model.

---

## Target Read API

Phase 4.2 should introduce the following read structure as the new primary API shape:

- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/requirements`
- `GET /projects/{project_id}/blocks`
- `GET /projects/{project_id}/components`
- `GET /projects/{project_id}/validation`

### Suggested endpoint roles

#### `GET /projects`
Returns a list of available projects.

Typical fields:
- `id`
- `name`
- `phase`
- optionally timestamps

#### `GET /projects/{project_id}`
Returns project-level metadata and chat messages.

Typical fields:
- `id`
- `name`
- `phase`
- `chatMessages`

#### `GET /projects/{project_id}/requirements`
Returns:
- `items`

#### `GET /projects/{project_id}/blocks`
Returns:
- `items`

#### `GET /projects/{project_id}/components`
Returns:
- `items`

#### `GET /projects/{project_id}/validation`
Returns:
- `items`

---

## Migration Approach

Phase 4.2 should be introduced in a controlled manner.

### Recommended transition strategy

#### Option A
Keep old read routes temporarily for compatibility while frontend migration happens.

Examples:
- old: `GET /project`
- new: `GET /projects/{project_id}`

#### Option B
Move directly to project-scoped routes if the frontend is small and migration cost is low.

For this project stage, Option A is typically safer unless the codebase is still compact enough for a clean direct switch.

The decision should be based on actual frontend coupling size, not preference alone.

---

## Backend Responsibilities

Phase 4.2 should add backend support for:

- listing available projects from SQLite
- resolving one project by ID
- resolving requirements for a specific project
- resolving blocks for a specific project
- resolving components for a specific project
- resolving validation for a specific project

The repository layer introduced in Phase 4.1 should now operate with explicit `project_id` parameters wherever appropriate.

---

## Frontend Responsibilities

Phase 4.2 should add the minimum frontend support required to consume project-based routing.

Expected frontend changes:
- fetch project list or determine one active project
- store selected/active `project_id`
- load:
  - project metadata
  - requirements
  - blocks
  - components
  - validation
  using project-scoped routes

This does not require a full project management UI yet.
A minimal active-project selection approach is sufficient.

---

## Suggested Minimal Frontend Strategy

For an incremental implementation, the frontend can begin with one of these approaches:

### Option 1
Load the first available project from `GET /projects` automatically.

### Option 2
Use a hardcoded active project ID during migration.

### Option 3
Add a simple project selector if the UI already has a natural location for it.

For this phase, Option 1 or Option 2 is usually enough.
The main goal is API migration, not UX completeness.

---

## Data Model Expectations

Phase 4.2 assumes the SQLite schema already stores project ownership via `project_id` foreign keys.

That means all major domain reads should now be filtered by project identity.

Required relationships:
- `chat_messages.project_id -> projects.id`
- `requirements.project_id -> projects.id`
- `blocks.project_id -> projects.id`
- `components.project_id -> projects.id`

If a component belongs to a block, that relation remains secondary to project ownership.

---

## Suggested Technical Deliverables

Phase 4.2 should produce at least:

- repository functions for:
  - listing projects
  - reading project header by ID
  - reading project chat messages by project ID
  - reading requirements by project ID
  - reading blocks by project ID
  - reading components by project ID
- new FastAPI routes for project-scoped reads
- frontend active-project handling
- frontend migration to project-scoped fetches
- local verification that one selected project loads end-to-end

---

## Design Constraints

Phase 4.2 must respect the following constraints:

- build directly on SQLite persistence from Phase 4.1
- do not add write APIs yet
- do not introduce auth/user ownership
- do not overdesign project management UI
- keep the domain split intact
- keep migration understandable and testable
- avoid mixing routing migration with validation redesign

---

## Risks to Avoid

### 1. Treating `/projects` as only a cosmetic endpoint
The real point is project identity, not endpoint count.

### 2. Mixing project routing with editing concerns
Editing belongs to Phase 4.3.

### 3. Reintroducing monolithic project coupling
The frontend should continue loading domain data through separate routes.

### 4. Making project selection a large UI feature
This phase only needs enough selection logic to support the API model.

---

## Acceptance Criteria

Phase 4.2 is complete when:

- `GET /projects` exists and returns persisted projects
- `GET /projects/{project_id}` exists
- `GET /projects/{project_id}/requirements` exists
- `GET /projects/{project_id}/blocks` exists
- `GET /projects/{project_id}/components` exists
- `GET /projects/{project_id}/validation` exists
- backend read logic is project-scoped
- frontend can load one explicit active project via `project_id`
- the application no longer depends conceptually on one implicit global project

---

## Completion State

At the end of Phase 4.2, Hardware Copilot should behave like a project-based application rather than a single seeded demo state.

The system should now have:
- persistent projects
- explicit project identity
- project-scoped read APIs
- frontend loading tied to an active project

That is the required basis for:
- Phase 4.3 — Minimal Write API
- Phase 4.4 — Derived Validation
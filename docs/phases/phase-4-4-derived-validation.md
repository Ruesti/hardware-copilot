# Hardware Copilot – Phase 4.4

## Title

Derived Validation

---

## Purpose

Phase 4.4 turns validation into a computed domain derived from persisted project state.

Earlier phases established:
- domain-separated read APIs
- SQLite-backed persistence
- explicit project identity
- minimal write operations

At that point, validation should no longer behave like a static example payload or a loosely attached demo structure.
It should be generated from the actual stored project state.

The purpose of Phase 4.4 is to make validation reflect the real contents of a project.

---

## Relation to Previous Phases

### Phase 4.1 established
- persistent SQLite-backed state

### Phase 4.2 established
- project-scoped reads

### Phase 4.3 established
- persistent create/update flows

### Phase 4.4 now focuses on
- deriving validation from stored project entities
- making validation responses depend on actual project data
- removing static validation payloads as the source of truth

---

## Core Goal

Replace static or demo-style validation responses with validation output computed from persisted project state.

---

## Why This Phase Exists

As soon as the system supports persisted reads and writes, static validation becomes structurally misleading.

If validation does not reflect the real data:
- users cannot trust it
- write operations are not meaningfully checked
- later export logic would build on weak assumptions
- the system remains demo-like despite persistence

Phase 4.4 solves that by making validation a derived domain.

---

## Scope

Phase 4.4 includes:

- defining a first validation computation layer
- reading project state from persisted entities
- generating validation items from:
  - project metadata where relevant
  - requirements
  - blocks
  - components
- serving validation through project-scoped validation endpoints
- removing static validation payloads as the effective source of truth

---

## Not in Scope

The following are explicitly out of scope for Phase 4.4:

- a full electrical rule-check engine
- schematic-level simulation
- datasheet truth extraction
- automatic fix generation
- AI-generated validation reasoning
- advanced severity tuning workflows
- historical validation snapshots
- background validation job systems
- export-time design rule integration
- manufacturing rule validation

Phase 4.4 introduces the first real validation layer, not the final one.

---

## Main Principle

Validation should be treated as a computed read model.

That means:
- persisted project entities are the source of truth
- validation is produced from those entities
- validation output is deterministic for a given project state
- validation is not hand-maintained demo content

This keeps the architecture clean:
state is stored, validation is derived.

---

## Validation Input Domain

Phase 4.4 should compute validation from at least:

- project metadata
- requirements
- blocks
- components

Chat messages may remain out of scope unless a concrete validation need exists.

---

## Suggested Initial Validation Categories

The first derived validation layer does not need deep engineering intelligence.
It needs structural usefulness.

Reasonable initial categories include:

### 1. Missing required project structure
Examples:
- no requirements defined
- no blocks defined
- no components defined

### 2. Missing or weak field completeness
Examples:
- requirement without title
- block without trust level
- component without type
- component without trust level

### 3. Incomplete relationships
Examples:
- component references nonexistent block
- block exists but has no components, if relevant to the current model
- duplicate or suspiciously incomplete entries, if simple to detect

### 4. Consistency checks
Examples:
- project exists but contains no engineering structure
- requirement count and design structure appear disconnected
- multiple placeholder-like entries remain

These checks are enough to turn validation into a real domain without overreaching.

---

## Validation Output Expectations

The project-scoped validation endpoint should continue returning:

- `items`

Each validation item should remain compatible with the existing frontend expectations.

Typical fields may include:
- `id`
- `title`
- `description`
- `severity`
- related entity reference if applicable

The exact shape should align with the current typed frontend/backend model already in use.

---

## Severity Direction

Severity should remain simple and stable in this phase.

A reasonable initial model is:
- info
- warning
- error

The exact labels should match the existing `ValidationSeverity` typing already present in the frontend/backend model.

The goal is not perfect severity semantics.
The goal is consistent and explainable severity assignment.

---

## Computation Strategy

Phase 4.4 should introduce a dedicated validation computation layer rather than embedding validation rules directly into route handlers.

Suggested conceptual flow:

1. load project state
2. load requirements
3. load blocks
4. load components
5. apply deterministic validation rules
6. return validation items

This computation can happen on request.

For Phase 4.4, on-demand computation is usually sufficient.
Caching can wait until performance actually requires it.

---

## Suggested Backend Structure

Exact files can vary, but validation logic should move toward a dedicated location such as:

- `app/services/validation_service.py`
- or `app/validation.py`

Responsibilities:
- gather project-scoped persisted data
- apply validation rules
- build typed validation items

This avoids mixing validation rules with route definitions or raw repository code.

---

## Example Rule Types

The exact final rules are up to implementation, but the first version should likely include a small set such as:

- project has zero requirements -> warning or error
- project has zero blocks -> warning or error
- project has zero components -> warning or error
- requirement title empty -> warning
- block trust level missing or invalid -> warning
- component type missing -> warning
- component trust level missing or invalid -> warning
- component references missing block -> error
- placeholder names still present -> info or warning

The critical point is not rule quantity.
It is that rules run against real persisted state.

---

## Interaction with Write APIs

Phase 4.4 does not require hard validation blocking during writes.

Recommended behavior:
- writes remain possible if payloads meet basic integrity checks
- validation reports problems through the validation endpoint
- the frontend can surface those issues after data changes

This keeps write flows simple while still making validation meaningful.

Strict write-time domain enforcement can be explored later if needed.

---

## Suggested Technical Deliverables

Phase 4.4 should produce at least:

- a validation computation layer
- project-scoped loading of persisted entities for validation
- deterministic rule evaluation
- project-scoped `GET /projects/{project_id}/validation`
- removal of static validation payloads as the backend source of truth
- frontend verification that validation now reflects real project edits

---

## Design Constraints

Phase 4.4 must respect the following constraints:

- build directly on SQLite-backed persisted project state
- operate on project-scoped data
- do not become an electrical expert system yet
- do not add background validation infrastructure yet
- do not tightly couple validation logic into write handlers
- keep the first derived rules understandable and testable

---

## Risks to Avoid

### 1. Trying to make validation too intelligent too early
The first version should be structurally useful, not exhaustive.

### 2. Keeping static fallback payloads as hidden truth
That would undermine the phase goal.

### 3. Mixing structural validation with future export logic
Export-specific checks can come later.

### 4. Making validation block normal editing too early
Read-oriented validation feedback is enough for this phase.

---

## Acceptance Criteria

Phase 4.4 is complete when:

- validation is computed from persisted project state
- `GET /projects/{project_id}/validation` returns project-specific derived validation items
- static validation payloads are no longer the effective source of truth
- validation changes when persisted requirements, blocks, or components change
- validation output remains compatible with the current frontend model
- the validation layer is implemented in dedicated backend logic rather than scattered across routes

---

## Completion State

At the end of Phase 4.4, Hardware Copilot should have crossed from:

- persisted data with demo-style validation

to:

- persisted data with real derived validation

That means Phase 4 as a whole will have established:
- SQLite persistence
- project identity
- minimal write capability
- validation tied to real project state

This is the first application-grade foundation for later phases such as stronger validation depth, export models, and deterministic KiCad-oriented workflows.
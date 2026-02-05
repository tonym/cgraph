# CGraph Phase 2: Observation Surfaces — Context Summary

## Goal

Expose canonical CGraph memory as read-only, Git-derived observation surfaces with explicit schemas and rebuildable views.

## Outcome

Implemented a dedicated observe CLI namespace with id, parent, and canonical queries, Git-only reads, explicit JSON schemas, tests for read-only and Git-only reconstruction, and updated docs/examples.

## Invariants (Must Remain True)

* Observation surfaces are read-only (no Git or context mutation).
* Git remains the sole source of truth; derived views are disposable.
* No runtime state required to interpret canonical memory.
* No orchestration, execution, or insight layers introduced.

## Key Decisions

* Added a dedicated observe namespace to keep read/write boundaries explicit.
* Implemented observation reads via git ls-tree and git show only.
* Added machine-readable schemas under cgraph/schemas and tightened invariants.
* Added canonical disambiguation flags for summary collisions.

## System Constraints

* No new write paths or lifecycle changes.
* No background processes, triggers, or caching assumptions.
* Minimal query primitives only (id, reference, parent/relationship, canonical).

## Failure Modes (Now Explicit)

* Missing meta.json or content.md raises explicit errors.
* ID collisions require --type and/or --canonical or --non-canonical.
* Meta/id/type mismatches raise explicit errors.

## What Is Explicitly Out of Scope

* Canon mutation, lifecycle writes, or summary generation.
* Orchestration, automation, or execution hooks.
* Semantic search, inference, or insight layers.

## Open Questions / Inputs to Next Phase

* (none)

## Implementation Notes (Optional)

* New read-only module: cgraph/observe.py.
* Git helpers extracted to cgraph/git.py.
* Schemas in cgraph/schemas with if/then invariants.
* Tests in tests/ assert read-only and Git-only reconstruction.

## End State

Phase 2 provides safe, explicit, Git-derived observation of canonical memory with stable schemas and rebuildable views, without expanding authority.

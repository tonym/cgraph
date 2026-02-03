# Zephyr Phase 1 Gate A — Context Summary

## Goal

- Establish a CLI-first, file-backed CGraph kernel that enforces Root → Branch → Summary → Canon → Archive.
- Provide a minimal, Git-legible example proving the full loop.

## Outcome

- Implemented a Python `cgraph` CLI with lifecycle commands and structural enforcement.
- Defined on-disk artifacts as directories containing `meta.json` + `content.md` under `memory/`.
- Added a minimal example project that runs the full loop and leaves proof artifacts.
- Updated `README.md` with structure and usage instructions.

## Invariants (Must Remain True)

* CLI is the sole authority for lifecycle transitions.
* Summaries are the only merge surface into canon.
* No branch may modify canon directly.
* Canonical truth is Git-tracked, file-backed, and human-readable.
* Append-only applies to lifecycle transitions; content remains human-editable.
* No UI, automation, background processes, or orchestration layers.

* Source handoffs: memory/_ops/handoff/2026-02-02-161513-gate-a-implementation.md

## Key Decisions

* Lifecycle directories: `memory/{root,branch,summary,canon,archive}` with `meta.json` + `content.md` per artifact.
* Root id fixed as `root` to enforce single canonical root per project.
* Canon merge appends summary content to root and moves the summary into `memory/canon/`.
* Branch archive moves branch artifacts into `memory/archive/branch/`.
* CLI built with `argparse` and supports `--project` for explicit target directory.

* Source handoffs: memory/_ops/handoff/2026-02-02-161513-gate-a-implementation.md

## System Constraints

* Python standard library only; no third-party CLI frameworks.
* Artifacts must be intelligible by reading files directly.
* Operational outputs must live under `memory/_ops/` and remain non-canonical.

* Source handoffs: memory/_ops/handoff/2026-02-02-161513-gate-a-implementation.md

## Failure Modes (Now Explicit)

* Attempting to merge a branch directly into root is not supported.
* Summaries must be active and attached to an active branch before merge.
* Archived branches cannot be used as parents for new contexts.
* Missing root prevents lifecycle actions; `cgraph init` is required first.

* Source handoffs: memory/_ops/handoff/2026-02-02-161513-gate-a-implementation.md

## What Is Explicitly Out of Scope

* UI (web or otherwise), MCP servers/APIs, automation, watchers/daemons.
* Search, embeddings, indexing, orchestration, or integrations.
* Containerization, deployment, or performance optimization.

## Open Questions / Inputs to Next Phase

* (none)

* Source handoffs: memory/_ops/handoff/2026-02-02-161513-gate-a-implementation.md

## Implementation Notes (Optional)

* Core logic: `cgraph/store.py` and `cgraph/cli.py`.
* Example proof: `examples/minimal/memory/`.
* Documentation: `README.md`.

## End State

- Gate A kernel implemented with enforced lifecycle transitions.
- Canon remains readable without reopening branches via root content updates.
- Example project proves the full loop with Git-diffable artifacts.
- Minimal documentation enables a first run.

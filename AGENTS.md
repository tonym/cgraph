# AGENTS — CGraph Repository

## Repo Nature (Canonical)

This repository implements **CGraph**, the context graph kernel of the Zephyr system.

CGraph is:

- A filesystem- and Git-backed context kernel
- CLI-first
- Append-only by lifecycle
- Concerned with **truth and structure**, not insight, orchestration, or execution

This repository is **infrastructure**, not an application.

These characteristics are **permanent invariants** of this repo.

---

## Project Status

- **Gate A (CGraph Kernel): COMPLETE**
- The Root → Branch → Summary → Canon → Archive lifecycle is implemented and proven.
- This repo now enters a **maintenance + evolution** posture.

Future work may extend capabilities, but **must not violate** the invariants defined here.

---

## Scope Boundaries (Persistent)

### ✅ In Scope

- Python-based CLI tooling
- On-disk artifacts (Markdown + JSON or equivalent)
- Explicit lifecycle transitions:
  - Root
  - Branch
  - Summary
  - Canon merge
  - Archive
- Git as the truth substrate
- Minimal, structural documentation
- Example projects that *prove* behavior

### ❌ Out of Scope (Unless Explicitly Reopened)

- UI (web or otherwise)
- MCP servers or APIs
- Background processes or daemons
- Automation, triggers, or watchers
- Search, embeddings, or insight layers
- Orchestration (handled by CManage)
- Docker or deployment tooling
- Validation substrates
- Product-facing abstractions
- “Future-proofing” layers without concrete need

If a change crosses these boundaries, **the scope must be explicitly redefined first**.

---

## Branching & PR Workflow (Required)

- **Default branch:** `develop`
- **Protected branch:** `main`
  - Treat as stable / releasable
  - No direct pushes
- **Work policy:**
  - Branch from `develop`
  - Open PRs back into `develop`
- **PRs are expected** for all non-trivial changes.
- Keep PRs:
  - Small
  - Reviewable
  - Tightly scoped

Branching discipline is part of the repo’s correctness model.

---

## Design Biases (Hard Preferences)

When making tradeoffs, prefer:

- Explicitness over convenience
- Legibility over flexibility
- Fewer concepts over extensibility
- Boring over clever

If something feels like **product design**, it is likely out of scope.

---

## Agent Operating Guidance

Agents operating in this repo should:

- Treat the filesystem as the primary interface
- Avoid speculative abstractions or directories
- Leave clear, inspectable artifacts
- Prefer correctness proofs over cleverness
- Stop work when invariants are satisfied

Do not “helpfully extend” the system without an explicit mandate.

---

## Authority

This file defines **how this repository is allowed to change**.

It is authoritative until explicitly revised.

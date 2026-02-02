# AGENTS — CGraph Kernel (Gate A)

## Repo Nature

This repository implements **CGraph**, the memory kernel of the Zephyr system.

CGraph is:
- A filesystem- and Git-backed context kernel
- CLI-first
- Append-only
- Concerned with **truth**, not insight, orchestration, or execution

This repo is **infrastructure**, not an application.

---

## Current Phase

**Zephyr Phase 1 — Gate A (CGraph Kernel)**

The only goal of this phase is to establish a durable, disciplined
Root → Branch → Summary → Canon workflow.

---

## Scope (Strict)

### ✅ In Scope
- Python-based CLI
- On-disk artifacts (Markdown + JSON or equivalent)
- Lifecycle enforcement:
  - Root
  - Branch
  - Summary
  - Canon merge
  - Archive
- Git as the truth substrate
- Minimal documentation
- Example project proving the full loop

### ❌ Out of Scope
- UI (web or otherwise)
- MCP servers or APIs
- Background processes or daemons
- Automation, triggers, or watchers
- Search, embeddings, or insight layers
- Integration with CManage
- Docker or deployment tooling
- Validation substrates
- “Future-proofing” abstractions

---

## Design Biases

When making tradeoffs, prefer:
- Explicitness over convenience
- Legibility over flexibility
- Fewer concepts over extensibility
- Boring over clever

If something feels like product design, it is out of scope.

---

## Agent Guidance

Agents operating in this repo should:
- Make small, reviewable changes
- Avoid speculative directories or abstractions
- Treat the filesystem as the primary interface
- Leave clear artifacts that prove correctness

Stop work once Gate A is provably satisfied.

---

## Authority

This file is authoritative for agent behavior in this repository
until explicitly revised.

# CGraph

CGraph is a CLI-first, file-backed context kernel. It enforces a disciplined
Root → Branch → Summary → Canon → Archive lifecycle using Git-readable artifacts.

CGraph is infrastructure, not an application. It manages structure and lifecycle
only; content remains human-authored.

**Scope (Gate A)**
- CLI-first kernel
- On-disk artifacts (Markdown + JSON)
- Lifecycle enforcement and append-only transitions
- Git as the truth substrate

## Repository Structure

Lifecycle artifacts live under a single `memory/` directory:
- `memory/root/`
- `memory/branch/`
- `memory/summary/`
- `memory/canon/`
- `memory/archive/`

Operational outputs (non-canonical) live under:
- `memory/_ops/handoff/`

Each lifecycle artifact is a directory containing:
- `meta.json`
- `content.md`

Only directories with `meta.json` are managed by the CLI. Other files under
`memory/summary/` (such as phase summaries) are allowed but ignored by the CLI.

## Artifact Metadata

Each artifact includes minimal metadata:
- `id`
- `type` (`root`, `branch`, `summary`)
- `status` (`active`, `canonical`, `archived`)
- `title`
- `created_at`
- `parent` (where applicable)

## CLI Usage

Run from a project directory (defaults to current directory) or provide
`--project` before the subcommand.

Initialize a root:
```bash
python -m cgraph init --title "Project Root"
```

Initialize in another directory:
```bash
python -m cgraph --project /path/to/project init --title "Project Root"
```

Create a branch (defaults to `root` as parent):
```bash
python -m cgraph branch new --title "Investigate X"
```

Create a summary from a branch:
```bash
python -m cgraph summary new --title "Summary of X" --branch <branch-id>
```

Merge summary into canon (updates root and moves summary into `memory/canon/`):
```bash
python -m cgraph canon merge --summary <summary-id>
```

Archive a branch (moves branch into `memory/archive/branch/`):
```bash
python -m cgraph branch archive --branch <branch-id>
```

## Observation (Phase 2)

Observation surfaces are read-only and Git-derived. They never write to the
working tree or mutate canon. Use `--ref` to inspect a specific Git ref
(defaults to `HEAD`).

List contexts (optionally filter canonical/non-canonical):
```bash
python -m cgraph observe list --canonical
```

Fetch a context by id (include meta + content by default):
```bash
python -m cgraph observe get --id <context-id>
```

List children by parent reference:
```bash
python -m cgraph observe children --parent branch:<branch-id>
```

Machine-readable schemas live in `cgraph/schemas/`.

### Lifecycle Enforcement

- Branch → Root direct merges are not supported.
- Only summaries can be merged into canon.
- Summaries become canonical after merge and are moved to `memory/canon/`.
- Branches are archived via explicit CLI commands.

## Example Project (Proof)

See `examples/minimal/` for a full Root → Branch → Summary → Canon → Archive
loop with real artifacts created by the CLI.

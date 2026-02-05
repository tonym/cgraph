# Minimal Example

This directory contains a minimal, end-to-end CGraph lifecycle proof.
The `memory/` tree was produced by the CLI using:

1. Root initialization
2. Branch creation
3. Summary creation
4. Summary merge into canon
5. Branch archive

Inspect `memory/` to see the resulting artifacts.

## Observation Walkthrough

From the repository root, observe this example project using read-only commands.

List all contexts (Git-derived, default `HEAD`):
```bash
python -m cgraph --project examples/minimal observe list
```

Fetch a single context by id:
```bash
python -m cgraph --project examples/minimal observe get --id root
```

List children of the example branch (replace with the branch id in meta.json):
```bash
python -m cgraph --project examples/minimal observe children --parent branch:<branch-id>
```

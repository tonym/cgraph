from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIRNAME = "memory"
ROOT_DIRNAME = "root"
BRANCH_DIRNAME = "branch"
SUMMARY_DIRNAME = "summary"
CANON_DIRNAME = "canon"
ARCHIVE_DIRNAME = "archive"
OPS_DIRNAME = "_ops"
HANDOFF_DIRNAME = "handoff"
ROOT_ID = "root"


@dataclass(frozen=True)
class ContextRef:
    type: str
    id: str


class CGraphError(RuntimeError):
    pass


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    cleaned = cleaned.strip("-")
    return cleaned or "untitled"


def make_id(title: str) -> str:
    return f"{timestamp_slug()}-{slugify(title)}"


def memory_path(base: Path) -> Path:
    return base / MEMORY_DIRNAME


def ensure_layout(base: Path) -> None:
    mem = memory_path(base)
    (mem / ROOT_DIRNAME).mkdir(parents=True, exist_ok=True)
    (mem / BRANCH_DIRNAME).mkdir(parents=True, exist_ok=True)
    (mem / SUMMARY_DIRNAME).mkdir(parents=True, exist_ok=True)
    (mem / CANON_DIRNAME).mkdir(parents=True, exist_ok=True)
    (mem / ARCHIVE_DIRNAME / BRANCH_DIRNAME).mkdir(parents=True, exist_ok=True)
    (mem / OPS_DIRNAME / HANDOFF_DIRNAME).mkdir(parents=True, exist_ok=True)


def require_project(base: Path) -> None:
    mem = memory_path(base)
    if not mem.exists():
        raise CGraphError(f"No {MEMORY_DIRNAME}/ found at {base}")
    ensure_layout(base)


def root_dir(base: Path) -> Path:
    return memory_path(base) / ROOT_DIRNAME / ROOT_ID


def branch_dir(base: Path, branch_id: str) -> Path:
    return memory_path(base) / BRANCH_DIRNAME / branch_id


def archive_branch_dir(base: Path, branch_id: str) -> Path:
    return memory_path(base) / ARCHIVE_DIRNAME / BRANCH_DIRNAME / branch_id


def summary_dir(base: Path, summary_id: str) -> Path:
    return memory_path(base) / SUMMARY_DIRNAME / summary_id


def canon_dir(base: Path, summary_id: str) -> Path:
    return memory_path(base) / CANON_DIRNAME / summary_id


def meta_path(context_dir: Path) -> Path:
    return context_dir / "meta.json"


def content_path(context_dir: Path) -> Path:
    return context_dir / "content.md"


def read_meta(context_dir: Path) -> dict:
    path = meta_path(context_dir)
    if not path.exists():
        raise CGraphError(f"Missing meta.json in {context_dir}")
    return json.loads(path.read_text())


def write_meta(context_dir: Path, meta: dict) -> None:
    meta_path(context_dir).write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")


def write_content(context_dir: Path, content: str) -> None:
    content_path(context_dir).write_text(content)


def create_context(context_dir: Path, meta: dict, content: str) -> None:
    context_dir.mkdir(parents=True, exist_ok=False)
    write_meta(context_dir, meta)
    write_content(context_dir, content)


def root_exists(base: Path) -> bool:
    return meta_path(root_dir(base)).exists()


def parse_parent(value: str) -> ContextRef:
    if value == "root":
        return ContextRef("root", ROOT_ID)
    if ":" not in value:
        raise CGraphError("Parent must be in the form <type>:<id> or 'root'")
    parent_type, parent_id = value.split(":", 1)
    if parent_type not in {"root", "branch", "summary"}:
        raise CGraphError("Parent type must be root, branch, or summary")
    if parent_type == "root":
        parent_id = ROOT_ID
    return ContextRef(parent_type, parent_id)


def resolve_parent(base: Path, parent: ContextRef) -> Path:
    if parent.type == "root":
        path = root_dir(base)
    elif parent.type == "branch":
        path = branch_dir(base, parent.id)
    elif parent.type == "summary":
        path = summary_dir(base, parent.id)
        if not path.exists():
            path = canon_dir(base, parent.id)
    else:
        raise CGraphError(f"Unknown parent type {parent.type}")

    if not path.exists():
        raise CGraphError(f"Parent not found: {parent.type}:{parent.id}")

    meta = read_meta(path)
    if meta.get("status") == "archived":
        raise CGraphError(f"Parent is archived: {parent.type}:{parent.id}")
    if parent.type == "branch" and meta.get("status") != "active":
        raise CGraphError(f"Parent branch is not active: {parent.id}")
    return path


def append_canon(root_path: Path, summary_meta: dict, summary_content: str) -> None:
    timestamp = now_iso()
    branch_id = None
    parent = summary_meta.get("parent")
    if isinstance(parent, dict) and parent.get("type") == "branch":
        branch_id = parent.get("id")

    header = [
        "---",
        f"## Canon Update: {summary_meta.get('title')}",
        f"- Summary: {summary_meta.get('id')}",
        f"- Merged: {timestamp}",
    ]
    if branch_id:
        header.append(f"- Source branch: {branch_id}")
    header.append("---")

    block = "\n".join(header) + "\n\n" + summary_content.strip() + "\n"

    existing = content_path(root_path).read_text()
    updated = existing.rstrip() + "\n\n" + block
    write_content(root_path, updated)


def move_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        raise CGraphError(f"Destination already exists: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def is_active_summary(base: Path, summary_id: str) -> bool:
    return summary_dir(base, summary_id).exists()


def is_active_branch(base: Path, branch_id: str) -> bool:
    return branch_dir(base, branch_id).exists()


def load_summary(base: Path, summary_id: str) -> tuple[Path, dict, str]:
    path = summary_dir(base, summary_id)
    if not path.exists():
        raise CGraphError(f"Summary not found: {summary_id}")
    meta = read_meta(path)
    content = content_path(path).read_text()
    return path, meta, content


def load_branch(base: Path, branch_id: str) -> tuple[Path, dict]:
    path = branch_dir(base, branch_id)
    if not path.exists():
        raise CGraphError(f"Branch not found: {branch_id}")
    meta = read_meta(path)
    return path, meta


def load_root(base: Path) -> tuple[Path, dict, str]:
    path = root_dir(base)
    if not path.exists():
        raise CGraphError("Root not initialized")
    meta = read_meta(path)
    content = content_path(path).read_text()
    return path, meta, content

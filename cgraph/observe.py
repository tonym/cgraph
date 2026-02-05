from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .git import git_list_tree, git_show
from .store import (
    ARCHIVE_DIRNAME,
    BRANCH_DIRNAME,
    CANON_DIRNAME,
    CGraphError,
    MEMORY_DIRNAME,
    ROOT_DIRNAME,
    ROOT_ID,
    SUMMARY_DIRNAME,
    ContextRef,
)

OBSERVATION_SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class ObservedContext:
    id: str
    type: str
    status: str
    canonical: bool
    location: str
    parent: dict | None
    meta: dict
    meta_path: str
    content_path: str


def _parse_meta_path(path: str) -> tuple[str, str, str] | None:
    parts = PurePosixPath(path).parts
    if len(parts) == 4 and parts[:2] == (MEMORY_DIRNAME, ROOT_DIRNAME) and parts[2] == ROOT_ID:
        if parts[3] != "meta.json":
            return None
        location = str(PurePosixPath(*parts[:3]))
        return location, "root", ROOT_ID

    if len(parts) == 4 and parts[:2] == (MEMORY_DIRNAME, BRANCH_DIRNAME):
        if parts[3] != "meta.json":
            return None
        location = str(PurePosixPath(*parts[:3]))
        return location, "branch", parts[2]

    if len(parts) == 4 and parts[:2] == (MEMORY_DIRNAME, SUMMARY_DIRNAME):
        if parts[3] != "meta.json":
            return None
        location = str(PurePosixPath(*parts[:3]))
        return location, "summary", parts[2]

    if len(parts) == 4 and parts[:2] == (MEMORY_DIRNAME, CANON_DIRNAME):
        if parts[3] != "meta.json":
            return None
        location = str(PurePosixPath(*parts[:3]))
        return location, "summary", parts[2]

    if len(parts) == 5 and parts[:3] == (MEMORY_DIRNAME, ARCHIVE_DIRNAME, BRANCH_DIRNAME):
        if parts[4] != "meta.json":
            return None
        location = str(PurePosixPath(*parts[:4]))
        return location, "branch", parts[3]

    return None


def _read_json(base: Path, ref: str, path: str) -> dict:
    raw = git_show(base, ref, path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CGraphError(f"Invalid JSON at {path} ({ref})") from exc


def _content_path(meta_path: str) -> str:
    if not meta_path.endswith("/meta.json"):
        raise CGraphError(f"Invalid meta path: {meta_path}")
    return meta_path[: -len("meta.json")] + "content.md"


def collect_contexts(base: Path, ref: str) -> list[ObservedContext]:
    paths = git_list_tree(base, ref, MEMORY_DIRNAME)
    path_set = set(paths)
    meta_paths = [path for path in paths if path.endswith("/meta.json")]
    contexts: list[ObservedContext] = []

    for meta_path in meta_paths:
        parsed = _parse_meta_path(meta_path)
        if parsed is None:
            continue
        location, expected_type, expected_id = parsed
        meta = _read_json(base, ref, meta_path)
        if not isinstance(meta, dict):
            raise CGraphError(f"Metadata must be a JSON object at {meta_path} ({ref})")

        meta_id = meta.get("id")
        meta_type = meta.get("type")
        if meta_id != expected_id:
            raise CGraphError(
                f"Meta id mismatch at {meta_path} ({ref}): expected {expected_id}, got {meta_id}"
            )
        if meta_type != expected_type:
            raise CGraphError(
                f"Meta type mismatch at {meta_path} ({ref}): expected {expected_type}, got {meta_type}"
            )

        status_value = meta.get("status")
        if status_value is None:
            raise CGraphError(f"Missing status in {meta_path} ({ref})")
        status = str(status_value)
        canonical = status == "canonical"
        parent = meta.get("parent") if isinstance(meta.get("parent"), dict) else None
        content_path = _content_path(meta_path)
        if content_path not in path_set:
            raise CGraphError(f"Missing content.md for {location} at {ref}")

        contexts.append(
            ObservedContext(
                id=meta_id,
                type=meta_type,
                status=status,
                canonical=canonical,
                location=location,
                parent=parent,
                meta=meta,
                meta_path=meta_path,
                content_path=content_path,
            )
        )

    if not contexts:
        raise CGraphError(f"No context metadata found at {MEMORY_DIRNAME}/ ({ref})")

    contexts.sort(key=lambda ctx: ctx.location)
    return contexts


def filter_contexts(
    contexts: Iterable[ObservedContext],
    type_filter: str | None = None,
    canonical: bool | None = None,
) -> list[ObservedContext]:
    filtered = []
    for context in contexts:
        if type_filter and context.type != type_filter:
            continue
        if canonical is not None and context.canonical != canonical:
            continue
        filtered.append(context)
    return filtered


def find_context(
    contexts: Iterable[ObservedContext],
    context_id: str,
    context_type: str | None = None,
    canonical: bool | None = None,
) -> ObservedContext:
    matches = [
        context
        for context in contexts
        if context.id == context_id
        and (context_type is None or context.type == context_type)
        and (canonical is None or context.canonical == canonical)
    ]
    if not matches:
        raise CGraphError(f"Context not found: {context_id}")
    if len(matches) > 1:
        raise CGraphError(
            f"Multiple contexts match {context_id}; specify --type or --canonical/--non-canonical"
        )
    return matches[0]


def children_of(contexts: Iterable[ObservedContext], parent: ContextRef) -> list[ObservedContext]:
    results = []
    for context in contexts:
        if not context.parent:
            continue
        if context.parent.get("type") == parent.type and context.parent.get("id") == parent.id:
            results.append(context)
    return results


def serialize_context(context: ObservedContext, include_meta: bool = False) -> dict:
    payload = {
        "id": context.id,
        "type": context.type,
        "status": context.status,
        "canonical": context.canonical,
        "location": context.location,
    }
    if context.parent:
        payload["parent"] = context.parent
    if include_meta:
        payload["meta"] = context.meta
    return payload


def serialize_index(contexts: Iterable[ObservedContext], ref: str) -> dict:
    return {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "ref": ref,
        "contexts": [serialize_context(context) for context in contexts],
    }


def serialize_observation(
    context: ObservedContext,
    ref: str,
    base: Path,
    include_content: bool = True,
) -> dict:
    payload = serialize_context(context, include_meta=True)
    if include_content:
        payload["content"] = git_show(base, ref, context.content_path)
    return {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "ref": ref,
        "context": payload,
    }

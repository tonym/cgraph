from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .git import ensure_git_repo, git_cmd, require_git_repo
from .observe import (
    collect_contexts,
    children_of,
    filter_contexts,
    find_context,
    serialize_index,
    serialize_observation,
)
from .store import (
    ARCHIVE_DIRNAME,
    CANON_DIRNAME,
    CGraphError,
    MEMORY_DIRNAME,
    archive_branch_dir,
    append_canon,
    branch_dir,
    canon_dir,
    create_context,
    ensure_layout,
    is_active_branch,
    is_active_summary,
    load_branch,
    load_root,
    load_summary,
    make_id,
    now_iso,
    parse_parent,
    resolve_parent,
    root_dir,
    root_exists,
    summary_dir,
    write_meta,
)


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def project_path(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd()


def commit_memory(base: Path, message: str) -> None:
    git_cmd(base, ["add", "-A", "--", MEMORY_DIRNAME])
    status = git_cmd(base, ["status", "--porcelain", "--", MEMORY_DIRNAME])
    if not status.stdout.strip():
        return
    git_cmd(base, ["commit", "-m", message, "--", MEMORY_DIRNAME])


def cmd_init(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    ensure_git_repo(base)
    if root_exists(base):
        fail("root already exists")

    ensure_layout(base)

    root = root_dir(base)
    meta = {
        "id": "root",
        "type": "root",
        "status": "canonical",
        "title": args.title,
        "created_at": now_iso(),
    }
    content = f"# {args.title}\n\nCanonical root context.\n"
    create_context(root, meta, content)
    commit_memory(base, f"cgraph init: {args.title}")
    print(f"root created at {root}")


def cmd_branch_new(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)
    if not root_exists(base):
        fail("root not initialized; run 'cgraph init'")

    ensure_layout(base)

    parent = parse_parent(args.parent)
    resolve_parent(base, parent)

    branch_id = make_id(args.title)
    branch = branch_dir(base, branch_id)

    meta = {
        "id": branch_id,
        "type": "branch",
        "status": "active",
        "title": args.title,
        "created_at": now_iso(),
        "parent": {"type": parent.type, "id": parent.id},
    }
    content = f"# {args.title}\n\nBranch context.\n"

    create_context(branch, meta, content)
    commit_memory(base, f"cgraph branch: {branch_id}")
    print(branch_id)


def cmd_summary_new(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)
    if not root_exists(base):
        fail("root not initialized; run 'cgraph init'")

    ensure_layout(base)

    branch_path, branch_meta = load_branch(base, args.branch)
    if branch_meta.get("status") != "active":
        fail("branch is not active")

    summary_id = make_id(args.title)
    summary = summary_dir(base, summary_id)

    meta = {
        "id": summary_id,
        "type": "summary",
        "status": "active",
        "title": args.title,
        "created_at": now_iso(),
        "parent": {"type": "branch", "id": args.branch},
    }
    content = f"# {args.title}\n\nSummary content.\n"

    create_context(summary, meta, content)
    commit_memory(base, f"cgraph summary: {summary_id}")
    print(summary_id)


def cmd_canon_merge(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)
    if not root_exists(base):
        fail("root not initialized; run 'cgraph init'")

    ensure_layout(base)

    if not is_active_summary(base, args.summary):
        fail("summary not found or already merged")

    summary_path, summary_meta, summary_content = load_summary(base, args.summary)
    if summary_meta.get("status") != "active":
        fail("summary is not active")

    parent = summary_meta.get("parent")
    if not parent or parent.get("type") != "branch":
        fail("summary parent is not a branch")

    branch_id = parent.get("id")
    if not branch_id or not is_active_branch(base, branch_id):
        fail("source branch must be active to merge")

    root_path, root_meta, _ = load_root(base)
    append_canon(root_path, summary_meta, summary_content)

    root_meta["updated_at"] = now_iso()
    root_meta["latest_summary_id"] = summary_meta.get("id")
    write_meta(root_path, root_meta)

    summary_meta["status"] = "canonical"
    summary_meta["merged_at"] = now_iso()
    write_meta(summary_path, summary_meta)

    destination = canon_dir(base, args.summary)
    from .store import move_dir

    move_dir(summary_path, destination)
    commit_memory(base, f"cgraph canon merge: {args.summary}")
    print(f"summary merged into root; moved to {CANON_DIRNAME}/")


def cmd_branch_archive(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)
    if not root_exists(base):
        fail("root not initialized; run 'cgraph init'")

    ensure_layout(base)

    branch_path, branch_meta = load_branch(base, args.branch)
    if branch_meta.get("status") == "archived":
        fail("branch already archived")

    branch_meta["status"] = "archived"
    branch_meta["archived_at"] = now_iso()
    write_meta(branch_path, branch_meta)

    destination = archive_branch_dir(base, args.branch)
    from .store import move_dir

    move_dir(branch_path, destination)
    commit_memory(base, f"cgraph branch archive: {args.branch}")
    print(f"branch archived to {ARCHIVE_DIRNAME}/")


def cmd_observe_get(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)

    if args.canonical and args.non_canonical:
        fail("choose only one of --canonical or --non-canonical")

    canonical_filter = None
    if args.canonical:
        canonical_filter = True
    elif args.non_canonical:
        canonical_filter = False

    contexts = collect_contexts(base, args.ref)
    context = find_context(contexts, args.id, args.type, canonical_filter)
    payload = serialize_observation(context, args.ref, base, include_content=not args.meta_only)
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_observe_list(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)

    if args.canonical and args.non_canonical:
        fail("choose only one of --canonical or --non-canonical")

    canonical_filter = None
    if args.canonical:
        canonical_filter = True
    elif args.non_canonical:
        canonical_filter = False

    contexts = collect_contexts(base, args.ref)
    contexts = filter_contexts(contexts, args.type, canonical_filter)
    payload = serialize_index(contexts, args.ref)
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_observe_children(args: argparse.Namespace) -> None:
    base = project_path(args.project)
    require_git_repo(base)

    parent = parse_parent(args.parent)
    contexts = collect_contexts(base, args.ref)
    children = children_of(contexts, parent)
    payload = serialize_index(children, args.ref)
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cgraph")
    parser.add_argument(
        "--project",
        help="Path to the project root (defaults to current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a CGraph project root")
    init_parser.add_argument("--title", required=True, help="Root title")
    init_parser.set_defaults(func=cmd_init)

    branch_parser = subparsers.add_parser("branch", help="Branch lifecycle commands")
    branch_sub = branch_parser.add_subparsers(dest="branch_cmd", required=True)

    branch_new = branch_sub.add_parser("new", help="Create a new branch")
    branch_new.add_argument("--title", required=True, help="Branch title")
    branch_new.add_argument(
        "--from",
        dest="parent",
        default="root",
        help="Parent context (root or <type>:<id>)",
    )
    branch_new.set_defaults(func=cmd_branch_new)

    branch_archive = branch_sub.add_parser("archive", help="Archive a branch")
    branch_archive.add_argument("--branch", required=True, help="Branch id")
    branch_archive.set_defaults(func=cmd_branch_archive)

    summary_parser = subparsers.add_parser("summary", help="Summary lifecycle commands")
    summary_sub = summary_parser.add_subparsers(dest="summary_cmd", required=True)

    summary_new = summary_sub.add_parser("new", help="Create a new summary")
    summary_new.add_argument("--title", required=True, help="Summary title")
    summary_new.add_argument("--branch", required=True, help="Source branch id")
    summary_new.set_defaults(func=cmd_summary_new)

    canon_parser = subparsers.add_parser("canon", help="Canon lifecycle commands")
    canon_sub = canon_parser.add_subparsers(dest="canon_cmd", required=True)

    canon_merge = canon_sub.add_parser("merge", help="Merge summary into root")
    canon_merge.add_argument("--summary", required=True, help="Summary id")
    canon_merge.set_defaults(func=cmd_canon_merge)

    observe_parser = subparsers.add_parser("observe", help="Read-only observation commands")
    observe_sub = observe_parser.add_subparsers(dest="observe_cmd", required=True)

    observe_get = observe_sub.add_parser("get", help="Fetch a context by id")
    observe_get.add_argument("--id", required=True, help="Context id")
    observe_get.add_argument(
        "--type",
        choices=["root", "branch", "summary"],
        help="Optional context type to disambiguate ids",
    )
    observe_get.add_argument(
        "--canonical",
        action="store_true",
        help="Require canonical context",
    )
    observe_get.add_argument(
        "--non-canonical",
        action="store_true",
        help="Require non-canonical context",
    )
    observe_get.add_argument(
        "--ref",
        default="HEAD",
        help="Git ref to read from (default: HEAD)",
    )
    observe_get.add_argument(
        "--meta-only",
        action="store_true",
        help="Exclude content.md from output",
    )
    observe_get.set_defaults(func=cmd_observe_get)

    observe_list = observe_sub.add_parser("list", help="List contexts")
    observe_list.add_argument(
        "--type",
        choices=["root", "branch", "summary"],
        help="Optional context type filter",
    )
    observe_list.add_argument(
        "--canonical",
        action="store_true",
        help="Only include canonical contexts",
    )
    observe_list.add_argument(
        "--non-canonical",
        action="store_true",
        help="Only include non-canonical contexts",
    )
    observe_list.add_argument(
        "--ref",
        default="HEAD",
        help="Git ref to read from (default: HEAD)",
    )
    observe_list.set_defaults(func=cmd_observe_list)

    observe_children = observe_sub.add_parser("children", help="List contexts by parent")
    observe_children.add_argument(
        "--parent",
        required=True,
        help="Parent context (root or <type>:<id>)",
    )
    observe_children.add_argument(
        "--ref",
        default="HEAD",
        help="Git ref to read from (default: HEAD)",
    )
    observe_children.set_defaults(func=cmd_observe_children)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except CGraphError as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from cgraph.observe import (
    OBSERVATION_SCHEMA_VERSION,
    collect_contexts,
    children_of,
    find_context,
    serialize_index,
    serialize_observation,
)
from cgraph.store import (
    ARCHIVE_DIRNAME,
    BRANCH_DIRNAME,
    CANON_DIRNAME,
    MEMORY_DIRNAME,
    ROOT_DIRNAME,
    SUMMARY_DIRNAME,
    ContextRef,
    CGraphError,
)


def run_git(base: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "CGraph Test",
            "GIT_AUTHOR_EMAIL": "cgraph-test@example.com",
            "GIT_COMMITTER_NAME": "CGraph Test",
            "GIT_COMMITTER_EMAIL": "cgraph-test@example.com",
        }
    )
    return subprocess.run(
        ["git", "-C", str(base), *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


def git_status(base: Path) -> str:
    result = run_git(base, ["status", "--porcelain"])
    return result.stdout.strip()


def write_context(context_dir: Path, meta: dict, content: str) -> None:
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    (context_dir / "content.md").write_text(content)


class ObserveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        base = Path(self.tempdir.name)
        run_git(base, ["init"])

        memory = base / MEMORY_DIRNAME
        write_context(
            memory / ROOT_DIRNAME / "root",
            {
                "id": "root",
                "type": "root",
                "status": "canonical",
                "title": "Root",
                "created_at": "2026-02-05T00:00:00Z",
            },
            "# Root\n",
        )
        write_context(
            memory / BRANCH_DIRNAME / "b1",
            {
                "id": "b1",
                "type": "branch",
                "status": "active",
                "title": "Branch",
                "created_at": "2026-02-05T00:01:00Z",
                "parent": {"type": "root", "id": "root"},
            },
            "# Branch\n",
        )
        write_context(
            memory / SUMMARY_DIRNAME / "s1",
            {
                "id": "s1",
                "type": "summary",
                "status": "active",
                "title": "Summary",
                "created_at": "2026-02-05T00:02:00Z",
                "parent": {"type": "branch", "id": "b1"},
            },
            "# Summary\n",
        )
        write_context(
            memory / CANON_DIRNAME / "s2",
            {
                "id": "s2",
                "type": "summary",
                "status": "canonical",
                "title": "Canon",
                "created_at": "2026-02-05T00:03:00Z",
                "merged_at": "2026-02-05T00:04:00Z",
                "parent": {"type": "branch", "id": "b1"},
            },
            "# Canon\n",
        )
        write_context(
            memory / ARCHIVE_DIRNAME / BRANCH_DIRNAME / "b2",
            {
                "id": "b2",
                "type": "branch",
                "status": "archived",
                "title": "Old Branch",
                "created_at": "2026-02-05T00:05:00Z",
                "archived_at": "2026-02-05T00:06:00Z",
                "parent": {"type": "root", "id": "root"},
            },
            "# Archived Branch\n",
        )

        run_git(base, ["add", "-A"])
        run_git(base, ["commit", "-m", "fixture"])
        self.base = base

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_observe_is_read_only(self) -> None:
        before = git_status(self.base)
        contexts = collect_contexts(self.base, "HEAD")
        payload = serialize_index(contexts, "HEAD")
        self.assertEqual(payload["schema_version"], OBSERVATION_SCHEMA_VERSION)
        after = git_status(self.base)
        self.assertEqual(before, after)

    def test_observe_children_by_parent(self) -> None:
        contexts = collect_contexts(self.base, "HEAD")
        children = children_of(contexts, ContextRef("branch", "b1"))
        ids = sorted(context.id for context in children)
        self.assertEqual(ids, ["s1", "s2"])

    def test_observe_meta_only(self) -> None:
        contexts = collect_contexts(self.base, "HEAD")
        context = find_context(contexts, "root", "root")
        payload = serialize_observation(context, "HEAD", self.base, include_content=False)
        self.assertIn("meta", payload["context"])
        self.assertNotIn("content", payload["context"])

    def test_observe_reads_from_git_without_worktree(self) -> None:
        shutil.rmtree(self.base / MEMORY_DIRNAME)
        contexts = collect_contexts(self.base, "HEAD")
        self.assertTrue(contexts)

    def test_missing_content_raises_error(self) -> None:
        missing = self.base / MEMORY_DIRNAME / SUMMARY_DIRNAME / "s1" / "content.md"
        missing.unlink()
        run_git(self.base, ["add", "-A"])
        run_git(self.base, ["commit", "-m", "remove content"])
        with self.assertRaises(CGraphError):
            collect_contexts(self.base, "HEAD")

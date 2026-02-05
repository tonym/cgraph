from __future__ import annotations

import subprocess
from pathlib import Path

from .store import CGraphError


def git_cmd(base: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(base), *args],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise CGraphError("git is not installed or not on PATH") from exc

    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        message = f"git {' '.join(args)} failed"
        if detail:
            message = f"{message}: {detail}"
        raise CGraphError(message)

    return result


def is_git_repo(base: Path) -> bool:
    if not base.exists():
        return False
    result = git_cmd(base, ["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0


def ensure_git_repo(base: Path) -> None:
    if not base.exists():
        base.mkdir(parents=True)
    if is_git_repo(base):
        return
    git_cmd(base, ["init"])


def require_git_repo(base: Path) -> None:
    if not base.exists():
        raise CGraphError(f"Project path does not exist: {base}")
    if not is_git_repo(base):
        raise CGraphError("Project is not a Git repository; run 'cgraph init'")


def git_show(base: Path, ref: str, path: str) -> str:
    result = git_cmd(base, ["show", f"{ref}:{path}"])
    return result.stdout


def git_list_tree(base: Path, ref: str, path: str) -> list[str]:
    result = git_cmd(base, ["ls-tree", "-r", "--name-only", ref, "--", path])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

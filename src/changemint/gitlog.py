"""Reading commit history out of git.

Kept separate from parsing so tests can feed raw log text straight into the
parser without touching a real repository.
"""

from __future__ import annotations

import shutil
import subprocess

from .errors import BadRefError, GitNotFoundError, NoCommitsError, NotAGitRepoError

# Unit separator between fields, record separator between commits. Using
# control characters instead of newlines means multi-line bodies can't
# break the split.
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"
_LOG_FORMAT = _FIELD_SEP.join(["%H", "%ad", "%s", "%b"]) + _RECORD_SEP


def _run_git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    """Run git, raising a friendly error when git itself is the problem."""
    if shutil.which("git") is None:
        raise GitNotFoundError(
            "git is not installed or not on your PATH. "
            "Install git, then try again."
        )
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:  # pragma: no cover - defensive, hard to trigger
        raise GitNotFoundError(f"could not run git: {exc}") from exc


def ensure_repo(path: str) -> None:
    """Raise NotAGitRepoError unless `path` is inside a git repository."""
    result = _run_git(["rev-parse", "--git-dir"], cwd=path)
    if result.returncode != 0:
        raise NotAGitRepoError(
            f"'{path}' is not inside a git repository. "
            "Run changemint from a repo, or pass --repo."
        )


def read_log(
    repo: str,
    since: str | None = None,
    until: str | None = None,
    max_count: int | None = None,
) -> str:
    """Return the raw `git log` output for the requested range.

    `since`/`until` are refs (tags, branches, SHAs) forming the range
    `since..until`. Either end may be omitted for an open-ended range.
    """
    ensure_repo(repo)

    args = ["log", f"--format={_LOG_FORMAT}", "--date=short"]
    if max_count is not None:
        args.append(f"--max-count={max_count}")
    if since is not None or until is not None:
        args.append(f"{since or ''}..{until or 'HEAD'}")

    result = _run_git(args, cwd=repo)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "does not have any commits yet" in stderr:
            # A fresh repo with zero commits: not a bad ref, just empty.
            raise NoCommitsError(
                "This repo has no commits yet, so there is nothing "
                "to put in a changelog."
            )
        # git's own message names the bad ref; surface it, don't guess.
        raise BadRefError(
            f"git could not read that range: {stderr or 'unknown error'}. "
            "Check the --since / --until refs exist (tag, branch or SHA)."
        )
    return result.stdout

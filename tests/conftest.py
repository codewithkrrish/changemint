"""Shared fixtures: a throwaway git repo with a known history."""

from __future__ import annotations

import subprocess

import pytest


def _git(repo: str, *args: str, env_extra: dict | None = None) -> None:
    import os

    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": "Test Dev",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test Dev",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }
    )
    if env_extra:
        env.update(env_extra)
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )


@pytest.fixture()
def repo(tmp_path):
    """A git repo with a small conventional-commit history, tagged v0.1.0."""
    path = str(tmp_path)
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "Test Dev")
    _git(path, "config", "user.email", "test@example.com")
    (tmp_path / "a.txt").write_text("one\n")
    _git(path, "add", ".")
    _git(path, "commit", "-q", "-m", "feat: add the first thing")
    _git(path, "tag", "v0.1.0")
    (tmp_path / "a.txt").write_text("two\n")
    _git(path, "add", ".")
    _git(path, "commit", "-q", "-m", "fix(parser): handle empty input")
    (tmp_path / "a.txt").write_text("three\n")
    _git(path, "add", ".")
    _git(path, "commit", "-q", "-m", "docs: explain the setup")
    return path


@pytest.fixture()
def empty_repo(tmp_path):
    """A git repo with zero commits."""
    path = str(tmp_path)
    _git(path, "init", "-q")
    return path

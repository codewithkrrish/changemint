"""End-to-end CLI tests against real (temporary) git repos."""

from __future__ import annotations

import os
import subprocess

import pytest

from changemint.cli import main


def _run_cli(args: list[str]) -> int:
    return main(args)


def test_full_run_writes_grouped_changelog(repo, tmp_path, monkeypatch):
    out = tmp_path / "CHANGELOG.md"
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--output", str(out)]) == 0
    text = out.read_text()
    assert "## [Unreleased]" in text
    assert "### Features" in text
    assert "add the first thing" in text
    assert "### Bug Fixes" in text
    assert "handle empty input" in text
    assert "### Documentation" in text


def test_since_until_range_limits_commits(repo, tmp_path, monkeypatch):
    out = tmp_path / "CHANGELOG.md"
    monkeypatch.chdir(tmp_path)
    assert (
        _run_cli(["--repo", repo, "--since", "v0.1.0", "--output", str(out)])
        == 0
    )
    text = out.read_text()
    assert "add the first thing" not in text  # the tagged commit is excluded
    assert "handle empty input" in text


def test_refuses_to_overwrite_without_force(repo, tmp_path, monkeypatch):
    out = tmp_path / "CHANGELOG.md"
    out.write_text("my hand-written notes\n")
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--output", str(out)]) == 4
    assert out.read_text() == "my hand-written notes\n"


def test_force_overwrites(repo, tmp_path, monkeypatch):
    out = tmp_path / "CHANGELOG.md"
    out.write_text("old notes\n")
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--output", str(out), "--force"]) == 0
    assert "old notes" not in out.read_text()


def test_dry_run_writes_nothing(repo, tmp_path, monkeypatch, capsys):
    out = tmp_path / "CHANGELOG.md"
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--output", str(out), "--dry-run"]) == 0
    assert not out.exists()
    captured = capsys.readouterr()
    assert "add the first thing" in captured.out
    assert "dry run" in captured.err


def test_stdout_mode_writes_nothing(repo, tmp_path, monkeypatch, capsys):
    out = tmp_path / "CHANGELOG.md"
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--output", str(out), "--stdout"]) == 0
    assert not out.exists()
    assert "### Features" in capsys.readouterr().out


def test_bad_ref_exits_2_with_human_message(repo, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--since", "no-such-tag"]) == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "--since" in err or "range" in err


def test_not_a_repo_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", str(tmp_path)]) == 2
    assert "not inside a git repository" in capsys.readouterr().err


def test_empty_repo_exits_3(empty_repo, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", empty_repo]) == 3
    assert "no commits yet" in capsys.readouterr().err


def test_bad_max_count_exits_2(repo, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert _run_cli(["--repo", repo, "--max-count", "0"]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_version_flag_labels_heading(repo, tmp_path, monkeypatch):
    out = tmp_path / "CHANGELOG.md"
    monkeypatch.chdir(tmp_path)
    assert (
        _run_cli(
            ["--repo", repo, "--output", str(out), "--version", "1.2.0"]
        )
        == 0
    )
    assert "## [1.2.0] - " in out.read_text()


def test_console_script_entry_point(tmp_path):
    """pip install -e . then `changemint --help` must work."""
    result = subprocess.run(
        ["python3", "-m", "pip", "install", "-q", "-e", "."],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    help_run = subprocess.run(
        ["changemint", "--help"], capture_output=True, text=True
    )
    assert help_run.returncode == 0
    assert "CHANGELOG.md" in help_run.stdout

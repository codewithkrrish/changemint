"""Tests for conventional-commit parsing."""

from changemint.commits import parse_log, parse_subject
from changemint.gitlog import _FIELD_SEP, _RECORD_SEP


def _raw(*subjects: str) -> str:
    """Build a fake git log record string from subjects."""
    records = []
    for i, subject in enumerate(subjects):
        records.append(
            _FIELD_SEP.join(
                [f"abc123{i:04d}", "2026-11-20", subject, ""]
            )
        )
    return _RECORD_SEP.join(records) + _RECORD_SEP


def test_simple_feat_and_fix():
    commits = parse_log(_raw("feat: add search", "fix: crash on empty file"))
    assert [c.type for c in commits] == ["feat", "fix"]
    assert commits[0].description == "add search"
    assert commits[1].description == "crash on empty file"


def test_scope_is_captured():
    commits = parse_log(_raw("feat(auth): add login"))
    assert commits[0].type == "feat"
    assert commits[0].scope == "auth"
    assert commits[0].description == "add login"


def test_bang_marks_breaking():
    commits = parse_log(_raw("feat!: drop the old API"))
    assert commits[0].breaking is True


def test_breaking_change_footer():
    raw = _FIELD_SEP.join(
        [
            "abc1230001",
            "2026-11-20",
            "refactor: rename config key",
            "BREAKING CHANGE: old key no longer works",
        ]
    ) + _RECORD_SEP
    commits = parse_log(raw)
    assert commits[0].breaking is True


def test_freeform_subject_becomes_other():
    commits = parse_log(_raw("updated some stuff", "WIP"))
    assert all(c.type == "other" for c in commits)
    assert commits[0].description == "updated some stuff"


def test_unknown_prefix_becomes_other():
    commits = parse_log(_raw("wip: half done"))
    assert commits[0].type == "other"


def test_empty_log_gives_empty_list():
    assert parse_log("") == []
    assert parse_log("\n") == []


def test_malformed_record_is_skipped_not_fatal():
    raw = "not-a-record" + _RECORD_SEP + _raw("fix: still parsed")
    commits = parse_log(raw)
    assert len(commits) == 1
    assert commits[0].type == "fix"


def test_parse_subject_directly():
    assert parse_subject("docs(readme): fix typo", "")[:3] == (
        "docs",
        "readme",
        "fix typo",
    )

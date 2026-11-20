"""Tests for changelog rendering and grouping."""

from changemint.commits import Commit
from changemint.render import group_commits, render_changelog


def _commit(ctype: str, desc: str, breaking: bool = False, scope=None) -> Commit:
    return Commit(
        sha="a" * 40,
        date="2026-11-20",
        type=ctype,
        scope=scope,
        description=desc,
        breaking=breaking,
    )


def test_breaking_commits_get_their_own_section_first():
    commits = [
        _commit("feat", "add search"),
        _commit("feat", "remove old API", breaking=True),
    ]
    out = render_changelog(commits, version="1.0.0")
    assert out.index("### Breaking Changes") < out.index("### Features")
    assert "remove old API" in out


def test_sections_in_scan_order():
    commits = [_commit("docs", "update readme"), _commit("fix", "fix crash")]
    out = render_changelog(commits)
    assert out.index("### Bug Fixes") < out.index("### Documentation")


def test_empty_groups_are_omitted():
    out = render_changelog([_commit("fix", "fix crash")])
    assert "### Features" not in out
    assert "### Bug Fixes" in out


def test_scope_is_bolded_in_entry():
    out = render_changelog([_commit("feat", "add login", scope="auth")])
    assert "- **auth**: add login" in out


def test_version_heading_uses_date_when_versioned():
    out = render_changelog(
        [_commit("feat", "x")], version="1.2.0", date="2026-11-20"
    )
    assert "## [1.2.0] - 2026-11-20" in out


def test_unreleased_heading_has_no_date():
    out = render_changelog([_commit("feat", "x")])
    assert "## [Unreleased]" in out


def test_group_commits_preserves_order():
    commits = [_commit("fix", "first"), _commit("fix", "second")]
    groups = group_commits(commits)
    assert [c.description for c in groups["fix"]] == ["first", "second"]

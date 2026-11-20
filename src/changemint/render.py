"""Rendering parsed commits as a Markdown changelog.

Groups follow the conventional-commit order people actually scan for:
breaking changes first, then features, then fixes, then everything else.
"""

from __future__ import annotations

from .commits import Commit

# Display heading per commit type, in the order sections appear.
SECTION_ORDER: list[tuple[str, str]] = [
    ("breaking", "Breaking Changes"),
    ("feat", "Features"),
    ("fix", "Bug Fixes"),
    ("perf", "Performance"),
    ("refactor", "Refactoring"),
    ("docs", "Documentation"),
    ("test", "Tests"),
    ("build", "Build"),
    ("ci", "CI"),
    ("style", "Style"),
    ("chore", "Chores"),
    ("revert", "Reverts"),
    ("other", "Other Changes"),
]


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    """Bucket commits by section key, preserving log order within a group."""
    groups: dict[str, list[Commit]] = {key: [] for key, _ in SECTION_ORDER}
    for commit in commits:
        if commit.breaking:
            groups["breaking"].append(commit)
        else:
            groups[commit.type].append(commit)
    return groups


def _format_entry(commit: Commit) -> str:
    """One bullet: description, scope in bold, short hash for traceability."""
    scope = f"**{commit.scope}**: " if commit.scope else ""
    return f"- {scope}{commit.description} ({commit.short_sha})"


def render_changelog(
    commits: list[Commit],
    title: str = "Changelog",
    version: str = "Unreleased",
    date: str | None = None,
) -> str:
    """Render the full Markdown document for a list of commits."""
    groups = group_commits(commits)
    lines = [f"# {title}", ""]
    heading = f"## [{version}]"
    if date:
        heading += f" - {date}"
    lines.append(heading)
    lines.append("")

    for key, label in SECTION_ORDER:
        entries = groups[key]
        if not entries:
            continue
        lines.append(f"### {label}")
        lines.append("")
        lines.extend(_format_entry(commit) for commit in entries)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

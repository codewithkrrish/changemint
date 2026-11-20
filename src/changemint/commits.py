"""Parsing raw git log output into conventional commits.

A "conventional" subject looks like `feat(auth): add login` or
`fix!: drop the old API`. Anything else is kept as an untyped commit and
lands under "Other changes" instead of being thrown away — a changelog
that silently drops half your history is worse than a messy one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .gitlog import _FIELD_SEP, _RECORD_SEP

# type(scope)!: description   — scope and the ! are both optional
_SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<bang>!)?"
    r":\s(?P<desc>.+)$"
)

# Keep the full conventional-commit vocabulary; anything else is "other".
KNOWN_TYPES = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
}


@dataclass(frozen=True)
class Commit:
    """One parsed commit."""

    sha: str
    date: str
    type: str  # conventional type, or "other" for free-form subjects
    scope: str | None
    description: str
    breaking: bool

    @property
    def short_sha(self) -> str:
        """First 7 characters of the hash, like git's own short form."""
        return self.sha[:7]


def _is_breaking(subject: str, body: str) -> bool:
    """Breaking if `!` is in the subject or the body has a BREAKING CHANGE footer."""
    if "!" in subject.split(":", 1)[0]:
        return True
    return any(
        line.startswith("BREAKING CHANGE:")
        or line.startswith("BREAKING-CHANGE:")
        for line in body.splitlines()
    )


def parse_subject(subject: str, body: str) -> tuple[str, str | None, str, bool]:
    """Split a subject into (type, scope, description, breaking)."""
    match = _SUBJECT_RE.match(subject.strip())
    if match is None:
        return "other", None, subject.strip(), _is_breaking(subject, body)

    ctype = match.group("type")
    if ctype not in KNOWN_TYPES:
        # Unknown prefix like `wip: stuff` — keep the text, don't invent a group.
        return "other", None, subject.strip(), _is_breaking(subject, body)

    return (
        ctype,
        match.group("scope"),
        match.group("desc").strip(),
        bool(match.group("bang")) or _is_breaking(subject, body),
    )


def parse_log(raw: str) -> list[Commit]:
    """Parse the record-separated output of `git log` into Commit objects."""
    commits: list[Commit] = []
    for record in raw.split(_RECORD_SEP):
        record = record.strip("\n")
        if not record.strip():
            continue
        fields = record.split(_FIELD_SEP)
        if len(fields) != 4:
            # A malformed record is skipped, not fatal — one weird commit
            # shouldn't kill the whole changelog.
            continue
        sha, date, subject, body = fields
        ctype, scope, description, breaking = parse_subject(subject, body)
        commits.append(
            Commit(
                sha=sha.strip(),
                date=date.strip(),
                type=ctype,
                scope=scope,
                description=description,
                breaking=breaking,
            )
        )
    return commits

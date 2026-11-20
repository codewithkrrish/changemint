"""Command-line interface: thin layer over gitlog / commits / render.

The CLI owns argument parsing, exit codes and file writing. All real work
happens in the modules it calls, so the logic stays testable without
spawning a process.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from datetime import date

from .commits import parse_log
from .errors import ChangemintError, NoCommitsError, OutputExistsError
from .gitlog import read_log
from .render import render_changelog

DEFAULT_OUTPUT = "CHANGELOG.md"
MAX_COMMITS_DEFAULT = 500


def build_parser() -> argparse.ArgumentParser:
    """Define the CLI. Kept in its own function so tests can inspect it."""
    parser = argparse.ArgumentParser(
        prog="changemint",
        description="Turn a git log into a clean, grouped CHANGELOG.md.",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="path to the git repository (default: current directory)",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="start of the range: a tag, branch or SHA (default: first commit)",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="end of the range: a tag, branch or SHA (default: HEAD)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT,
        help=f"output file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--version",
        "-v",
        default="Unreleased",
        help="version label for the section heading (default: Unreleased)",
    )
    parser.add_argument(
        "--title",
        default="Changelog",
        help="top-level document title (default: Changelog)",
    )
    parser.add_argument(
        "--max-count",
        type=int,
        default=MAX_COMMITS_DEFAULT,
        help=f"maximum commits to include (default: {MAX_COMMITS_DEFAULT})",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the changelog instead of writing a file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would be written, without writing anything",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite the output file if it already exists",
    )
    return parser


def _write_atomic(path: str, content: str) -> None:
    """Write via a temp file in the same directory, then rename.

    A crash mid-write leaves the old file intact instead of a half-written
    changelog.
    """
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".changemint-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def generate(
    repo: str,
    since: str | None,
    until: str | None,
    max_count: int,
    title: str,
    version: str,
) -> str:
    """Read the log and render it. Raises ChangemintError on any failure."""
    raw = read_log(repo, since=since, until=until, max_count=max_count)
    commits = parse_log(raw)
    if not commits:
        raise NoCommitsError(
            "No commits found in that range. "
            "Check --since / --until, or pick a repo with some history."
        )
    today = date.today().isoformat() if version != "Unreleased" else None
    return render_changelog(commits, title=title, version=version, date=today)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code; never raises to the user."""
    args = build_parser().parse_args(argv)
    try:
        if args.max_count is not None and args.max_count <= 0:
            print(
                "changemint: --max-count must be a positive number.",
                file=sys.stderr,
            )
            return 2

        content = generate(
            repo=args.repo,
            since=args.since,
            until=args.until,
            max_count=args.max_count,
            title=args.title,
            version=args.version,
        )

        if args.stdout or args.dry_run:
            print(content, end="")
            if args.dry_run:
                print(
                    f"\n[dry run] would write {len(content)} chars to "
                    f"{args.output}",
                    file=sys.stderr,
                )
            return 0

        if os.path.exists(args.output) and not args.force:
            raise OutputExistsError(
                f"{args.output} already exists. "
                "Pass --force to overwrite it, or --output to pick another file."
            )

        _write_atomic(args.output, content)
        print(f"Wrote {args.output} ({len(content)} chars, {content.count(chr(10))} lines).")
        return 0
    except ChangemintError as exc:
        print(f"changemint: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    sys.exit(main())

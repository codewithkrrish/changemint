"""Errors raised by changemint.

Every failure a user can hit gets its own type so the CLI can print a
plain-English message and exit with the right code instead of dumping a
traceback.
"""


class ChangemintError(Exception):
    """Base class for all changemint errors."""

    exit_code: int = 1


class GitNotFoundError(ChangemintError):
    """The `git` binary is not on PATH."""

    exit_code = 2


class NotAGitRepoError(ChangemintError):
    """The target directory is not inside a git repository."""

    exit_code = 2


class BadRefError(ChangemintError):
    """A --since/--until ref does not resolve to a commit."""

    exit_code = 2


class NoCommitsError(ChangemintError):
    """No commits matched the requested range."""

    exit_code = 3


class OutputExistsError(ChangemintError):
    """The output file already exists and --force was not given."""

    exit_code = 4

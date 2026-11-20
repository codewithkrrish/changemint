# changemint

Turn a git log into a clean, grouped CHANGELOG.md. Zero dependencies, just Python and git.

I write conventional commits most of the time — `feat:`, `fix:`, `docs:` — but every release I still ended up hand-writing the changelog, scrolling through `git log` and copying lines into sections. It was boring, and I kept missing things. So I wrote the little tool I wanted to exist: point it at a repo, get a grouped changelog back.

```bash
pip install git+https://github.com/codewithkrrish/changemint.git
cd my-project
changemint --since v1.2.0 --version 1.3.0
```

That writes `CHANGELOG.md` in the current directory:

```markdown
# Changelog

## [1.3.0] - 2026-11-20

### Breaking Changes

- drop the old config format (a1b2c3d)

### Features

- **auth**: add login with passkeys (e4f5g6h)

### Bug Fixes

- crash on empty input (i7j8k9l)
```

## How it groups things

Commits are parsed as [conventional commits](https://www.conventionalcommits.org/). The type decides the section, in this order: Breaking Changes, Features, Bug Fixes, Performance, Refactoring, Documentation, Tests, Build, CI, Style, Chores, Reverts, Other Changes.

A commit counts as breaking if its subject has a `!` (`feat!: ...`) or its body has a `BREAKING CHANGE:` footer. Breaking commits get pulled into their own section at the top, even if they're also a `feat` or a `fix`.

Anything that isn't a conventional commit — a plain "updated some stuff" — still shows up, under Other Changes. I don't like tools that silently drop history.

## Usage

```
changemint [--repo PATH] [--since REF] [--until REF]
           [--output FILE] [--version VERSION] [--title TITLE]
           [--max-count N] [--stdout] [--dry-run] [--force]
```

Some things I reach for a lot:

```bash
# everything since the last tag, labelled as the next release
changemint --since v1.2.0 --version 1.3.0

# just look at it first — nothing gets written
changemint --dry-run

# print to stdout, pipe it wherever you want
changemint --stdout | head -40

# a range between two tags
changemint --since v1.1.0 --until v1.2.0 --output RELEASE-1.2.0.md
```

By default changemint refuses to overwrite an existing `CHANGELOG.md` — that file might have hand-written notes in it. Pass `--force` when you mean it.

## What it doesn't do (yet)

- It doesn't merge with an existing changelog, it writes a fresh one. If you keep a hand-edited changelog, generate to a different file and merge by hand, or use `--stdout` and paste.
- It doesn't read GitHub PR titles or issue numbers. The changelog comes purely from commit messages, so the quality of the output is exactly the quality of your commit messages.
- It only reads local git history. No network calls, no GitHub API.

## Install

Python 3.9+ and git. No other dependencies.

```bash
pip install git+https://github.com/codewithkrrish/changemint.git
```

Or clone it and run from source:

```bash
git clone https://github.com/codewithkrrish/changemint.git
cd changemint
pip install -e .
changemint --help
```

## Project structure

```
changemint/
├── src/changemint/
│   ├── cli.py       # argument parsing, exit codes, atomic file writes
│   ├── gitlog.py    # talking to git, nothing else
│   ├── commits.py   # parsing conventional-commit subjects
│   ├── render.py    # grouping commits and rendering Markdown
│   └── errors.py    # one exception type per failure, with exit codes
└── tests/
    ├── conftest.py  # builds throwaway git repos with known history
    ├── test_commits.py
    ├── test_render.py
    └── test_cli.py
```

## Tests

```bash
python -m pytest
```

The CLI tests build real temporary git repos (commits, tags and all) and run the tool against them — no mocking of git itself.

## License

MIT — see [LICENSE](LICENSE).

## Author

Krrish — [github.com/codewithkrrish](https://github.com/codewithkrrish)

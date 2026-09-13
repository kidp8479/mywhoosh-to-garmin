# Contributing

Engineering practice for this project is in
[`.claude/standards/engineering.md`](.claude/standards/engineering.md):
workflow, commits, the review and merge gate, testing, decisions,
code clarity, secrets, and how to work with the agent. Read that file,
not this one - it is the source, vendored from `agentic-lab` and kept in
sync there. This file exists so the standard is visible without opening
`.claude/` (e.g. browsing on GitHub without an agent), plus what is
specific to this fork.

## Fork-specific

Keep changes to this fork narrow and easy to carry forward: the upstream
is [marcelorodrigo/mywhoosh-to-garmin](https://github.com/marcelorodrigo/mywhoosh-to-garmin)
and is still active. A large local rewrite of code we didn't add
ourselves makes the next `git fetch upstream` painful to reconcile.

## Before committing

No `Makefile` here - run these directly (`engineering.md`'s `make
format` / `make lint` do not apply):

```sh
ruff format --check .
ruff check .
mypy .
pytest -q
```

CI runs the same set (`ci.yml`) plus a gitleaks secret scan
(`gitleaks.yml`) on every push and PR. Don't bypass them.

## Secrets

- This repo is **public** - never commit a real credential or token, even
  in a throwaway commit.
- The `sync.yml` workflow is disabled (Garmin 429s GitHub Actions IPs);
  its secrets, if still set, are dormant.

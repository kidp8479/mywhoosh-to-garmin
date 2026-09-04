# Contributing

Personal fork, run like a real project. The project-agnostic bar lives in
`~/42/WIP/CLAUDE.md` (Engineering standards); this file is the local
summary.

## Workflow

- One unit of work = one branch = one PR. No direct commits to `master`.
- Rebase the branch on `master` before opening or merging the PR; keep a
  linear history (merge commits only at the actual merge).
- Re-read your own diff before merging (`/code-review`).
- Keep changes to this fork narrow and easy to carry forward: the
  upstream is [marcelorodrigo/mywhoosh-to-garmin](https://github.com/marcelorodrigo/mywhoosh-to-garmin)
  and is still active. A large local rewrite of code we didn't add
  ourselves makes the next `git fetch upstream` painful to reconcile.

## Commits

- Conventional Commits: `type: summary` (`feat`, `fix`, `refactor`,
  `docs`, `build`, `ci`, `test`, `style`, `chore`).
- Atomic: one logical change per commit. The body explains *why* when the
  diff does not.
- Everything written into the repo is in English.

## Before committing

```sh
ruff format --check .
ruff check .
mypy .
pytest -q
```

CI (`.github/workflows/ci.yml`) runs the same set on every push and PR.
Don't bypass it.

## Code clarity

- Comment the *why*, not the *what*.
- Public surface (exported functions/classes, the CLI entry point) gets a
  doc comment; obvious private code does not.

## Secrets

- Local runs: `.env` only (git-ignored), `.env.example` kept current.
- Scheduled runs: GitHub Actions secrets
  (`MYWHOOSH_EMAIL`/`MYWHOOSH_PASSWORD`/`GARMIN_USERNAME`/`GARMIN_TOKEN_BASE64`),
  never a value in the workflow file itself. This repo is public - never
  commit a real credential or token, even in a throwaway commit.
- Treat a leaked secret as compromised: rotate it, don't just delete the
  line.

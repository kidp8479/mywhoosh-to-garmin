---
name: standards-audit
description: Bring an existing repo up to the engineering standards in .claude/standards/engineering.md - triage, plan, then a fixed set of atomic lots (git hygiene, secrets, CI, lint ratchet, slop, missing tests), each gated by /code-review, ending with reusable findings promoted to the template and the lab. Use when the user says "on met <repo> au standard", "applique le plan standards", "audit <repo>", or names a repo to standardise.
---

# standards-audit

`pr-review` is the ritual for a PR that is *in flight*. This is the
ritual for a repo that already exists and predates the standards: a
one-time pass that ends with the repo passing the same bar a fresh
`42-project-template` clone would.

Reference bar: `.claude/standards/engineering.md`, vendored into the
repo (and, on a 42 project, `.claude/standards/school-42.md` for the
subject-specific checklist). Do not restate either here - read them at
the start of every run, they are the source of truth and they move.

## 0. Triage first

Not every repo earns a full pass. Decide before planning:

- **Full pass**: a real project that will be run, shared, or defended.
- **Light pass**: a notebook / profile repo - git hygiene + secrets
  only, skip CI and tests.
- **Decide or delete**: a scratch pad with no git - either give it a
  structure or remove it. Ask the user, do not standardise it by
  default.

If a rollout tracker exists (`~/projects/hermes-lab/STANDARDS-ROLLOUT.md`),
it holds the per-repo triage verdict - update it as you go. No tracker:
skip this, the branch and its commits are the record.

## 0.5. Pre-flight - branch off the real default

Old repos drift. Before creating the working branch:

- `git remote set-head origin -a` then
  `git symbolic-ref refs/remotes/origin/HEAD` - use *that* as the base,
  do not assume `master` or `main`.
- If both `origin/master` and `origin/main` exist, they diverged (a
  GitHub rename never pulled locally). Confirm which one is live
  (`git log --oneline -1` on each, check the repo on GitHub), rename the
  stale local ref out of the way (`master` -> `master-stale`), and base
  the branch on the live one.
- Getting this wrong means every commit is reviewed against a stale tree
  and the branch has to be rebuilt. Cost of the check: 30 seconds.

## 1. Plan mode

Non-trivial by definition (3+ lots). Enter plan mode. Starting point:
the repo's own report in `~/projects/hermes-lab/reports/<repo>.md` if
one exists, plus a fresh look. Agree the lot list and the branch name
(`chore/engineering-standards`) before touching code.

## 2. The lots

One branch, one atomic commit per lot, in this order (skip what does not
apply). Each `type:` follows Conventional Commits.

| # | Lot | Typical commits |
|---|---|---|
| 1 | **git hygiene** | rename `gitignore`/`env.example` to dotfiles; `git rm -r --cached` generated output (`api-docs/`, `__pycache__/`, build artefacts); complete `.gitignore` from the template; drop empty dirs and `requirements.txt` when moving to `pyproject` |
| 2 | **secrets** | committed `.env.example` with placeholders + a comment per var; `gitleaks` scan of the working tree AND history; if a real secret is in history, tell the user to rotate it, do not just delete the line |
| 3 | **build / deps** | `pyproject.toml` (or equivalent) with pinned ranges; split runtime-only-on-target deps into an extra (e.g. `pi`) so CI installs a clean set; lazy-import the target-only modules so the package stays importable in CI |
| 4 | **CI** | `.github/workflows/ci.yml` (format check / lint / typecheck / test / build) + `gitleaks.yml`, both `on: [push to default, pull_request]`; `dependabot.yml` for the package ecosystem + github-actions |
| 5 | **lint ratchet** | adopt the lint config with the same complexity budget as `notes/eslint-hardening.md` / `anti-slop` (mccabe <= 10 for Python `C90`, the ESLint budget for JS/TS); `Makefile` with `format`/`lint`/`test`/`check`; `.githooks/pre-commit` + `make install` wiring |
| 6 | **slop** | delete boilerplate (NestJS `app.controller`/`app.service`, unused scaffolding); collapse duplicated blocks into one helper; kill dead constants and single-use wrappers; `print` -> `logging`; narrow `except Exception` that silently swallows to per-cycle log-and-continue; strip JSDoc/docstrings that paraphrase the identifier |
| 7 | **behaviour fixes surfaced by the scan** | anything the report flagged as a real bug (e.g. alert with no hysteresis spamming a webhook). One commit each, with a test. Confirm the intended behaviour with the user when the fix changes semantics. |
| 8 | **missing tests** | one test per public unit with no coverage (client method, monitor logic, script entry point). Inject collaborators so the loop logic is testable without hardware / network. |
| 9 | **docs** | `CONTRIBUTING.md` from the template (mirrors the standards); `README` / `SETUP` updated for the new env-driven config and `make` targets |

## 3. Gate each lot

- `/code-review` (or `mattpocock-skills:code-review` - needs the
  `mattpocock-skills` plugin installed globally, falls back to native
  `/code-review` if not) on the branch before merge, same as `pr-review`
  steps 6-7: verify each finding, delete-oriented triage first.
- Never `--no-verify`, never push to the default branch.
- CI green before merge. If the workflows only trigger on the default
  branch + PRs, CI stays unverified until the PR opens - open the PR to
  get the first green run, do not merge on faith.
- Rebase on the default branch, linear history.

## 4. Promote the reusable findings

The whole point of doing these in sequence is that lots 1-5 repeat across
repos. After the branch is reviewed, route what generalised:

| Finding | Goes to |
|---|---|
| A `.gitignore` line, a CI step, a `dependabot` group, a `Makefile` target, a pre-commit check that any project would want | PR on `git@github.com:kidp8479/42-project-template.git` |
| A new *rule* (stated as a standard, not a snippet) | `agentic-lab/standards/engineering.md` (promoted from there into every project's vendored copy) |
| A lint rule / complexity limit that proved its worth | `notes/eslint-hardening.md` (ratchet) and the `anti-slop` budget table |
| An agentic primitive (a hook, a subagent, a skill tweak) | its home in `agentic-lab` |

Record the promotion in the rollout tracker row so the next repo starts
from the improved template.

## 5. Close out

- Update the rollout tracker if one exists: status, branch/PR, what was
  promoted.
- If the repo has a session-handoff habit, follow `end-session`.

## Why a skill

- The lot order is the reusable part: doing git hygiene before CI before
  slop before tests is what keeps each commit atomic and each
  `/code-review` small. The user re-derives this order every repo
  otherwise.
- Step 4 (promote to the template / CLAUDE.md / lab) is the step that
  turns eleven one-off cleanups into one improving template, and it is
  the one that gets skipped under time pressure.
- Zero context cost until a repo audit triggers it.

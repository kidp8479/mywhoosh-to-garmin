---
name: pr-review
description: Full PR review ritual - check out the branch, verify a recent rebase did not break it, run /code-review, cross-check against Copilot and existing PR comments, verify every finding for real, triage worth-fixing vs informational, then draft and post the review comment. Use when the user says "review the branch", "regarde la PR", "on review la PR de X", or names a PR / branch in review.
---

# pr-review

The `CLAUDE.md` rule is "re-read the diff before merging, never push
straight to `main`". This skill is the *how*: the full ritual, the one
mined from ~90 past sessions on transcendence, generalised so it also
fits a solo PR on any project.

## 0. Scope

- **Team PR** (someone else's branch): full flow, ends with a review
  comment addressed to the author.
- **Solo PR** (your own branch): same flow, the "comment"
  becomes a self-review note on the PR and a go / no-go for merge.

## 1. Get on the branch

- `git fetch --all --prune`.
- Check out the PR branch in the right worktree (never review from a
  dirty tree). `gh pr checkout <n>` if unsure of the branch name.
- Note the base: `git log --oneline main..HEAD` and
  `git merge-base --is-ancestor main HEAD; echo $?`.

## 2. Verify a recent rebase did not break anything

Branches here get rebased onto `main` often. Before reviewing content:

- CI status: `gh pr checks <n>`. Red CI on mechanical grounds (lint,
  typecheck, build) stops the review - report that first.
- If the branch was rebased since the last review, diff what actually
  changed vs what should have: `git range-diff` against the pre-rebase
  SHA when you have it (session handoff doc / Slack log).
- Known conflict-prone spots on a NestJS project: Swagger decorators
  (`@ApiBearerAuth`, `@ApiTags`), guard order, `synchronize` vs
  migrations. Read those files after any rebase.

## 3. Schema review - judge the approach before the lines

Before any line-by-line review, step back to the goal (linked Linear
issue / subject constraint) and judge the approach itself:

- Does this approach actually meet the need?
- Was something simple made complex? Did an early choice spawn a pile of
  later patches?
- Do the auth / state / security concerns come from the architecture
  itself, or just from local code?
- Could the problem be fixed locally, or does a different approach
  remove this class of problem at the root? Is the migration cost worth
  it?

End with one explicit verdict: **keep the approach / adjust it / replace
it / not enough info**. Only go on to the line-level review if it holds.
Do not propose code fixes before this verdict.

## 4. Run the code review

- `/code-review` (or `mattpocock-skills:code-review` for the two-axis
  Standards + Spec split when there is a linked Linear issue - needs the
  `mattpocock-skills` plugin installed globally, falls back to native
  `/code-review` if not).
- Let it fan out. Do not accept its findings yet.

## 5. Cross-check the code review - drop what was already raised

Before reporting anything, subtract findings that already exist:

- Copilot inline comments:
  `gh api repos/{owner}/{repo}/pulls/<n>/comments --paginate`.
- Human review comments: `gh pr view <n> --comments`.
- Anything Copilot or a teammate already flagged: do not re-report it.
  Note "already raised by Copilot" instead.

## 6. Verify every surviving finding for real

A `/code-review` finding is a hypothesis. Confirm or refute each one:

- Re-read the actual source yourself (not just the agent's quote).
- If it is observable in the running app, reproduce it in the browser
  (spawn the `browser-e2e` agent for anything that needs a login +
  click-through). Report the repro steps.
- Refute openly the ones that do not hold. Past reviews killed several
  "races" and "divergences" that were not real on inspection.

## 7. Triage

First pass, delete-oriented: read the diff as if the job is to remove as
much of it as possible without breaking the requested behavior. Flag and
propose the smaller version for:

- an abstraction with a single real use
- a capability that already exists elsewhere, now duplicated
- speculative extensibility ("might need it later")
- an unnecessary new dependency
- files changed outside the causal path of the request
- comments / types / wrappers that only exist to explain complexity the
  change itself introduced

Optimize for the least new structure that makes the behavior true, not
for fewer lines.

Then split all confirmed findings (yours + the survivors from step 6):

- **Worth fixing before merge**: correctness bugs, security (any
  ownership / auth gap), console errors / warnings, the delete-oriented
  findings that are cheap now. On a 42 subject, check `CLAUDE.md` and
  `.claude/standards/school-42.md` for which of these are eliminatory.
- **Informational, do not touch now**: larger refactors and duplication,
  especially close to a deadline or when the file is shared with other
  in-flight work. State it as context, request no action.

## 8. Draft the comment

Constraints (from the user, non-negotiable):

- English, concise, factual, kind.
- The author is the expert on their code - "you decide if any of this is
  worth it".
- Do **not** offer to push fixes.
- Lead with what was tested (browser steps, e2e), then the short list of
  worth-fixing findings, then one purely informational paragraph if any.
- No em dash: spaced hyphen, colon, or parentheses.

Show the draft. Wait for the user's OK.

## 9. Post

- Team PR: `gh pr review <n> --comment --body-file <draft>`.
- Solo PR: post as an issue comment (`gh pr comment <n> --body-file`)
  and give the user a merge go / no-go.

## Why a skill

- The trigger words ("regarde la PR", "review la branche") are exactly
  how the user opens these sessions.
- The context cost is zero until triggered - none of this belongs in
  `CLAUDE.md`.
- Steps 5 and 6 (cross-check Copilot, verify every finding for real) are
  the ones the user re-explains every single time.

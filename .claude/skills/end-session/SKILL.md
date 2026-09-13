---
name: end-session
description: Close a project work session - summarize what moved, post the recap to the project's Slack daily-log channel, and update the Linear Session Handoff doc so the next machine can resume. Use when the user says "on s'arrete la", "log la session", "fin de session", "fais le recap".
---

# end-session

`.claude/standards/engineering.md` (Session handoff): post a recap to the
project's daily-log channel and keep its tracker "Session Handoff" doc
current (Linear on the current projects) - these two artifacts are what
survive between the home and school machines. This skill produces both.

(`log-session` in this repo is the stripped learning example. This is the
real one.)

## Steps

1. **Identify the project** from cwd + `CLAUDE.md`.
2. **Collect**: `git log --oneline` since the last session (use the last
   recap's date / SHA), `git status --porcelain`, merged PRs
   (`gh pr list --state merged --limit 5`), any new `docs/adr/` file.
3. **Draft the recap** (English, no em dash):
   - **Done**: 2 to 5 bullets, what actually moved
   - **Decisions**: any structural choice - if one was made and there is
     no matching `docs/adr/NNNN-*.md`, flag that an ADR is owed
   - **Blocked / to decide**: open questions, undecided items
   - **Next**: the one concrete next step
4. Show the draft. On OK:
   - Post to `#<project>-daily-log` (slack MCP).
   - Update the Linear "Session Handoff" doc (replace the "current state"
     / "next steps" sections, keep the history).
5. Do **not** commit code. Do not push.

## Why a skill

- The recap + handoff update is mandated by `CLAUDE.md` but never
  proceduralised - it gets skipped or done inconsistently.
- Fixed source list (git, PRs, ADRs) so the recap is complete.
- Ends the session in a state the next machine can pick up cold via
  `resume-session`.

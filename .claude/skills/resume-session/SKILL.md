---
name: resume-session
description: Reconstruct the state of a project at the start of a work session from the Slack daily-log, the Linear Session Handoff doc, and git, then list the concrete next steps. Use when the user says "on reprend", "nouvelle session", "day N", "lis les docs de session", "mets-toi a jour".
---

# resume-session

`.claude/standards/engineering.md` (Session handoff): context does not
carry between machines (home Docker / school Podman) - the daily-log
recap and the tracker's handoff doc do (Slack + Linear on the current
projects). This skill reads them back.

## Steps

1. **Identify the project** from the cwd (`Hypertube/`, `ravito/`, etc.) and its
   `CLAUDE.md`.
2. **Slack**: read the last few posts in `#<project>-daily-log`
   (slack MCP / `slack:summarize-channel`).
3. **Linear**: fetch the project's "Session Handoff" doc if it exists,
   plus open issues and their state (`mcp__linear__list_issues`,
   filtered to this project, not Done).
4. **Repo signals**:
   - `git fetch --all --prune`, then branch status vs `main`
     (`git log --oneline main..<branch>`, ahead / behind).
   - `gh pr list --state open` - anything waiting on review or merge.
   - `docs/reviews/` and `docs/defense/backlog.md` for open findings.
   - Unpushed work: `git log <branch> ^origin/<branch>`.
5. **Output** a short brief:
   - Where we left off (1 to 3 lines)
   - Open threads (PRs, review findings, undecided items from the
     project `CLAUDE.md` "pas encore decide" section)
   - Proposed next step
6. Stop. Let the user confirm or redirect before doing any work.

## Why a skill

- Replaces the cold "on reprend, day 4" the user types every session.
- Pulls from three sources (Slack, Linear, git) in a fixed order so
  nothing is missed.
- Read-only by contract: it briefs, it does not start coding.

# Engineering standards

Project-agnostic. Applied the same way on every project, 42 or personal.
Personal defaults (language, writing style, attribution) are in
`~/.claude/CLAUDE.md`. 42-subject rules are in `school-42.md` and are
instantiated per project in the repo's own `CLAUDE.md`.

## Workflow: one issue, one branch, one PR

- Work is tracked as issues (Linear on the current projects). One issue =
  one branch = one PR. When the tracker has a GitHub integration, the
  issue status moves automatically on branch / PR / merge.
- Comment on the issue at meaningful progress points, not only at the end.
- If the default branch moved, **rebase** the feature branch onto it
  before opening or merging the PR. Never merge the default branch into a
  feature branch. Merge commits happen only when a PR actually merges.

## Commits

- Atomic: one logical change per commit.
- Conventional Commits: `type: summary` (`feat`, `fix`, `chore`, `docs`,
  `ci`, `refactor`, `test`, `build`, `style`). Body explains *why* when
  the diff does not.
- Tied to an issue: `type(<PREFIX>-N): summary`.

## Local gate before committing

```sh
make format
make lint
# and, where the project has them: make typecheck, make test
```

A pre-commit hook (`.githooks/pre-commit`, enabled by `make install`)
runs the check variants and blocks the commit on failure. Fix and
re-commit. **Never** `--no-verify` unless the user explicitly decides it.

## Review and merge gate

Even solo:

- Re-read the full diff before merging (`/code-review`). Never push
  straight to the default branch.
- CI green before merge: format, lint, typecheck, test, build, secret
  scan (`gitleaks`). Never bypass CI.
- Each new unit of behaviour (endpoint, service, script, manifest) ships
  with at least one test before it merges (see Testing).

**Make the PR reviewable.** The description carries:

- what changed in plain terms or pseudocode, not a restatement of the
  diff
- a mermaid diagram when the change touches a flow, a state machine, or
  more than two components
- evidence, not claims: the test / lint / typecheck output, and the
  manual or e2e steps actually run (browser steps, plus screenshots
  attached to the PR or the tracker issue for a UI change)

## Testing

- Tests sit at the boundary that matters (HTTP route, service contract,
  pure function input to output), not on implementation detail.
- End-to-end and browser tests use **Playwright**: auth flows
  (register / login / reset / logout) and any user-facing flow get one
  before merge. The `browser-e2e` subagent also drives Playwright at
  review time (seeded login, click-through, screenshots, console check).
- Keep the suite honest: prune tests that only re-assert the source or
  lock in implementation detail (`test-audit` skill), then simplify the
  code they were propping open.

## Pull request template

`.github/pull_request_template.md`, identical across projects (only the
`<PREFIX>` and the exact `make` target names change):

```markdown
## What does this PR do?


## Linked issue

<!-- Closes <PREFIX>-N -->

## How to test it?


## Checklist

- [ ] description explains what changed (plain terms or pseudocode), not a restatement of the diff
- [ ] mermaid diagram included if the change touches a flow, a state machine, or 3+ components
- [ ] builds without errors or warnings
- [ ] format / lint / typecheck / test / build green
- [ ] tested manually (browser / API calls); screenshots on the PR or tracker issue for a UI change
- [ ] no regressions on existing features
- [ ] new behaviour ships with at least one test
- [ ] auth / user-data changes: `web-security-review` run, auth **and** ownership checked
- [ ] ADR added under `docs/adr/` if this is a structural decision
- [ ] rebased on latest `main` (resolving conflicts before opening the PR is the opener's responsibility)
- [ ] no sensitive data or secrets committed
```

## Planning and lessons

- Non-trivial task (3+ steps, or an architectural choice): agree a plan
  before touching code (plan mode). If the work goes sideways, stop and
  re-plan rather than pushing on.
- After a course correction, write the lesson down: a `feedback` memory
  for a cross-project habit, `docs/lessons.md` for a project-specific one.
- A deliberate tradeoff or accepted tech debt (not a bug to fix) goes in
  `docs/known-limitations.md` with why it is not fixed and what would
  resolve it. Check it before "fixing" one by surprise.

## Decisions (ADRs)

Record a structural decision (auth strategy, hashing algorithm,
transport, data model) as a short `docs/adr/NNNN-title.md`: context /
decision / consequences. A commit message or a chat thread is not a
durable record.

## Diagrams

Architecture and flow diagrams live in `docs/diagrams/`:
`<name>.excalidraw` is the source of truth, `<name>.png` the render,
`<name>.py` (optional) regenerates it via the `excalidraw-diagrams`
skill. Mirror each in the project's docs space, one document per domain
(a Linear document per domain on the current projects): embed the PNG, a
short walk-through, link it from that domain's issues. Refresh the
diagram and the doc when the feature that changed the flow merges.

## Code clarity

- Comment the *why*, not the *what*. A comment that restates the
  identifier name earns nothing.
- Public surface (exported classes/methods, HTTP routes, externally
  invoked scripts) gets a doc comment; obvious private code does not.
- Everything written into the repo is English (see `~/.claude/CLAUDE.md`),
  inline comments included. Check none slipped through before merging.

## Slop control

Draconian complexity limits are a bad fit for a human author but a good
automatic net against an agent that over-produces. Four layers, in the
order they fire:

- **teach**: the `anti-slop` skill, in context before the agent writes.
- **check**: `lint-feedback` hook, eslint on the file just written.
- **gate**: the ESLint / ruff complexity ratchet at commit and CI
  (`--max-warnings <baseline>`, monotone: can only go down).
- **review**: `diff-auditor` subagent and the `pr-review` skill.

Complexity budget (same intent for JS/TS and Python): branches per
function <= 10, nesting <= 4, params <= 4, function <= 80 lines
(components 120), file <= 300 lines. Over budget: split, do not disable
the rule.

The most common agent slop is not copy-paste but **semantic
duplication**: logic that already exists in the codebase, reimplemented
differently. Grep for the existing helper before writing one. `slopo`
(embedding-based near-duplicate detector) is being trialled as an
automated check for this at PR time.

## Secrets

- `.env` only (git-ignored). Never in code, git history, Linear, or
  Slack. Keep `.env.example` current with placeholder values.
- A leaked secret is compromised: rotate it, do not just delete the line.
- `gitleaks` runs in CI on every push and PR.

## Security (web projects)

Before merging anything touching authentication or user data, run the
`web-security-review` skill. The skill is the source of truth; this is a
summary to keep in sync with it:

- **Passwords/tokens**: argon2id hashing; reset/verification tokens
  CSPRNG-generated, single-use, short-lived, hashed at rest.
- **Authorization**: every mutating route on a user resource checks auth
  **and** ownership, `403` otherwise, never a silent pass. CRUD scaffolds
  ship with no guards: lock every generated route before merge. Never
  trust a client-supplied role or ID for an authz decision. No IDOR.
- **Enumeration / brute-force**: login / register / reset return
  identical responses (text and timing); auth endpoints rate-limited.
- **Input validation**: strict server-side, field whitelist, unknown
  fields rejected. Uploads: MIME checked, size-capped, name sanitized,
  stored outside the webroot.
- **Injection**: parameterized queries / ORM only; output escaped by
  default; security headers set (CSP, `X-Content-Type-Options`, frame
  options).
- **Session/transport**: session cookies `HttpOnly` + `Secure` +
  `SameSite`; CORS restricted to the expected origin; logout invalidates
  server-side.

## Containers: dev bind mounts

- Never let a dev container write directly onto a bind mount. Put
  anything it generates (`node_modules`, build output, lockfiles) into a
  **named volume**: both Docker and rootless Podman chown named volumes
  to the image user, unlike bind mounts. Under rootless Podman the host
  user maps to container root, so a non-root image user cannot write into
  a bind-mounted `/app` at all.
- On an SELinux-enforcing host (school lab), suffix host bind mounts with
  `:Z`. Docker on non-SELinux hosts ignores the flag, so it is safe
  across both runtimes.
- Run format / lint / typecheck host-side (`make ...`), which is what the
  pre-commit hook does anyway. Tool configs outside the bind mount are
  invisible from inside the container.

## Tools

The toolchain varies per project; on the current ones:

- **Issue tracker**: Linear (issues, milestones, priorities; labels group
  issues by technical domain).
- **GitHub**: source of truth for code, PRs, review.
- **Slack**: day-to-day comms; a `#<project>-daily-log` channel is a
  running journal (done / blocked each day) to keep context between work
  sessions and machines. Native integrations post GitHub and tracker
  activity into dedicated channels.

## Session handoff

Context does not carry over between machines. What does: at the end of a
session, post a recap to the project's `#<project>-daily-log` channel and
keep its "Session Handoff" tracker doc current (if the project has one);
read both back at the start of the next session. See the `end-session` /
`resume-session` skills.

## Working with the agent

Default (42 projects):

- Tooling / infra / CI setup: the agent can drive autonomously.
- Core project code: smaller steps, explain the *why*, let the user drive
  and react rather than accepting a large unattended scaffold.

Personal projects: when the user asks for it, the agent can run a task
end to end on its own and surface only the friction points (decisions,
tradeoffs, anything ambiguous) instead of every step.

---
name: anti-slop
description: Constraints to apply BEFORE writing or editing code, so the lint gate and PR review find less to reject. The "teach" half of agent slop control - the ESLint ratchet (notes/eslint-hardening.md) is the "checker" half. Use when about to write a new module, a new endpoint, a service, or a non-trivial refactor.
---

# anti-slop

`notes/eslint-hardening.md` blocks slop at commit / CI time. This skill
blocks it earlier: it is the checklist to hold in context while writing,
so the code clears `lint:check --max-warnings <baseline>` on the first
run instead of after a fix pass.

Same rationale as the lint note: draconian limits are a bad fit for a
human author but a good automatic net against an agent that over-produces.

## Before writing

1. **Reuse before you write.** Grep for an existing function / hook /
   util that already does this. Agents re-implement `formatDate`,
   `isUuid`, an axios wrapper, a guard, that already exist. Import it.
2. **No speculative abstraction.** No interface, factory, generic, config
   object, or "…Manager" / "…Service" wrapper unless there are two real
   call sites now. One caller = inline it.
3. **Model the type.** No `any` to silence the compiler. If the shape is
   unknown, write the interface. `@typescript-eslint/no-explicit-any` is
   the single most common agent tell.
4. **Match the neighbours.** Same error handling, same naming, same file
   layout as the sibling files in that directory. Do not introduce a
   second pattern for a solved problem.

## While writing - the budget

Stay inside the lint ceilings so nothing regresses:

| Limit | Ceiling |
|---|---|
| branches per function (`complexity`) | 10 |
| nested blocks (`max-depth`) | 4 |
| callback nesting | 3 |
| params | 4 (past that, one object) |
| lines per function | 80 (components 120) |
| lines per file | 300 |
| cognitive complexity | 15 |

Over budget = split the function or the file, do not disable the rule.

## Before saying it is done

- No copy-pasted block (`sonarjs/no-identical-functions`): extract or
  parametrise.
- No repeated string literal 4+ times: named constant.
- No dead code: an export with no importer, a param never read, a file
  nothing references. If you added it "for later", delete it.
- No stray `console.log` / `print`, no `TODO` without a linked issue.
- `evidence over claims`: show the `lint:check` and typecheck output, do
  not assert it passes.

## Why a skill

- Zero context cost until a real coding task triggers it - none of this
  belongs in `CLAUDE.md`.
- Pairs with `diff-auditor` (post-hoc audit) and the ESLint ratchet
  (commit gate): teach, then check, then review.

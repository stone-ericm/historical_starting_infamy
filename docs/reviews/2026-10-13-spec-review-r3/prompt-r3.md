# Historical Starting Infamy — design spec review, round 3 (tag HSI-R3), final round

Round 2 (`/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r2/codex-findings-r2.md`, verdict REVISE, N1–N13) has been answered by spec v3. This is the last review round under the project's cap; after it the owner decides. Review v3 adversarially; assume defects remain, including new ones introduced by v3.

## Hard rules (unchanged)
- Do NOT read `~/.codex/memories/` or any memory file; disclose any injected memory in section 0 and do not use it.
- Read-only. The only file you may create or modify is the deliverable named below.
- No `herdr` commands, no other panes or agents, no network, no git mutations.
- Allowed commands: cat, head, tail, sed -n, grep, rg, ls, find, wc, diff, shasum, python3 for read-only computation, git log/show/diff/status inside the mod repo.
- One command per tool call.

## Inputs (frozen for this round)
- Spec v3: `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` (repo HEAD 0c9b379). v2 is `git show f6fae84:docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md`.
- Your round-2 findings: `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r2/codex-findings-r2.md`.
- Vanilla 1.14.5 scripts, read-only: `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`.

## What to do
1. Disposition of N1–N13: RESOLVED / BOUNDED (acceptable or not, with the minimum change if not) / NOT ADDRESSED / REGRESSED, each with the v3 section and line.
2. Attack what v3 introduced: the `A_r` amount contract and the recurrence in §7; the canonical same-day order; the ordering registry and the four fixtures in §6 (is the fixture set now sufficient to identify the order, and is "refuse on two fitting classes" well defined?); the `DIAG` record and oracle A in diagnostic mode (can the probe actually evaluate those predicates and materialize `state_infamy_value` with the holder as root inside `on_monthly_pulse_country`?); the holder = creator restriction; whole-slice-only components; pending and post-horizon resolutions; the manifest contract; the tolerance and empty-table rules in §9.
3. Anything that would make the mod fail to load, fail to fire, or produce wrong numbers.
4. Be explicit about what remains a judgment for the owner rather than a defect.

## Deliverable
Write `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r3/codex-findings-r3.md` with:
0. Disclosure (injected memory; model/effort if visible).
1. Round-2 disposition table N1–N13.
2. New findings, numbered P1…, each with severity (BLOCKER / MAJOR / MINOR), v3 section, claim, evidence, proposed fix.
3. Owner decisions: items that are choices, not defects, in plain language.
4. Verdict: APPROVE / REVISE / REJECT with a one-sentence reason.

When the file is complete, run `shasum -a 256` on it and print, as your final on-screen message, the line `HSI-R3-<first 8 hex of the digest>` on its own line, then exactly `DONE` on the next line. (Template: `HSI-R3-xxxxxxxx`.)

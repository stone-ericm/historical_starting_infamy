# Historical Starting Infamy — design spec review, round 2 (tag HSI-R2)

Round 1 (your file `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r1/codex-findings-r1.md`, verdict REVISE, 17 findings) has been answered by a revised spec, v2. Review v2 as adversarially as round 1. Assume v2 still contains defects, including new ones introduced by the revision.

## Hard rules (unchanged)
- Do NOT read `~/.codex/memories/` or any memory file; disclose any injected memory in section 0 and do not use it.
- Read-only. The only file you may create or modify is the deliverable named below.
- No `herdr` commands, no other panes or agents, no network, no git mutations.
- Allowed commands: cat, head, tail, sed -n, grep, rg, ls, find, wc, diff, shasum, python3 for read-only computation, git log/show/diff/status inside the mod repo.
- One command per tool call.

## Inputs (frozen for this round)
- Spec v2: `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` (repo HEAD f6fae84). `git show 202905f:docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` is v1 if you want the diff.
- Your round-1 findings: `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r1/codex-findings-r1.md`.
- Vanilla 1.14.5 scripts, read-only: `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/` (same relevant files as round 1).

## What to do
1. For each round-1 finding F1–F17, state one of: RESOLVED (v2 fixes it), BOUNDED (v2 adopts a narrower version and declares the approximation; say whether the bound is acceptable and, if not, what minimum change would make it so), NOT ADDRESSED, or REGRESSED. Cite the v2 section and line.
2. Attack what v2 introduced:
   - §7 timeline semantics: one balance per country, continuous linear decay between dated events, clamp [0,1000] after each event, refunds as fractions of the goal's accrued amount, victim reductions. Any ordering or sign error? Does scaling accruals, refunds and reductions by the rule multiplier before decay reproduce what the engine would do under that rule?
   - §7 five tables + §8 selection by `has_game_rule` with Standard as the `else` branch, scalar `change_infamy` lines under `c:TAG ?= { }` inside a scripted effect called from a rootless on_action. Anything invalid or fragile?
   - §6 probe: rootless start records from both start hooks registered additively; country-rooted monthly records from `on_monthly_pulse_country` guarded to the ledger's countries; `SIV` records of `state_infamy_value` with root = the credited country; the three oracle tooltips under the Very Low rule; the 2 % stabilization rule. Anything that cannot work, or that measures the wrong thing?
   - §5 ledger: three CSVs, components keyed by region plus 1836 owner slices with shares summed across slices; separate credited / victim identities; predicates for the subject blocks. What still cannot be expressed that the formula needs? Is the slice-summing counterfactual coherent with the caps?
   - §9 verification: oracle checks A and B, structural save parsing, failure-direction tests, lifecycle checks. Which false greens remain?
   - §3 hypothesis H1 (ordering) and the plan to fix it from tooltip transcripts: is the proposed set of three tooltips sufficient to determine the order, or can two orders fit the same three readings?
3. Anything else that would make the mod fail to load, fail to fire, or produce wrong numbers.

## Deliverable
Write `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r2/codex-findings-r2.md` with:
0. Disclosure (injected memory; model/effort if visible).
1. Round-1 disposition table: F1–F17 with status and v2 citation.
2. New findings, numbered N1…, each with severity (BLOCKER / MAJOR / MINOR), v2 section, claim, evidence (file:line or quoted script), proposed fix.
3. Unresolved disagreements you want surfaced to the owner, if any, in plain language.
4. Verdict: APPROVE / REVISE / REJECT with a one-sentence reason.

When the file is complete, run `shasum -a 256` on it and print, as your final on-screen message, the line `HSI-R2-<first 8 hex of the digest>` on its own line, then exactly `DONE` on the next line. (Template: `HSI-R2-xxxxxxxx`.)

# Historical Starting Infamy — final whole-branch review before the merge (tag HSI-F1)

You are a fresh reviewer. A Victoria 3 (1.14.5, Mac Steam) mod was built on branch `build/v1` of
`/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy` and is about to be merged to `main`
and used in play. Assume defects exist. Find what is wrong, overstated or unsupported.

## Hard rules
- Do NOT read `~/.codex/memories/` or any memory file; disclose any injected memory summary in section 0 and do not use it.
- Read-only. The only file you may create or modify is the deliverable named below.
- No `herdr` commands, no other panes or agents, no network, no git mutations. Do not launch the game. Do not touch anything under `~/Documents/Paradox Interactive/Victoria 3/` outside this repository.
- Allowed commands: cat, head, tail, sed -n, grep, rg, ls, find, wc, diff, shasum, python3 for read-only computation, `git log/show/diff/status` inside the repo, the suite exactly as `cd tools && uvx pytest -q` (if it cannot resolve its dependency, say so; do not substitute another runner). Scratch files under `/private/tmp/hsi-codex-f1/` only. Do not run the shell scripts under `research/measurement/` outside the suite.
- One command per tool call.

## Part 1 — blind (do this before reading any file under `docs/reviews/` or `.codex-review/`)
The whole branch: `git log --oneline main..build/v1`, `git diff main..build/v1 --stat`. Read `CLAUDE.md`, `ARCHITECTURE.md`, the spec `docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` and its v4 addendum `docs/superpowers/specs/2026-10-14-v4-simplification-addendum.md` (the addendum wins where they differ). Then review, in this priority:
1. **What ships**: `.metadata/metadata.json`, `common/on_actions/zz_hsi_on_actions.txt`, `common/scripted_effects/zz_hsi_effects.txt`, `README.md`. Will it load, fire exactly once per campaign after the lobby, respect the Infamy Generation game rule with Standard as the `else` branch, apply the table values, and never touch Bolivia? Check every construct against the vanilla files under `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/` (read-only).
2. **Are the numbers what the game's own formula gives?** `tools/hsi/constants.py`, `formula.py`, `timeline.py`, `generate.py` against `common/script_values/00_infamy_values.txt`, `common/defines/00_defines.txt`, `common/country_ranks/00_country_ranks.txt`, `common/war_goal_types/*.txt`; the stage order and the rank block against the eleven captured tooltips in `research/measurement/2026-10-14-run-20261014-142803-66370/` (`attempt-notes.md` transcribes them; the images are `.jpg`); the day-one snapshot and oracle A against `research/measurement/2026-10-14-run-20261014-150956-73604/`; the ledger (`research/acts.csv`, `goals.csv`, `goal_states.csv`, `sources.md`, `not_representable.md`) for mapping errors a reader of the sources would object to; `research/derivation.csv` and `research/tables.json` for arithmetic you can recompute. Say explicitly which parts are measured, which are judgments, and which are unverified.
3. **The README**: every sentence a player would rely on; anything overstated.
4. **False greens** in `tools/tests/`: wrong implementations the suite would not catch, as regression cases.
5. `research/acceptance/2026-10-14-run-20261014-153134-83398/acceptance-notes.md`: is the acceptance claim supported by the evidence there, and what is missing?

## Part 2 — after Part 1 is written down
Read `docs/reviews/2026-10-14-code-review-r1/`, `-r2/`, `-r3/` (three earlier rounds on the pre-boot code and their triage files) and check that nothing those rounds found is still open in the shipped state, and whether their deferred items (B5–B7, L2, L3, L5, L6) are moot under the v4 addendum or still owed.

## Deliverable
Write `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/final-review/codex-findings-f1.md` with:
0. Disclosure (injected memory; model/effort if visible; the commit you reviewed; what you ran and its result).
1. Part 1 findings F1…, each with severity (BLOCKER = wrong in play or wrong numbers / MAJOR / MINOR), repo `file:line`, claim, evidence (vanilla `file:line`, a transcribed tooltip, a recomputation), proposed fix, cheap check.
2. README statements that are overstated, with the honest wording.
3. False greens as regression cases.
4. Part 2: earlier-round items still open, and the deferred items' status under the addendum.
5. Owner decisions (choices, not defects), in plain language.
6. Verdict: `SAFE TO MERGE` or `FIX BEFORE MERGE`, one sentence, then the ordered list of what must change first (empty if none).

When the file is complete, run `shasum -a 256` on it and print, as your final on-screen message, the line `HSI-F1-<first 8 hex of the digest>` on its own line, then exactly `DONE` on the next line. (Template: `HSI-F1-xxxxxxxx`.)

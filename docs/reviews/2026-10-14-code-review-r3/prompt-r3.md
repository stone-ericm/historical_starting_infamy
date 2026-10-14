# Historical Starting Infamy — pre-boot code review, round 3 (tag HSI-C3), final pre-boot round

Round 2 (`/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/code-review-r2/codex-findings-r2.md`, verdict FIX BEFORE BOOT, N1–N9) has been applied. This is the last pre-boot round under the project's cap; after it the owner boots or the owner decides. Verify the fixes; assume defects remain, including new ones introduced by them. Keep the scope to what can waste the boot or damage the playset: the deferred items (B5–B7, L2, L3, L5, L6) are not reopened here.

## Hard rules (unchanged)
- Do NOT read `~/.codex/memories/` or any memory file; disclose any injected memory summary in section 0 and do not use it.
- Read-only. The only file you may create or modify is the deliverable named below.
- No `herdr` commands, no other panes or agents, no network, no git mutations. Do not launch the game. Do not touch anything under `~/Documents/Paradox Interactive/Victoria 3/` outside this repo.
- Allowed commands: cat, head, tail, sed -n, grep, rg, ls, find, wc, diff, shasum, python3 for read-only computation, `git log/show/diff/status` inside the repo, the audit exactly as `python3 research/scripts/capture_audit.py "/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game"` (no `--write-config`), and the suite as `cd tools && uvx pytest -q` (it needs no network once cached; if it fails to resolve, say so and do not substitute another runner). Scratch files under `/private/tmp/hsi-codex-r3/` only. Do not run the boot scripts outside the suite.
- One command per tool call.

## Inputs (frozen for this round)
- Repo, branch `build/v1`; the round-2 fixes are `git diff b503dd0..HEAD` (two commits: the fixes, then the archived reviews). Read the diff first, then `.codex-review/code-review-r2/triage-r2.md`.
- Vanilla 1.14.5 scripts, read-only, as before.

## What to do
1. Disposition of N1–N9 as applied: FIXED / PARTIAL / NOT FIXED / REGRESSED, with repo `file:line`, and for each PARTIAL the minimum change.
2. Re-run your round-2 counterexamples against the new `check_receipt` (the mutation table) and the new scripts' control flow; report any that still pass or any correct boot the new checks would now wrongly refuse (a legitimate per-root firing date a few days after the sampler must pass; the configured Very Low rule read in the after-lobby hook must pass; a different reading in `on_game_started` alone must pass as an observation).
3. The regenerated probe (`research/probe/`, 42 fixture slices, 5,732 lines): the new `unrec_mult` operand's scope and moment; the fixture-slice set versus every candidate's priced slices; anything that changed the log-line envelope.
4. Anything in `research/measurement/PROCEDURE.md` and `capture-plan.md` that would fail at the keyboard or lose an observation the deferred fixes need.

## Deliverable
Write `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/code-review-r3/codex-findings-r3.md` with:
0. Disclosure (injected memory; model/effort if visible; the commit you reviewed; what you ran and its result).
1. Disposition table N1–N9.
2. New findings P1…, each with severity (BLOCKER = the boot would be wasted or the playset damaged / MAJOR / MINOR), repo `file:line`, claim, evidence, proposed fix, cheap check.
3. Owner decisions (choices, not defects), in plain language.
4. Verdict: `SAFE TO BOOT` or `FIX BEFORE BOOT`, one sentence, then the ordered list of what must change before the boot (empty if none).

When the file is complete, run `shasum -a 256` on it and print, as your final on-screen message, the line `HSI-C3-<first 8 hex of the digest>` on its own line, then exactly `DONE` on the next line. (Template: `HSI-C3-xxxxxxxx`.)

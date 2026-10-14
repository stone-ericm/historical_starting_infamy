# Historical Starting Infamy — pre-boot code review, round 2 (tag HSI-C2)

Round 1 (`/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/code-review-r1/codex-findings-r1.md`, verdict FIX BEFORE BOOT) has been triaged and partly applied. This round verifies the applied fixes and the new capture plan before the owner's one-shot boot. Assume defects remain, including new ones introduced by the fixes.

## Hard rules (unchanged from round 1)
- Do NOT read `~/.codex/memories/` or any memory file; disclose any injected memory summary in section 0 and do not use it.
- Read-only. The only file you may create or modify is the deliverable named below.
- No `herdr` commands, no other panes or agents, no network, no git mutations. Do not launch the game. Do not touch anything under `~/Documents/Paradox Interactive/Victoria 3/` outside this repo.
- Allowed commands: cat, head, tail, sed -n, grep, rg, ls, find, wc, diff, shasum, python3 for read-only computation, `git log/show/diff/status` inside the repo, the suite exactly as `cd tools && uvx pytest -q`, and the audit exactly as `python3 research/scripts/capture_audit.py "/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game"` (no `--write-config`). Scratch files under `/private/tmp/hsi-codex-r2/` only. The boot-script tests use a fake home and a stub binary; do not run the scripts themselves outside that suite.
- One command per tool call.

## Inputs (frozen for this round)
- Repo as before, branch `build/v1`; the fixes are the commits after `dfed034`: `git log --oneline dfed034..HEAD` and `git diff dfed034..HEAD`.
- The triage of your round-1 findings, with what was fixed, what was deferred until after the boot and one disagreement: `.codex-review/code-review-r1/triage-r1.md` (read it after the diff, not before).
- Vanilla 1.14.5 scripts, read-only, as before.

## What to do
1. Disposition of B1–B10, F1, L1–L7 as applied: FIXED / PARTIAL / NOT FIXED / REGRESSED, each with repo `file:line`. Where the triage deferred an item until after the boot, say whether you accept that the boot's evidence (screenshots of the full breakdown and the state-level tooltip, plus the probe's tick-0 and monthly records for every candidate slice) is sufficient for the deferred fix, or name what the boot must additionally capture.
2. The new capture plan (`research/measurement/capture-plan.json`, `capture-plan.md`, `research/scripts/capture_audit.py`): check every candidate's full eligibility chain against the vanilla files again, including `requires_interest`, subject and overlord rules, truces (`common/history/diplomacy/00_truces.txt`), decentralized targets, and whatever else code-side validation the files document; check the audit's arithmetic (standing, factors, severity, clamps) and its static proxies; say which candidate is most at risk and why.
3. The regenerated probe (`research/probe/`, 5,552 lines, 32 fixture slices): every new construct valid in its scope; the DIAG record's added operands evaluated in the right scope and at the right moment (same block as `siv`); the monthly guard; the fixture holder's DIAG loop; log-line format unchanged for the extractor.
4. `tools/hsi/measurement.py` receipt (`expected_receipt`, `check_receipt`, `monthly_snapshots`, the `check` CLI) and `generate.main`'s use of them: false greens, wrong refusals, anything that would reject a correct boot.
5. `research/measurement/boot_probe.sh`, `restore_playset.sh`, `PROCEDURE.md`, `tools/tests/test_boot_scripts.py`: anything that can still leave the owner's playset wrong, lose evidence, or make the procedure fail at the keyboard.
6. The small fixes (ledger invariant, `emitted_value`, validator, lookup helper) and their tests.

## Deliverable
Write `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/code-review-r2/codex-findings-r2.md` with:
0. Disclosure (injected memory; model/effort if visible; the commit you reviewed; what you ran).
1. Round-1 disposition table (B1–B10, F1, L1–L7), with the deferred-item acceptance per item 1 above.
2. New findings N1…, each with severity (BLOCKER = the boot would be wasted or the playset damaged / MAJOR / MINOR), repo `file:line`, claim, evidence, proposed fix, cheap check.
3. Capture-plan risk ranking (item 2).
4. Owner decisions (choices, not defects), in plain language.
5. Verdict: `SAFE TO BOOT` or `FIX BEFORE BOOT`, one sentence, then the ordered list of what must change before the boot (empty if none).

When the file is complete, run `shasum -a 256` on it and print, as your final on-screen message, the line `HSI-C2-<first 8 hex of the digest>` on its own line, then exactly `DONE` on the next line. (Template: `HSI-C2-xxxxxxxx`.)

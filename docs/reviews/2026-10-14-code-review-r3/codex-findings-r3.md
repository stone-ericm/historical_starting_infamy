# Historical Starting Infamy — code review R3 (HSI-C3)

## 0. Disclosure and checks

An injected conversation-compaction summary of earlier review work was visible. I did not use it as review evidence; the findings and dispositions below come from re-reading the actual diff, R2 report/triage, current files and the checks recorded here. No memory file or shared context corpus was read. The session identifies Codex as based on GPT-6; the precise model variant and reasoning effort are not visible.

Reviewed `build/v1` at `44d5ca854795fd9dcc18818a1f5a03fbdd1b2059`: fixes in `8a78482d59b0d2deed6b9016518be2ea941a4126`, followed by the archived reviews. Read `git diff b503dd0..HEAD` before the R2 triage; the large output was truncated, so I read the operational changes in smaller path-specific diffs and checked the generated files against the renderer. The working tree was clean before the checks and remained clean immediately before writing this report.

Ran the authorized suite once, exactly `cd tools && uvx pytest -q`: exit 0, **129 passed, 1 skipped**. The skip is the retained real acceptance-save test, guarded at `tools/tests/test_savecheck.py:105`. This is a test pass, not an engine boot or real-save certification.

Ran the authorized audit once, exactly `python3 research/scripts/capture_audit.py "/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game"`, without `--write-config`: exit 0, **AUDIT OK**. Every mandatory candidate has an OK estimate; D/RUS and D/PRU have BOUNDARY? estimates. Runtime interest, regime eligibility, liberation movement and protectorate rank/type checks are now explicitly unverified. No network or substitute runner was used.

Other operations were allowed read-only git/file reads and `python3 -B` computations. These independently checked candidate pricing coverage, renderer agreement, generated-script BOM/braces, receipt/oracle mutations, truce/claim mutations, strategic regions and the procedural branch table. Boot/restore scripts ran only through the authorized fake-home suite, never independently. No game, herdr, other agent, git mutation or Victoria 3 user-directory access outside this repo was performed. Only this deliverable was authored; no computation scratch files were needed.

Vanilla references below are relative to `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`; other references are repo-relative. Runtime formatting, pulse cadence, actual UI eligibility and stabilization remain observations for the owner’s boot. I am not reporting any constructed failure as an observed game event.

## 1. N1–N9 disposition

| R2 | Disposition | Current evidence and minimum remaining change |
|---|---|---|
| N1 | FIXED | `tools/hsi/probe_gen.py:76` logs the saved root’s `unrec_mult` immediately after materializing `siv` at `:149`; `tools/hsi/generate.py:55` consumes that local operand; `tools/hsi/measurement.py:145` requires it. The differently timed COUNTRY-modifier counterexample now passes oracle A, while perturbing the DIAG-local modifier produces the expected mismatch. |
| N2 | FIXED | `research/measurement/capture-plan.json:81` replaces RUS with PRU. Independent candidate resolution gives all 13 PRU priced slices and all 15 AUS slices, with zero missing slices. The configured 42-slice set is exactly the union of every current candidate’s priced slices. The helper still supports `no_fixture_records` (`research/scripts/capture_audit.py:183`), but no current candidate uses it. |
| N3 | PARTIAL | Truce/claim checks and runtime-condition disclosure are fixed (`research/scripts/capture_audit.py:126`, `:137`, `:153`). Both injected eligibility mutations now fail. `capture-plan.md:64` still incorrectly puts Alsace in Central Europe. Minimum: name Western Europe and Prussia’s Rhineland/North Rhine ownership as the relevant proxy, retaining the runtime-interest caveat (P5). Mandatory runtime preflight also needs P1. |
| N4 | PARTIAL | Full required-field schemas, finite/code checks, start_b rule matching, distant DIAG dates and extra groups are fixed (`tools/hsi/measurement.py:140`, `:205`, `:232`, `:257`). The five original mutation rows now refuse; all three required positive cases pass. Unexpected keys inside a required group and equal monthly dates still pass; invalid calendar dates escape as ValueError (`:163`, `:221`, `:263`). Minimum: check exact record-key sets, strict sampler-date progression and wrap calendar errors as MeasurementError (P4). |
| N5 | PARTIAL | Atomic lock, verified backup before mutation, early EXIT trap, pre-copy backup integrity checks and atomic restore are fixed (`boot_probe.sh:15`, `:22`, `:31`; `restore_playset.sh:19`, `:28`). The suite proves staging failure, missing destination and invalid-backup recovery/refusal. An existing unhashable destination still aborts restore at `restore_playset.sh:26`. Minimum: make the old-destination hash best-effort; only the backup and restored destination hashes should gate recovery (P2). |
| N6 | PARTIAL | Unique archive allocation, retained staged config/plan/hash and pre-quit debug bytes are fixed (`restore_playset.sh:36`; `boot_probe.sh:36`, `:44`; `PROCEDURE.md:34`, `:48`). Two fake runs retain separate receipts. Collection still reuses a date-only directory with mkdir -p, overwriting same-day evidence (`PROCEDURE.md:46`). Minimum: bind collection to this run and create a fresh attempt directory without merging (P3). |
| N7 | PARTIAL | Boundary fallback, every selected A/B/D constituent tooltip, Cmin detail and context shots are explicit (`capture-plan.md:29`, `:33`, `:36`). The population-order claim is removed. The stop condition at `:41` and `PROCEDURE.md:26` is still “neither,” so one missing mandatory clamp does not stop observer sampling. Minimum: require a complete A/B/Cmin/Cmax inventory before observing; stop if any required capture is absent or non-discriminating (P1). |
| N8 | FIXED | `PROCEDURE.md:7`, `:13`, `:35`, `:56` bind the root and use module subshells. A persistent shell following these blocks stays at the repo root. `boot_probe.sh:57` now names collection step 7. |
| N9 | FIXED — disclosed estimate | `research/scripts/capture_audit.py:15`, `:105`, `:155`, `:194` disclose GDP=population, tier 3 and declared adjacency, and apply the plan’s −0.1 unrecognized modifier. The same Algiers proxy moves from 19.35555 to 17.42000, exactly ×0.9. Shared-language/bonus omissions are disclosed in the docstring. These remain planning estimates. |

### Receipt and oracle mutation results

Used the current `make_probe_log.lines()` in memory, the test ledger, months=3, FRA fixture holder and rule=very_low. No mutated logs were written.

| Mutation or correct case | New result |
|---|---|
| Remove COUNTRY gen_mult | REFUSE: named missing gen_mult fields. |
| Remove DIAG claim | REFUSE: named missing claim fields; no later KeyError is needed to discover the omission. |
| Remove DIAG unrec_mult | REFUSE: named missing local modifier fields. |
| Change start_b RULE to standard | REFUSE: lobby was set to very_low. |
| Date all DIAG records May 17, 1840 | REFUSE: root firing is outside the sampler’s month window. |
| Append complete monthly sample 4 | REFUSE: unexpected group. `choose_snapshot(..., months=3)` selects sample 3. Generation passes this argument (`tools/hsi/generate.py:156`). |
| Remove every DIAG | REFUSE: missing required pairs. |
| Remove monthly sample 3 | REFUSE: configured group missing entirely. |
| Malformed STATE key with an extra slash | REFUSE: missing expected slice and named sample-construction error. |
| GLOBAL pop=nan | REFUSE: non-finite value. |
| DIAG interest_bucket=4 | REFUSE: illegal probe bucket. The renderer intentionally folds engine tiers 3/4 into bucket 3. |
| Mix COUNTRY dates inside sampler sample 3 | REFUSE: sampler has two dates. |
| Mix dates within GBR’s sample-3 DIAG firing | REFUSE: root has two dates. |
| Complete baseline with start_b very_low | PASS. |
| Change only start_a RULE to standard | PASS: start_a remains an independent observation. |
| GBR sample-3 DIAG on April 9, sampler on April 1 | PASS. |
| Same legitimate stagger, sampler COUNTRY unrec_mult=−0.4 while DIAG retains −0.3 | PASS, and oracle A returns no mismatches. |
| Perturb that DIAG-local modifier to −0.4, retaining its old correct siv | Oracle A refuses GBR/HEDJAZ: generator 7.7481 versus engine 9.0394. |
| Append extra start_b COUNTRY/XXX while retaining every required record | Still PASS (P4). |
| Give every monthly record the same April 1 date | Still PASS (P4). |
| Use April 31 as a monthly date | Uncaught ValueError from datetime.date (P4), rather than a named INCOMPLETE result. |

All five original R2 receipt-table counterexamples are closed. The remaining passes above are additional, constructed completeness cases, not evidence that a normal generated probe will emit them. The three correct-boot cases requested by this round are not wrongly refused.

### Script control-flow recheck

The suite now exercises normal restore, launch failure, staging failure, two successive runs, an active-run refusal, missing destination, invalid backup leaving Q untouched, and incomplete backup leaving P untouched. Source order places the EXIT trap before staging and before replacing the live playset. Bad backup digest/JSON is checked before any destination mutation. Archive mkdir allocates a fresh destination, with a suffix on collision; it cannot perform the old `mv active existing-directory` nesting. The staged config is copied from the actual staged tree, and that tree is hashed.

Failure before backup verification can still leave active/; manual restore now explicitly diagnoses “no verified backup” and asks for inspection, without modifying the playset. That is a safe refusal rather than the former misleading “nothing to restore.” I do not require automatic deletion of that evidence. Force-killed boot windows still require the documented manual recovery.

The old unreadable-destination counterexample remains in source control flow: after successfully validating P, restore tries to hash Q merely for its before/after receipt text and exits before the atomic replacement if that hash fails. No independent shell fault injection was run; P2 identifies the exact failing branch. The existing suite tests a missing destination, which bypasses that branch, not an unreadable existing one.

### Regenerated probe

All four renderer outputs match their checked-in counterparts. Every generated script .txt has its UTF-8 BOM. The effects file has **5,732 lines**, balanced 2,112 opening/closing braces, 80 unique STATE keys and 587 unique DIAG keys. Those sets equal the receipt expectations. Each of the 587 DIAG lines contains the saved-root unrec_mult operand.

| Capture | Candidate priced-slice counts; all covered |
|---|---|
| A | MAS 2; MOR 4; CON 1 |
| B | MAS/Algiers 1; BEL/Flanders 1 |
| Cmin | LUC 1; PAR 1; MOD 1 |
| Cmax | AUS 15; PRU 13 |
| D | GBR/WLS 1; RUS/LIT 2; PRU/POL 3 |

The distinct candidate union is exactly 42 fixture slices, with neither missing nor extra entries. This comparison resolves country-wide candidates through vanilla ownership and release candidates through release regions intersected with the current opponent’s ownership; it does not obtain both sides through fixture_slices().

Scope/moment: the monthly country effect saves hsi_root before visiting states (`tools/hsi/probe_gen.py:132`). Each state computes hsi_siv immediately before logging (`:149`); the new field reads `hsi_probe_unrec` through that saved country scope (`:76`, `:107`), with no intervening gameplay effect changing the modifier. The first generated block at `research/probe/common/scripted_effects/zz_hsi_probe_effects.txt:1012` demonstrates the same order. Vanilla `common/script_values/00_infamy_values.txt:258` applies the root’s modifier to this state value. Source inspection and the timing regression support N1’s fix; runtime localization/scoping still needs the boot.

The envelope remains `HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v…`; the DIAG payload gains one field. Hook/sample/key positions and start date token “lobby” are unchanged. The new receipt date parser assumes the monthly GetString form is an English calendar date; the synthetic logs establish that parser behavior, not the actual engine’s emitted format.

## 2. Findings P1–P5

### P1 — BLOCKER when a required capture is missing — The stop condition permits an incomplete mandatory inventory

**Repo:** `research/measurement/capture-plan.md:41`; `research/measurement/PROCEDURE.md:26`, `:28`.

**Claim:** a boot can advance beyond tick 0 without one of the two mandatory clamp observations. There is also no explicit final stop for exhausted A/B alternatives.

**Evidence:** both documents say stop if **neither Cmin nor Cmax** shows its clamp. The literal branch is `not Cmin and not Cmax`. The read-only truth table gives “continue” for Cmin=false/Cmax=true and for Cmin=true/Cmax=false, although both captures are required. Regime eligibility is explicitly unverified, so this is a relevant failure branch, not a claim that the candidates actually fail. The log receipt cannot catch a missing screenshot: it logs configured target states independently of whether a draft was captured. Once observer sampling unpauses, a later refusal cannot recover the missing tick-0 UI observation from those monthly records.

**Fix:** immediately before observe, require usable A, B, Cmin and Cmax captures, each with its required breakdown/context/state-detail inventory. If any one is missing, stay paused and report the missing class; choose a verified replacement or obtain an explicit owner scope decision. D remains optional. Change the table header’s “first that the game lets you draft” at `capture-plan.md:46` to the already intended “first that shows the required observation.”

**Cheap check:** rehearse both one-clamp-missing cases, exhausted B alternatives and a two-state A with one detail missing. Each must stop before unpause. A complete mandatory inventory with D skipped must proceed.

### P2 — MAJOR — An informational hash can still prevent playset recovery

**Repo:** `research/measurement/restore_playset.sh:25`, `:26`, `:28`.

**Claim:** restore refuses an existing destination that cannot be hashed, even when the backup is verified and the directory permits replacement.

**Evidence:** the missing-file guard fixes the absent destination case. For an existing regular file, the script still performs `before="$(shasum … | awk …)"` under `set -euo pipefail`. If shasum cannot read that file, the assignment fails and restore exits before copying P to the temporary file. For example, an unreadable Q can coexist with a writable parent directory; atomic replacement needs the parent permission, not a readable Q. Q’s digest is only a receipt annotation and is not used to validate P. This is the remaining R2 failure branch, not an observed permissions change on Eric’s playset.

**Fix:** attempt the old-file hash in a guarded, best-effort branch and record “unreadable/hash failed” on failure. Keep backup JSON/digest validation and post-restore digest verification mandatory. Do not suppress errors from those integrity checks.

**Cheap check:** in the existing fake-home suite, inject failure only for hashing the live destination, with a valid backup and writable parent. Require restored bytes equal P, archived receipt and the informational failure annotation. The test must assert that its injected hash failure occurred; chmod alone may not fail under a privileged runner.

### P3 — MAJOR — Same-day collection can overwrite another attempt’s evidence

**Repo:** `research/measurement/PROCEDURE.md:41`, `:46`, `:48`, `:49`, `:60`; `research/measurement/capture-plan.md:60`.

**Claim:** run archives are unique, but the documented evidence directory is not. A retry or later tooltip boot on the same date merges or overwrites evidence, including files already declared immutable.

**Evidence:** collection sets D to the date and uses mkdir -p, then copies fixed names including debug.log, debug.checkpoint.log, playset.txt, run-receipt.txt and probe-config.json into it. Running the same block for a second same-day receipt selects a different RUN but exactly the same D. cp overwrites those names and leaves unmatched old files behind. The failure narrative mentions an attempt1 directory and the optional later-D narrative says never merge, but neither rule is implemented by the collection block. This is direct command/path analysis; the block was not executed against real or scratch evidence.

**Fix:** resolve the archived receipt for this boot first, choose a fresh destination incorporating its run id or an explicit attempt id, and refuse an existing destination before copying. Freeze that RUN binding through collection. A later D-only capture belongs in its own directory, even on the same date. Preserve both checkpoint and post-quit logs; if they differ, explicitly choose and document the complete source before extraction rather than discard the checkpoint.

**Cheap check:** the operational harness should collect two same-date fake receipts into separate directories. A second collection targeting an existing directory must fail without changing any file digest. Retain the prior manifest-bound directory unchanged.

### P4 — MINOR — Receipt validation still overstates exact identity/date checking

**Repo:** `tools/hsi/measurement.py:163`, `:221`, `:224`, `:242`, `:263`; `research/measurement/PROCEDURE.md:37`.

**Claim:** COMPLETE enforces required keys and group bounds, but does not enforce exact within-group key sets or strictly increasing monthly dates; calendar errors can bypass its named refusal path.

**Evidence:** the additional mutations in section 1 pass with an extra COUNTRY/XXX and with all monthly dates equal. The date comparison sorts values, so equality is accepted. April 31 raises ValueError in parse_game_date; its callers only catch MeasurementError. These are constructed malformed receipts. I found no changed renderer branch that emits them during an otherwise correct boot, so this is not a demonstrated mandatory reboot trigger.

**Fix:** compare actual record identities against the expected sets for each group, require strict progression of sampler dates without guessing a universal pulse day, and convert invalid calendar construction to MeasurementError. Continue allowing per-root dates a few days apart and independent start_a rule observations.

**Cheap check:** retain the existing positive cases and add extra-key, equal-date and invalid-calendar mutations. Require named refusals, with no traceback. These checks can also run on retained evidence after the boot; no extra game observation is needed to implement them.

### P5 — MINOR — The interest explanation names the wrong strategic region

**Repo:** `research/measurement/capture-plan.md:64`.

**Claim:** Alsace does not supply France an ownership interest in Central Europe.

**Evidence:** vanilla `common/strategic_regions/europe_strategic_regions.txt:4` and `:7` put STATE_ALSACE_LORRAINE in region_western_europe. The independent ownership scan finds no French-owned Central European state. Prussia does own STATE_RHINELAND and STATE_NORTH_RHINE in Western Europe, so a relevant shared-region ownership proxy exists; I am not claiming this makes Cmax/PRU unavailable. Actual play eligibility remains explicitly unverified.

**Fix:** correct the explanation to Western Europe and the Prussian Rhineland/North Rhine states, retaining the distinction between ownership proxy and actual tick-0 tier/availability. Do not infer that France already has a Central/Eastern European interest from Alsace.

**Cheap check:** resolve the named French and target states through the installed strategic-region definitions and verify the shared region. Keep the actual draft/refusal screenshot at the keyboard.

## 3. Owner decisions

This is the last pre-boot review under the cap. No additional review round is needed to make the bounded changes above reviewable; the owner chooses whether to apply them or explicitly accept the remaining failure branches.

D stays optional, including the possibility of another tooltip capture if the measured domain needs a floor discriminator. A non-discriminating D screenshot is still useful evidence, but does not establish floor placement. Keep a later capture in a separate attempt directory.

B5–B7, L2, L3, L5 and L6 remain deferred as instructed. Their implementations were not reopened. The current full-breakdown, every-selected-state and identity/date/rule screenshot instructions preserve the observations they need **if** the mandatory inventory is checked before unpause and collection does not overwrite an earlier attempt. After fixing P1–P3, P4’s remaining validator work can operate on retained evidence; P5 is a small explanatory correction, not proof of a blocked candidate.

AUDIT OK remains a static/proxy result. The owner must resolve actual required draft availability and boundary observations while still paused. Engine log formatting and monthly timing also remain unmeasured; a receipt-format failure should preserve this attempt’s raw/checkpoint logs rather than be papered over by changing operands or choosing another sample. A successful suite does not remove these boot observations.

## 4. Verdict

**FIX BEFORE BOOT** — the probe and original receipt counterexamples are repaired, but the procedure can still advance with a missing mandatory capture, restore can abort on an informational destination hash, and same-day collection can overwrite evidence.

Required changes, in order:

1. Require the complete A/B/Cmin/Cmax capture inventory before observe/unpause, fixing both “neither” stop conditions and the conflicting candidate-selection header (P1).
2. Make hashing the old destination informational while preserving mandatory backup and restored-file validation; cover the failure branch in the fake-home suite (P2).
3. Collect this run into a fresh, non-merging attempt directory and preserve the checkpoint/final log choice and exact run binding; cover same-day collection in the operational harness (P3).

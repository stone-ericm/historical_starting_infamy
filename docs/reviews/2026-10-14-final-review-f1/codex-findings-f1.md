# HSI-F1 — final whole-branch review

## 0. Disclosure and checks

No injected memory summary was visible. I read no memory file or memory directory and used none. The visible identity is Codex based on GPT-6; a more specific model identifier and reasoning effort were not exposed. Reviewed `build/v1` at **13e4d46d8355094454a82011ea4b1ad7d24f06a2**, with a clean working tree when review began. No commits, network research, game launches, other agents, herdr calls or changes outside this deliverable were made. The required `uvx` invocation itself attempted dependency resolution and failed, as detailed below.

Blind-review boundary: I read the assigned prompt, then the branch history/stat, shipped files, architecture, CLAUDE.md, v3.1 spec, v4 addendum, relevant plan/procedure material, implementation, tests, ledger, both measurement directories and acceptance evidence. **Sections 1–3 and 5 and the provisional verdict below were written before opening any earlier review or triage file.** The prompt was the only pre-existing `.codex-review/` file read during this phase. Section 4 records the subsequent earlier-round audit; later clarifications are labeled there.

Checks actually run:

- `git log --oneline main..build/v1`, `git diff main..build/v1 --stat`, `git status --short --branch`, and the HEAD commit record. Twenty-nine branch commits; status initially clean.
- Exactly `cd tools && uvx pytest -q`: **exit 2 before any tests ran**, unable to fetch `https://pypi.org/simple/pytest/` after retries, DNS lookup failure. No substituted runner and no claimed fresh suite pass. The architecture's historical 123-pass/1-skip claim is not my test result.
- Read-only Python with `-B`, importing the tooling without invoking generation: real-ledger validation passed (20 acts, 37 goals, 52 components, 39 ledger slices); the v4 receipt passed; static validator returned **OK** against the explicitly named boot-2 directory and installed vanilla files. The older strict monthly receipt reported exactly the expected missing Ladakh slice and seven diagnostics in sample 3; that is permitted by v4, not a defect.
- Boot-2 extraction gives monthly diagnostic counts **587 + 587 + 580 = 1,754**, under fourteen holders. Oracle A has zero mismatches; maximum absolute residual is **0.000075** (sample 3, BOL/STATE_SANTO_DOMINGO/HAI: replica 3.346875, log 3.3468), well below 0.005. Ledger homeland/language flags also match the effective first-month diagnostic flags for each of the ledger's own holder/slice pairs.
- `compute_tables` reproduces every committed table; every field of all **680** committed derivation data rows matches the computed rows. A separate literal-constant implementation of component factors, severity, rank factors, events, decay, threshold and half-up emission also reproduces all five tables. It did not call `component_value`, `nominal_charge`, `compute_tables` or the timeline functions.
- Recomputed all transcribed numeric tooltip cases in attempt 1. No image viewer was invoked under the restricted command list: screenshot observations here rely on `attempt-notes.md` and `acceptance-notes.md`, not an independent visual transcription of their JPG/HEIC files. No external source text was fetched; historical judgments are distinguished from verified local arithmetic.
- In-memory, read-only reproductions of savecheck acceptance using its test fixture (mocking `Path.read_text`, no scratch saves): `NaN` EGY, `NaN` BOL, absent BOL, duplicate guard, and an unbalanced trailing manager each return an empty problem list. These were computations demonstrating behavior, not a substitute test-suite run.
- Later Part-2 read-only rechecks found exact agreement between all four probe renderer outputs and committed files, independently confirmed all 42 configured fixture slices, and reconciled the checkpoint tail with the final stream (details in section 4). A hypothetical present-target rank case produces the sensitivity result in F5 without a reduction event.
- Acceptance/probe error comparison after stripping the timestamp prefix: acceptance has 34 distinct lines, probe boot 2 has 64, **zero acceptance-only lines**; no acceptance error names HSI. This confirms the narrower probe-baseline comparison, not a vanilla-only comparison.

## 1. Part 1 findings (blind)

### F1 — MAJOR: acceptance has been silently reduced, and its verdict claims more than its evidence

**Locations:** `research/acceptance/ACCEPTANCE.md:21`; `research/acceptance/2026-10-14-run-20261014-153134-83398/acceptance-notes.md:13` and `:17`; `README.md:15`.

**Claim:** the mod “fires once,” applies the Standard table, and changes nothing on an existing save; Very Low and lifecycle checks are optional.

**Evidence:** the acceptance notes explicitly say no save and no lifecycle checks were made. Their Egypt observation establishes the Notorious band, not 54; the numeric tooltip was not opened. Punjab's reported 11.0 is evidence for that one Standard recipient. There is no retained Standard save checking the other countries, BOL or global guard, no Very Low acceptance save, no reload comparison, and no existing-vanilla-save before/after comparison. The logs contain no HSI execution receipt. `playset.txt` records the intended shipped-only playset, and the run receipt records restoration; neither records the infamy rule or every resulting balance. The quiet-error comparison uses another modded probe boot, not the same-day vanilla-only baseline required by v3.1 §9 step 7.

V4 **explicitly preserves acceptance steps 3–7** at `docs/superpowers/specs/2026-10-14-v4-simplification-addendum.md:48`. It retires calibration gates and the tolerance question, not the two rule boots or load checks. The vanilla hook documentation (`common/on_actions/00_code_on_actions.txt:10`) supports the intended once-per-campaign behavior; it does not replace the agreed acceptance measurement.

**Fix:** complete those retained acceptance checks with named, hashed saves and comparisons; repair the checker first (F2). Make the procedure match the preserved requirements. Until then call the existing evidence a Standard smoke check and weaken its verdict/README lifecycle claims. If Eric chooses to waive a requirement, record that as a new owner ruling; do not infer a waiver from the calibration simplification.

**Cheap check:** Standard paused save must have EGY 54, PAN 11, BOL 50, others 0 and one global guard. Very Low must have EGY 16/PAN 1. Reload Standard and compare all balances; load an existing vanilla save and compare against that actual input save. Compare both boot error sets against a named vanilla-only baseline. No new game was launched for this review.

### F2 — MAJOR: the acceptance checker is not fail-closed and cannot certify some claims it advertises

**Locations:** `tools/hsi/savecheck.py:14`, `:78`, `:98`, `:99`, `:120`, `:125`; `tools/tests/test_savecheck.py:67` and `:99`; `research/acceptance/ACCEPTANCE.md:18`.

**Claim:** malformed saves fail closed; Bolivia is checked at 50; the global guard is checked “once”; a truncated save fails.

**Evidence:** with the existing synthetic `SAVE` and `TABLES`, these independent in-memory modifications all produce `check_save(..., "very_low", 0.005) == []`:

1. Replace EGY's `infamy=2.29` with `infamy=nan`.
2. Replace BOL's `infamy=50` with `infamy=nan`.
3. Remove the complete BOL record.
4. Replace `flag=other_flag` with a second `flag=hsi_applied`.
5. Append `truncated_manager={` after the otherwise complete relevant blocks.

`float` accepts NaN, and both the positivity and discrepancy comparisons are false for it. BOL is only checked if encountered. Converting global flags to a set destroys their multiplicity. `parse_save` checks selected balanced blocks, not the full document; it accepts the unbalanced suffix. Its brace readers also do not distinguish quoted braces or comments, which is an unverified limitation for real save contents, not a demonstrated real-save failure here. No real-save evidence currently establishes compatibility with the engine's actual serialized structure.

**Fix:** require finite stored infamy values and finite/nonnegative tolerance, require BOL's record, preserve/check guard multiplicity in the actual global-variable schema, reject duplicate country definitions rather than overwrite them, require the known living bookmark/baseline roster, and read protected blocks with a quote-aware reader. Check lexical whole-input integrity if retaining the global malformed-save claim; a parser for every game subsystem is unnecessary. Retain a real engine save and execute the promised failure-direction mutations on it. Alternatively narrow documentation that exceeds the checker, but presence-only checking is insufficient for the agreed “once” assertion.

**Cheap check:** add each five-case mutation above with a named failure and retain the existing nested-AI-infamy success case. Also reject infinite values, non-finite table entries and NaN tolerance. Do this before using a green savecheck result as acceptance evidence.

### F3 — MAJOR: the published “full derivation” omits every component calculation

**Locations:** `tools/hsi/generate.py:42`, `:87`, `:92`, `:195`; `research/derivation.csv:1`; `README.md:19`.

**Claim:** the full derivation is published; v3.1 §7 requires every component, goal charge, event and balance step.

**Evidence:** the CSV has raw goal totals, goal-processing stages S/C/G/K/R/F, ranks, and timeline rows, but no `component_id`, slice-share operands, capped shares, standing/factor intermediates or component subtotal rows. The component calculations are discarded into `GoalInputs`. For example the Standard Egypt charge totals can be verified by recomputation, but the artifact does not show that `egy_aleppo` starts at (5 + 2.1 + 2.3) × 1.5 × 0.85 = 11.985 before its rank factor gives 19.176. For multi-component liberation goals the CSV cannot explain which component made the raw subtotal. V4 changes snapshot, order, binding and output rounding; it does not withdraw component derivation.

**Fix:** emit auditable component rows, with operands and running values through the factors, plus subject scaling before the raw goal subtotal. Record why ranks/modifiers are measured or fallback, not only their resulting rank names. Regenerate the derivation from the named boot without changing numerical constants to fit it.

**Cheap check:** one merged-slice component must sum shares before caps; component subtotals must sum to the pre-subject raw total, subject blocks must reconcile to `raw`, stages to the charge, and timeline final rows to emitted whole numbers. A two-component goal should be auditable from the CSV without executing Python.

### F4 — MAJOR: a whole-slice mapping conflicts with the ledger's own exclusion account

**Locations:** `research/goal_states.csv:21`; `research/not_representable.md:6`; `research/scripts/author_ledger.py:112`; `research/sources.md:10`.

**Claim:** `bic_assam` treats the complete 1836 BIC slice as Burmese Ahom Assam acquired in the 1824–26 war, while Cachar's separate 1832 annexation is omitted because it is part of that same slice.

**Evidence:** the repository's exclusion account says Cachar is part of the 1836 BIC Assam slice. The component includes all of that slice, with no qualification or evidence reconciling the distinct 1832 acquisition with the 1824 Burmese target. Vanilla `common/history/states/00_states.txt:4421` establishes the BIC slice and several other owner slices; it does not establish a historical 1824 boundary. If the exclusion account is right, the earlier goal is charging later-acquired land under a Burmese owner and the whole-slice-only restriction is not consistently applied. V4 retains the ledger and its scope restrictions (`addendum:5`). This is a demonstrated internal evidence conflict, not a claim that I independently fetched the treaty or established province-level boundaries.

**Fix:** reconcile the boundary against the named source and vanilla provinces in the authoring table. If the cession is only part of the BIC slice, exclude that component under the existing rule; otherwise correct the exclusion account and document the coverage. Do not silently introduce partial-slice approximation. Similar “lies in”/“stands for” reasoning in `goals.csv:29`, `:34` and `:36` needs coverage justification, but I have not independently proved those three mappings wrong.

**Cheap check:** list the 1836 slice provinces and the historical demand coverage, including the Cachar boundary. Recompute after the ruling. BIC is currently zero in all emitted tables, so this does not by itself demonstrate a changed shipped balance; it does affect the promised historical derivation.

### F5 — MAJOR: blank victim tags now select fallback target ranks for actors that exist in 1836

**Locations:** `research/goals.csv:30` (also `:26`–`:28`, `:32`); `research/scripts/author_ledger.py:80`, `:82`, `:84`; `tools/hsi/generate.py:36` and `:55`; `tools/hsi/participants.py:15`.

**Claim:** surviving targets use measured 1836 ranks; only absent actors use a type fallback.

**Evidence:** `pan_ladakh` names Ladakh and uses its LAD state slice, yet leaves `victim_tag_1836` blank because the goal is pending. `_rank_of` treats that blank as an absent actor and assigns `unrecognized_power`. LAD exists in vanilla `common/country_definitions/00_countries.txt:1609` and owns the slice at `common/history/states/00_states.txt:4295`; boot 2 supplies no LAD COUNTRY/rank record. The current 6.21 Standard Ladakh charge therefore uses an unmeasured fallback for a present country, contrary to v4's declared fallback scope (`addendum:39`). The original victim-reduction field has been reused as rank-target identity, but authoring it has not been updated consistently for pending/dropped goals. Belgium and Cambodia have the same omission in Dutch dropped goals and Siam's dropped demand; their ranks happen to be measured through other participants and match the respective fallbacks in this boot.

**Fix:** populate the existing tag for every surviving target irrespective of resolution, and include it in the probe's COUNTRY set. Pending/dropped targets will still receive no enforcement reduction under the current event logic. If a present actor is deliberately assigned a fallback rather than measured, make that an explicit override/ruling with its source instead of describing the actor as absent.

**Cheap check:** a pending LAD goal and a dropped CAM goal must use each target's measured rank without creating a victim-reduction event. In-memory, binding the pending goal to LAD and supplying a hypothetical measured unrecognized regional rank instead of the current unrecognized-power fallback raises this goal from 6.21 to 6.831 and PAN Standard from 11 to 12 after rounding; this is sensitivity, **not a measurement of LAD's real rank or a claim that 12 is correct**. Current 11 cannot be certified against a missing target-rank measurement.

### F6 — MINOR: calibration and release documentation retains factual/count and verification overstatements

**Locations:** `README.md:3`, `:19`, `:21`; `.metadata/metadata.json:6`; `docs/superpowers/specs/2026-10-14-v4-simplification-addendum.md:10`; `ARCHITECTURE.md:31` and `:35`; `research/measurement/PROCEDURE.md:37` and `:56`.

**Claim/evidence:** the retained logs have 1,754 diagnostics, not 1,752. Captures support the observed order/rank arithmetic in the captured domain; they do not empirically verify the final goal floor, subject cases, victim-reduction basis or historical predicates. The addendum acknowledges the floor gap, while the README collapses them into a single “verified against the engine” claim and says assigned war-start dates are the day a demand was made. The ledger covers selected 20 acts with exclusions, not a demonstrated exhaustive inventory of every country's conduct. The architecture still says it is waiting on the probe boot and acceptance and refers to a nonexistent `fixtures_ok.json`. The active measurement procedure still instructs strict receipt completion, fixtures/manifest construction and immutable evidence even though v4 retires those gates. Stale instructions would reject the permitted late-March Ladakh disappearance.

**Fix:** use the honest README wording in section 2, correct the diagnostic count, update status and mark superseded calibration steps. Keep the conservative after-lobby hook; its comment about rule timing is rationale, not evidence that an earlier hook cannot read rules (that was measured readable).

**Cheap check:** sum boot-2 DIAG counts; compare active procedure requirements with v4; ensure no README sentence presents unmeasured behavior or chosen historical mapping as an exact engine/historical fact.

### What the blind review does establish

No shipped syntax or arithmetic BLOCKER was demonstrated. This is distinct from completed acceptance.

- The metadata parses, names 1.14.*, and specifies multiplayer synchronization. Actual independent 1.14.* compatibility and multiplayer behavior were not tested; observed evidence is for 1.14.5 only.
- Additive registration at `common/on_actions/zz_hsi_on_actions.txt:4` matches vanilla `_on_actions.md:115`–`:128`. Rootless rule and guard usage matches vanilla `00_code_on_actions.txt:16`–`:19`, `:155`–`:160`; optional `c:TAG ?=` scopes occur in vanilla at `:97`; scalar infamy change matches `common/history/countries/bol - bolivia.txt:39`. The guard is outside country scope and persists by normal global-variable semantics. That is static support, not a measured reload result.
- The four nonstandard flags match vanilla `common/game_rules/00_game_rules.txt:100`–`:117`; Standard has no flag at `:108`. The shipped `else` correctly selects Standard. Every emitted scalar agrees with `tables.json`; no table emits BOL and the main hook does not scope BOL. The tooling computes BOL then suppresses emission.
- State arithmetic matches `common/script_values/00_infamy_values.txt:29`–`:112`, `:124`–`:284`: caps, exclusive standing/culture/claim branches, adjacency, interest and recognized-root/unrecognized-owner gate. Interest constants agree with `00_diplomacy_values.txt:1068`–`:1073`; source constants agree with `00_defines.txt:1000`–`:1006`, `:1113`–`:1175`. Severity/clamps/subject blocks were compared with all twelve allowed goal-type files, including release-only states in `13_liberate_country.txt:48` and `38_release_as_subject.txt:44`, and both subject blocks in `03_conquer_state.txt:64` and `:78`.
- All eight rank scaling pairs match `common/country_ranks/00_country_ranks.txt:29`, `:67`, `:125`, `:161`, `:196`, `:228`, with no scaling on minor/decentralized. Probe numeric codes are a custom mapping; they are not mistaken for vanilla rank_value numbers.
- Attempt-1 tooltip transcription recomputations: Algiers state 18.04275 → 18.0; Oran 17.4636 → 17.4; protectorate subtotal 35.50635, severity 17.753175, general/rank/rule → **6.7462065 → 6.7**. Their map totals are 6.856245 → **6.8** and 6.636168 → **6.6**. Lucca/Parma/Modena clamp to 3 then yield **1.5675 → 1.5**; Austria/Prussia clamp to 10 then yield **6.65 → 6.6**. This agrees with the transcriptions. The addendum's 17.735 subtotal is an approximate/transcription arithmetic slip, not the exact subtotal derived from its stated operands; it does not change the displayed result. The general and rank blocks must be separate for Mascara. General/rank/rule multiplication commutes, so their internal numerical order is not separately identified by totals; clamps relative to those stages matter. No capture exercised final floor 1; its last position is a source-backed decision from `00_defines.txt:1148`, expressly accepted in v4.
- Egypt's five Syria-goal Standard charges are **19.176 + 13.464 + 10.608 + 9.3024 + 21.84 = 74.3904**. Earlier Sudan balance is exhausted; decay for 1,522 days from 1831-11-01 to the horizon subtracts **20.8350444900753**, leaving **53.5553555099247 → 54**. Punjab accrues **13.068 + 6.21 = 19.278**, less 610 days' base decay **8.35044490075291**, leaving **10.9275550992471 → 11**, subject to the rank-input issue F5.

| Rule | EGY final balance → emitted | PAN final balance → emitted | FRA |
|---|---:|---:|---:|
| Very Low | 16.36015551 → 16 | 1.28855510 → 1 | 0 |
| Low | 34.95775551 → 35 | 6.10805510 → 6 | 0 |
| Standard | 53.55535551 → 54 | 10.92755510 → 11 | 0 |
| High | 72.15295551 → 72 | 15.74705510 → 16 | 0 |
| Very High | 90.75055551 → 91 | 20.56655510 → 21 | 0.89175742 → 1 |

**Measured:** day-one slice shares and sampled-country modifiers/ranks; engine state values and predicates across the present monthly diagnostics; the limited tooltip cases and the reported Standard smoke observations. **Judgments:** selected historical acts/goal mappings, territory coverage, standing, claims, adjacency, interest, subject predicates, assigned event dates, actor attribution, fallback types/ranks, pending treatment and the continuous-decay/same-day counterfactual. **Unverified:** independent source contents/province-level historical boundaries, LAD's rank, a full goal-formula oracle for every allowed goal/rule combination, final goal-floor runtime placement, H2's reduction basis, exact Egypt/whole-roster acceptance, Very Low delivery, reload/late-enable behavior, multiplayer and later 1.14 patches. Nothing in oracle A validates historical judgments.

## 2. README statements and honest wording

| Location / current statement | Honest wording |
|---|---|
| `README.md:3`, “Every country ... its conduct ... extends it to everyone else” (also metadata description) | “Assigns estimated starting infamy from a ledger of selected 1816–1835 acts, using vanilla 1.14.5 pricing and a base-rate replay. Excluded/unrepresentable acts are documented. Countries with no surviving ledger balance remain at zero; Bolivia's vanilla 50 is untouched.” |
| `README.md:15`, “Values apply once ... Adding ... existing save changes nothing” | Until F1 is closed: “The mod is designed to apply on the new-campaign after-lobby hook, guarded by a global flag. Standard has a limited smoke check; save/reload, late-enable and Very Low acceptance are not yet completed.” After actual acceptance, restore the stronger player promise with an evidence reference. |
| `README.md:19`, “Each historical act ... corresponds to ... verified against the engine ... 1,752” | “Selected acts are mapped by documented judgment to vanilla goal analogs. The state formula reproduces all 1,754 present diagnostics under fourteen sampled holders within 0.005. Tooltip cases support severity/clamp processing and separate general/rank scaling; the final goal floor is taken from the define and was not captured.” |
| `README.md:19`, “charged on the day the demand was made, refunded or reduced as the game would do” | “Charges use assigned claim dates, generally the start of the war or crisis, with one modeled resolution. Refund fractions follow vanilla defines; victim reductions use the creator's charge as an unmeasured assumption.” |
| `README.md:19`, “full ... derivation” | Emit the component derivation required in F3; meanwhile say “ledger, source references, measurement logs, goal-stage totals and timeline replay.” |
| `README.md:21`, “actors that no longer exist ... fallback ... ranks” | Resolve F5, or explicitly identify any surviving target deliberately using an unmeasured fallback; do not imply all present actors were measured. |

The five table columns, half-up whole-number output, dropping finished balances below 0.5, base decay without modifiers, day-one proxy inputs, creator restriction, primary-demand omission, canonical same-day ordering and BOL exclusion describe the current computation correctly. No A/B effect on AI behavior is claimed, appropriately.

## 3. False greens as regression cases

These are test gaps identified by reading the suite and by the limited read-only reproductions above; I could not run the prescribed suite. They are not a claim that I ran a mutant suite or proved every proposed mutant survives it.

1. **Malformed acceptance data:** F2's five cases all return success now. Existing tests check altered BOL, not missing BOL/NaN; they truncate halfway through a required block, not after the blocks the reader inspects. Retain a real save, mutate these cases and require named failures. Preserve the nested-AI-infamy success case.
2. **Guard presence mistaken for multiplicity:** two `hsi_applied` records reduce to one set member. A test for presence cannot certify “once.” Check exactly one actual global-variable record; then test the save/reload behavior separately.
3. **Wrong checked-in effect with valid hashes:** change only shipped Standard EGY 54 to 540, or swap High and Low dispatch targets, keeping the input header unchanged. The static checker only verifies input hashes, braces and known flags. Existing generation tests inspect a temporary synthetic repo, not recomputation/equality of the checked-in effect, README and table. Add a read-only round-trip comparison of the real named evidence to every shipped table/body and marker table; ensure BOL is absent in all five. Current files passed my direct comparison; this is future regression coverage.
4. **Wrong or absent shipped delivery hook:** changing the checked-in hook to `on_game_started` or removing its call is not caught by the generation fixture tests or the static validator's presence check. Assert the actual additive registration/callee and guard body, and retain the acceptance evidence; static checks alone cannot measure load behavior.
5. **Pending/dropped present targets wrongly fall back:** fixture `g_pending` leaves a target tag blank and tests that fallback, so it cannot catch F5. Supply a pending present target with a deliberately different measured rank and a dropped target; assert measured scaling and no reduction event. Add an absent historical holder enforcing against a surviving victim that already has positive balance: this promised fallback/reduction integration case is not in the current generator tests.
6. **Split-component arithmetic:** every production component currently has one slice, and the generator fixture also has no two-slice component. A sum-after-caps implementation can stay hidden. Use shares where summing before the cap differs sharply from summing component values; check raw subtotal and F3's component rows.
7. **Historical ledger regression:** tooling tests use `ledger_ok`, not sourced territorial coverage or the authoring table's correctness. The scope-conflict in F4 and present-target omissions pass structural validation. Test the explicit author judgments and compare regenerated CSV bytes, and document province/source coverage; unit tests cannot prove historical facts.
8. **Probe root identity:** `probe_gen.py:150` prints literal `root_tag={holder}` rather than a runtime root identity. The reader's equality check and `test_probe_gen.py:23` therefore certify the generator's label, not an independent engine observation. Wrong inherited root plus correspondingly logged predicates can still be algebraically self-consistent. Current country-rooted hook/branch structure and varied observed predicates provide static/supporting evidence; do not describe the label as independently measured. Add a runtime identity assertion using a proven value path if such a proof remains required.

The final-floor capture was explicitly waived by v4; reinstating the retired ordering registry/fixture gate is not a proposed regression requirement. The floor unit test remains useful for the chosen source-backed formula.

## 4. Part 2 — earlier-round audit

Read all files in the three named archived review directories after persisting the blind report, including findings, triage, prompts and round receipts. Their earlier results are historical evidence, not a fresh suite pass. R3's archived disclosure mentions a compaction summary in that earlier session; none was injected into this reviewer session. No memory file was read.

### Deferred obligations under v4

| Earlier item | Status now | Evidence / what remains |
|---|---|---|
| R1 **B5**, UI operand precision | **MOOT as a fitting-gate obligation.** | The registry/fitter is retired (`addendum:20`, `:46`; no `tools/hsi/ordering.py` remains). Current tests reconstruct A's component operands rather than sum displayed 18.0 + 17.4 as an exact raw 35.4 (`test_formula_goal.py:69`). My blind recomputation yields 35.50635 and the captured 6.7. Keep the captures and their limited precision; do not claim exact general engine calibration or reinstate interval-fitting merely to close this ID. |
| R1 **B6**, typed fixtures/capture binding | **MOOT as an executable schema/generation gate.** | V4 retains captures as evidence/tests, not an oracle-B gate. Attempt-1 notes record holder/rule/date/context and lines; boot-2 day-one data is deliberately the reconstruction snapshot. Missing `fixtures.json`, `oracle-tooltips.md` and the old loader are not merge defects under v4. Independent visual transcription/source completeness was not certified by this review. README claim limits remain F6. |
| R1 **B7**, fixture-inclusive numerical equivalence | **MOOT.** | No ordering candidate selection/equivalence classes are used; fixed `ORDER = SCGKRF` is the approved calibration. Final floor is explicitly unobserved and accepted from the define. |
| R1 **L2**, required manifest evidence set | **MOOT as the old manifest gate; current binding is fulfilled on this named boot.** | V4 removes the manifest/immutability rule (`addendum:44`). `hashes.py:10` hashes exactly the top-level rotated logs read plus collected probe config; `generate.py:188` includes those, ledger/source/vanilla hashes and order. My static check matches every current input. Boot 2 retains system/version/playset/run/config/plan evidence and names the actual game build. Do not require the retired manifest. Broader generator version/provenance checks would be hardening, not an outstanding L2 requirement for this boot. |
| R1 **L3**, complete derivation | **PARTIAL; STILL OWED (F3).** | `generate.py:92` and `:196` now preserve raw, ranks and every S/C/G/K/R/F stage; replay/emission values are separate. Component/slice/cap/factor/floor intermediates and subject reconciliation remain absent. V4 does not waive them. Earlier triage promised them before first generation; tables have now been generated without them. |
| R1 **L5**, non-finite save acceptance | **STILL OPEN (F2).** | `savecheck.py:98`, `:120` and `:136` are substantively unchanged. I reproduced NaN in EGY/BOL. After the blind phase I also reproduced doubled 4.58 accepted for 2.29 with NaN tolerance, with finite tolerance 3, and with a NaN table value. Whole numbers retire the storage-precision investigation/tolerance-selection question; they do not make NaN comparisons safe. Require finite table/save/tolerance values and a comparison tolerance that cannot hide a wrong whole number; no new storage-precision sampling gate is proposed. |
| R1 **L6**, missing records/guard/structural reader | **STILL OPEN (F2/F1).** | BOL is optional in the checker, guard multiplicity disappears, duplicate definitions overwrite, and no baseline bookmark roster or real save is retained. R1 triage explicitly accepted missing BOL/roster/duplicate guard as real gaps to close before Task 15. R2 agreed the reader can stay narrow, but protected blocks must respect quoted strings. This review does not require parsing every game subsystem: checking the protected structures, required identities, duplicates and lexical whole-input integrity is sufficient. If whole-file integrity is deliberately outside scope, remove the global “malformed save raises; nothing is guessed” claim and retain a valid, hashed real artifact. That does not waive the roster, finite comparisons or guard requirements. |

**The addendum did not retire L3, L5 or L6.** Nor did it make Standard/Very Low acceptance or reload/late-enable checks optional. Those are the substantive still-open earlier findings; their repeated reproduction is why an earlier deferred status cannot now be treated as completion.

### Other R1 findings

| Item(s) | Current disposition and verified location |
|---|---|
| **B1** planned B unavailable | Re-targeted to MAS/Algiers and BEL/Flanders (`capture-plan.json:34`); the unavailable SAR plan is gone. V4 accepts the observed map-tooltip B evidence rather than requiring a new draft-panel capture. No need to re-run the old capture boot. |
| **B2** invalid D release/fallback | The invalid SIC/AUS-LOM candidates are gone (`capture-plan.json:89`), D is optional, and final-floor fitting is retired by v4. Missing D is an explicitly accepted limitation, not an open blocker. |
| **B3** missing fixture states/guard | Fixed in `participants.py:8`, `:20`, `:24` and `probe_gen.py:81`. I re-rendered in memory: all four committed probe outputs exactly match. Independently resolving candidate ownership/release regions gives the same **42 fixture slices** as config, including all 15 AUS and 13 PRU slices. All 39 ledger slices also exist in vanilla history. |
| **B4** incomplete diagnostics/alignment | Repaired then deliberately simplified: strict start receipts remain at `measurement.py:219`; DIAG carries local operands and local unrecognized modifier (`probe_gen.py:138`, `generate.py:66`); all present monthly diagnostics are checked (`generate.py:170`). Removing every diagnostic refuses generation. V4 permits short monthly samples and retires stabilization. Current named final logs pass the new contract; the active procedure's old strict promise is F6. |
| **B8** latest-backup/stale staging | Fixed by active-run acquisition/verified backup/early EXIT trap (`boot_probe.sh:15`, `:22`, `:28`), clean probe staging (`:37`), pre-copy integrity and atomic restoration (`restore_playset.sh:19`, `:28`). Run-bound archives replace global latest-backup choice. Only source/retained receipts were checked in this round; operational tests did not freshly run. |
| **B9** playset/log evidence lost | Staged JSON/config and checkpoint/final rotated logs are retained and collected through the exact archived receipt (`collect_evidence.sh:18`, `:27`, `:33`). Evidence is present for boot 2. See the concrete checkpoint-tail clarification below. |
| **B10** bad CLI/cwd | Fixed in `PROCEDURE.md:7` and `:35`: correct module flags and subshell cwd. The remaining obsolete calibration instructions are F6, not the old import/argument-vector defect. |
| Formula **F1**, threshold after rounding | Corrected and superseded by the new 0.5/whole-number policy (`generate.py:71`; `test_generate.py:97`). Eligibility is tested before half-up emission; no stale 0.05 output is shipped. |
| **L1**, tagged holder selects zero modifiers | Fixed both directions at `ledger.py:172` and `:174`. Current ledger validates. F5 is a separate missing *target rank identity* defect, not a regression of this modifier invariant. |
| **L4**, missing content validates green | Fixed phase-required roots/files/rules and required measurement argument (`validate.py:71`, `:74`, `:88`, `:91`). Current full validation passes with current bindings. Old fixtures/manifest arguments correctly disappeared under v4. Output/dispatch body equality remains the regression gap in section 3, not a claim that current bodies mismatch. |
| **L7**, language lookup representation | Fixed at `vanilla_lookup.py:26`–`:28`; the author reads `language` at `author_ledger.py:18`. The ledger's effective holder/slice language/homeland flags agree with measured diagnostics. |

### R2 N1–N9 and R3 P1–P5

| Item | Current status / evidence |
|---|---|
| R2 **N1** timed modifier | Fixed: `probe_gen.py:138` captures the current country's modifier before state visits and includes it in DIAG; `generate.py:66` uses that field. Actual oracle checks succeed for varied per-root firing dates. |
| R2 **N2** incomplete RUS Cmax | Fixed: PRU replaces RUS as Cmax (`capture-plan.json:79`); its 13 slices are all measured. RUS's two Lithuanian *release* slices remain for optional D, which is different and correctly bounded. |
| R2 **N3** audit overstates eligibility | Static truce/claim checks and explicit runtime caveats are present (`capture_audit.py:126`, `:137`, `:153`; `capture-plan.md:3`). Regime/interest/rank/movement eligibility was never made a source-only fact. Accepted captures now provide the relevant runtime evidence for the chosen cases; retired gates need no new eligibility boot. |
| R2 **N4** schema/window | Fixed at `measurement.py:152`, `:181`, `:228`, `:265`, with R3 refinements below. V4 changes completeness policy, not finite/code/date/schema checks. |
| R2 **N5** unsafe rollback / R3 **P2** informational hash | Fixed: early trap and backup validation precede mutation; the old destination hash is best-effort at `restore_playset.sh:25`–`:28`, backup/post-restore checks remain mandatory. `test_boot_scripts.py:119` covers unreadable destination and explicitly skips if injection does not occur. No fresh shell execution here. |
| R2 **N6** run identity / R3 **P3** overwrite | Fixed: unique run/archive, `.run/last`, retained staged inputs and fresh non-merging destination (`boot_probe.sh:19`, `:45`; `restore_playset.sh:38`; `collect_evidence.sh:18`, `:24`). Tests at `test_boot_scripts.py:145` check distinct collections and unchanged digests on refusal. V4 permits regeneration from explicitly named evidence, so old manifest immutability is moot. |
| R2 **N7** boundary/inventory / R3 **P1** stop condition | The four-capture stop condition was applied (`capture-plan.md:36`, `PROCEDURE.md:25`), as were every-constituent/context instructions (`capture-plan.md:26`). Attempt 1 explicitly identifies B's substituted map tooltip and missing D. V4 supersedes the old fitting/capture gate; it does not require another capture just to close these historical pre-boot IDs. Mark the old procedure superseded (F6). |
| R2 **N8** persistent cwd | Fixed: procedure's module commands use subshells and named repo-root context (`PROCEDURE.md:12`, `:35`, `:48`). |
| R2 **N9** estimate proxies | Disclosed/corrected for its original scope (`capture_audit.py:15`, `:101`, `:155`), using unrecognized discount −0.1 but GDP=population and neutral interest. These planning estimates also lack the newly discovered rank block (`:160`); they are not generator operands or oracle measurements. Mark them obsolete or add ranks before reusing them for a future boundary plan. No shipped number comes from that audit estimate. |
| R3 **P4** exact receipt keys/calendar | Fixed at `measurement.py:247`, `:252`, `:275`, `:176`, `:298`: unexpected identities refuse, invalid calendar dates become named errors, sampler dates must increase. I inspected the corresponding mutation assertions at `test_measurement.py:122`; the current real receipt passes v4. |
| R3 **P5** Alsace region | Fixed at `capture-plan.md:63`: Western Europe, Prussian Rhine ownership proxy, no French Central Europe ownership, actual interest remains a runtime caveat. |

**Checkpoint clarification found after the blind phase:** boot-2 checkpoint extraction contains 2,314 HSI payloads; final extraction contains 2,315. The checkpoint's last payload ends mid-record at `HSI;monthly;3;March 31, 1836;DIAG;GBR/STATE_WALLONIA/BE`. The final logs have that full BEL record and one further GBR/STATE_WEST_AEGEAN_ISLANDS/GRE record. All earlier payloads match in order. Thus the count increase alone does not prove a byte-prefix relationship, but this actual difference is a repaired partially copied tail plus one completed record, not demonstrated lost evidence. The generator and hashes use the complete **final** log set; my validation/oracle check used those same files. The checkpoint must not be called a complete parseable receipt. Retain this distinction in any revised procedure/evidence note.

**Regression proposals from R1 T1–T13:** triage only claimed partial adoption, not closure of every proposal. Capture/receipt, threshold, operational fake-home and validator-presence cases were added. Finite save/roster/guard/real-save cases remain owed as L5/L6. Component derivation remains owed as L3. Other surviving optional gaps include UTF-8 non-ASCII payload preservation, a language-bonus-only arithmetic case, per-goal subject arithmetic (especially regime change), all-three-kind same-day step ordering, an absent-holder/positive-victim generator integration case, complete independently enumerated hash-key coverage and actual shipped-output/dispatch equality. R1's old ordering-JSON/interval/equivalence mutants are moot under v4. These proposals should not be described as fully exercised merely because a synthetic suite passed in an earlier round.

## 5. Owner decisions (choices, not defects)

- Day-one 1836 shares/modifiers/ranks, quantized shares, observed stage order, source-backed unobserved final floor, whole-number output, no stabilization policy and no fixture/manifest gate are approved v4 choices. A moving early economy or missing late Ladakh monthly slice is not a reason to reinstate those gates.
- Base continuous decay, canonical same-day order, chosen war-start claim dates, one claim/resolution, omission of the primary-demand surcharge, creator-based victim reductions (H2), creator=holder and whole slices are declared counterfactuals. Do not tune constants because Egypt is the only substantial Standard result or because a different historical estimate is desired.
- The ledger's Ladakh pending status derives from vanilla's independent LAD start despite its own cited campaign extending to October 1835 (`sources.md:16`). Whether history or the bookmark should govern that judgment is an owner choice that should be stated; pending versus pre-horizon enforcement would only add a reduction to LAD's zero modeled balance here, not refund PAN's charge. The rank identity problem F5 is separate.
- Attributing Gulab Singh's Ladakh act to PAN, treating Cambodian dual tributary status without a loyal-subject reduction, and using fallback ranks for genuinely absent polities are documented choices. The Vientiane “Lao rebellion” mapping has no sourced explanation for `rebellious_subject=0` (`goals.csv:33` versus vanilla `03_conquer_state.txt:78`); review that predicate against the full subject/enemy/initiator condition rather than automatically applying a discount from the word “rebellion.” No independently fetched source proves all three conditions here. Its current SIA balance decays to zero in every table regardless.
- No historical source text was available in the repository beyond summaries/reference names. Peshawar's “lies in” slice note, the entire-RUS-Azerbaijan=Nakhchivan mapping, and Kedah/Spanish reconquest coverage deserve geographic source checking. I am guessing that some cover more than their named act; I am not declaring those guesses proven defects. F4 is stronger because the repository itself states the conflicting Cachar coverage.
- Low/High/Very High live dispatch boots and a matched-seed observer A/B are declared follow-ups/residuals, not new merge gates. Standard and Very Low acceptance plus lifecycle checks remain required unless Eric explicitly changes the ruling. Publication still requires explicit approval.

## 6. Verdict

**FIX BEFORE MERGE** — numerical replay matches the chosen inputs, but acceptance, target-rank provenance, ledger scope consistency and promised audit artifacts are incomplete.

1. Repair the acceptance checker (F2), then complete the preserved Standard/Very Low/full-save/lifecycle/vanilla-baseline checks (F1), or obtain an explicit scoped owner waiver and revise the claims.
2. Resolve surviving-target rank identity/provenance (F5) and the Assam/Cachar whole-slice conflict (F4) at the authoring source; regenerate from named evidence after any numerical change.
3. Publish component derivation rows (F3), with a reconciliation check.
4. Correct the README, counts and active procedures/status (F6), and add the focused regression cases for the changed behavior.

# Historical Starting Infamy — code review R1 (HSI-C1)

## 0. Disclosure and scope

No injected memory summary was visible, and no memory file or shared context corpus was read or used. The session identifies me as Codex based on GPT-6; the exact model variant and reasoning-effort setting are not visible.

Reviewed `build/v1`, HEAD `dfed03422804e71ffd2e9c5cf033ba039e53d36d`, including the whole `main..build/v1` change. The initial working tree was clean. Read CLAUDE.md, ARCHITECTURE.md and spec v3.1 in the requested order, then relevant plan sections, implementation, tests, generated probe, research tables and procedures. Ran the suite once, exactly `cd tools && uvx pytest -q`; it passed, with the retained real-save test skipped. That result is context, not a finding.

Other checks were read-only `git status/log/diff`, file reads/searches, and Python computations with bytecode writing disabled. They checked every ledger owner slice against vanilla state history, all holder/victim tags for bookmark ownership, CSV agreement with the author tables, generated-probe agreement with its renderer, BOM/braces, and the counterexamples below. The three CSVs match the author tables, all 39 distinct ledger slices exist, and every current holder/victim tag owns a bookmark slice. These checks do not establish historical territorial coverage or the correctness of mapping judgments. No game, network, herdr, other agent, git mutation or external playset/save operation was used. The sole authored artifact is this report.

Vanilla references below are relative to `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`; repo references are relative to the reviewed repository.

**Verification limit:** the permitted search found no `effects.log`, `triggers.log` or `event_targets.log`, and no corresponding generated script documentation in the install. I could compare the probe with vanilla uses of its effects, triggers, links and localization functions, but could not certify their runtime scope behavior or the exact emitted log envelope. Vanilla `common/script_values/00_infamy_values.txt:1`, `:29`, `:114`, `:148`, `:185`, `:198`, `:212` and `:264` substantiate the measured quantities and predicates; `common/history/treaties/00_historical_treaties.txt:632` uses `s:STATE_….region_state:TAG`; `common/on_actions/00_code_on_actions.txt:854` uses a localized `debug_log`; `localization/english/diplomacy_l_english.yml:2414` uses state `MakeScope.ScriptValue`, and `localization/english/core_l_english.yml:17` uses `GetTagName`. Hook roots and additive registration are documented at `common/on_actions/00_code_on_actions.txt:3`, `:10`, `:474` and `common/on_actions/_on_actions.md:106`, `:115`.

The generated 4,994-line effects file agrees with `render()` and passes BOM/brace checks. There is no evidence here that its size alone prevents loading. Conversely, those checks are not an engine load test. Numeric localization inside this particular rootless/country-rooted chain, preservation of the root through scripted effects, actual monthly firing dates, third-sample economic stabilization, launch/quit log rotation, tooltip display order versus calculation order, and a real 1.14.5 plaintext save remain unmeasured. I am not reporting guesses about those behaviors as observed defects.

## 1. Boot-wasting findings

### B1 — BLOCKER — Neither planned B target permits the requested draft

**Repo:** `research/measurement/capture-plan.md:8`; `research/measurement/PROCEDURE.md:19`.

**Claim:** France cannot draft Conquer State against Sardinia-Piedmont at the untouched bookmark. Switching from Savoy to Piedmont does not remove the blocker.

**Evidence:** vanilla `common/history/diplomacy/00_relations.txt:237`–`:240` gives SAR–FRA relations 30. `common/defines/00_defines.txt:990` sets cordial to 20. `common/diplomatic_plays/00_diplomatic_plays.txt:117` requires `diplomatic_play_has_no_relations_blockers`, whose target predicate at `common/scripted_triggers/00_scripted_triggers.txt:1763`–`:1766` requires relations strictly below cordial. Both states have the same target country. Savoy's state slice and French homeland do exist (`common/history/states/00_states.txt:2028`–`:2036`); this is a diplomacy blocker, not a missing-state or formula-factor problem.

**Fix:** replace B with a target whose entire eligibility chain is checked at tick 0, or explicitly document controlled probe-only preparation that removes the relation blocker before capture without altering formula operands. Update the fallback too. Do not require waiting for relations to change: captures must stay at tick 0.

**Cheap check:** a static target audit should calculate starting relations versus the cordial define and resolve the play's scripted prerequisites. It must reject both existing B entries before any boot.

### B2 — BLOCKER — D's primary release is unavailable, and its fallback is also blocked

**Repo:** `research/measurement/capture-plan.md:11`; `research/measurement/PROCEDURE.md:21`.

**Claim:** “Liberate Sicily from Two Sicilies” is not a separate country release at this bookmark. The named Lombardy fallback cannot be drafted by France under the current relations either. Thus the plan has no usable floor-binding D capture.

**Evidence:** the release entry for Sicily is `SIC = { states = { STATE_SICILY } }` in vanilla `common/country_creation/00_releasable_countries.txt:1361`. SIC is already Two Sicilies (`localization/english/countries_l_english.yml:678`; `common/country_definitions/00_countries.txt:745`), and owns Sicily (`common/history/states/00_states.txt:1148`–`:1151`). There is no separate Sicily tag in the country definitions/release entries inspected. Lombardy is a real LOM release (`common/country_creation/00_releasable_countries.txt:418`), but FRA–AUS starts at 20 (`common/history/diplomacy/00_relations.txt:88`). Liberate Country requires the same strictly-below-20 relation predicate (`common/diplomatic_plays/00_diplomatic_plays.txt:190`; `common/scripted_triggers/00_scripted_triggers.txt:1766`). Liberation additionally has a code-side movement support condition documented by `common/defines/00_defines.txt:1111`; selecting a releasable tag alone does not establish eligibility.

There is also an unapproved contract substitution: spec §6 calls for a **Conquer State** D fixture, while this plan uses Liberate Country. A legal liberation can exercise the common final floor, but that substitution must be stated and justified, not silently treated as the specified capture.

**Fix:** establish a legal, genuinely floor-binding D and fallback at tick 0. Prefer the specified goal type; if an alternative is accepted, record the ruling and why it discriminates the relevant candidate orders. Check target existence, relations, interest, claims, subject/truce restrictions and any release support requirement, in addition to the numeric boundary.

**Cheap check:** resolve each release tag against the bookmark's existing country roster and evaluate starting relations. The current primary and fallback must both fail this check. Audit replacement arithmetic using the correct capital/homeland standing and interest multiplier; population-only estimates are not measurements.

### B3 — BLOCKER — The probe cannot produce the fixture STATE records the contract requires

**Repo:** `tools/hsi/probe_gen.py:79`, `:113`, `:121`, `:126`; generated `research/probe/common/scripted_effects/zz_hsi_probe_effects.txt:41`; `research/probe/config.json:1`.

**Claim:** `slices` comes exclusively from `led.all_slices()`. There is no fixture-target input. None of the planned primary fixture states is logged, so the boot cannot retain the required aligned tick-0 fixture state records.

**Evidence:** a read-only scan of the generated effect found no `STATE;STATE_FEZ/`, `STATE_MARRAKECH/`, `STATE_AL_RIF/`, `STATE_INNER_MOROCCO/`, `STATE_SAVOY/`, `STATE_TUSCANY/`, `STATE_SICILY/` or `STATE_LOMBARDY/`. Piedmont is absent too. Vanilla MOR owns the four Morocco states, SAR owns Savoy/Piedmont, TUS owns Tuscany, SIC owns Sicily and AUS owns Lombardy; those are valid slices but are outside this ledger. Spec §6 requires STATE records per fixture target and keeps them with the matching tick-0 capture. FRA's COUNTRY record does not replace those records.

A related renderer defect is currently hidden by this ledger: `fixture_holder` is included in COUNTRY records at `:78`, but not independently in the monthly guard at `:80` or DIAG loop at `:123`. Rendering the test ledger with `fixture_holder=USA` logs USA COUNTRY records but generates neither a USA monthly guard nor USA DIAG records. BOL similarly depends on being a ledger holder for its own monthly firing.

**Fix:** give the capture plan a machine-readable holder and complete owner-slice list; union that with ledger slices for the appropriate samples. Independently include the fixture holder and BOL in the required monthly participant set, and include the fixture holder in diagnostic evaluation. Regenerate the checked-in probe from that input.

**Cheap check:** render without writing and assert the exact set of fixture STATE keys is present in both start samples. Test with a fixture holder absent from the ledger and assert its guard and DIAG coverage. This check can run entirely before boot.

### B4 — MAJOR — Missing diagnostics and mixed/incomplete samples are accepted as usable evidence

**Repo:** `tools/hsi/measurement.py:78`, `:116`, `:147`; `tools/hsi/generate.py:46`, `:140`–`:144`.

**Claim:** the receipt gate does not establish sample completeness or alignment, and oracle A can succeed without executing a single comparison.

**Evidence:** read-only counterexamples based on `make_probe_log.lines()`:

- Delete every DIAG record: `choose_snapshot()` returns sample 3 and `diagnostic_check()` returns `[]`.
- Change every DIAG date to `May 17, 1840`, leaving GLOBAL/STATE/COUNTRY at April 1, 1836: selection and oracle A still succeed, and the returned date is April 1, 1836.
- Delete monthly sample 3 completely: selection accepts sample 2.

`build_snapshot()` checks only that one GLOBAL exists; it neither validates record dates/hook/sample consistency nor required schemas. `choose_snapshot()` checks required last-sample slices/countries, not the DIAG Cartesian product, both start hooks/RULE records, or completion of the configured window. The generator checks only last-sample diagnostics, whereas spec §9 oracle A covers every DIAG record using its own sample. Grouping by `(hook, sample)` cannot itself establish that separately fired country diagnostics are aligned with the sampler's GLOBAL/STATE records.

**Fix:** define a required receipt from probe configuration: start hooks and RULE records, required fields and legal codes, monthly sample IDs, participant/slice diagnostic keys, and an explicit alignment policy backed by actual firing dates. Refuse missing/extra/mixed records. Run oracle A for every diagnostic sample. If country pulses actually fire on different dates, repair the sampling design rather than discard the dates. Do not accept an earlier snapshot merely because the planned last one vanished.

**Cheap check:** the three mutations above must be refused with named completeness/alignment reasons; perturb sample-1 `siv` and require oracle A to fail. Apply this validator to the live boot evidence before quitting so collection errors are discovered while the session is still recoverable. The 2% economic policy itself must remain a refusal, not an excuse to select a different sample.

### B5 — MAJOR — Rounded UI operands are treated as exact engine subtotals

**Repo:** `research/measurement/capture-plan.md:13`; `tools/hsi/ordering.py:23`, `:46`, `:52`, `:57`, `:88`.

**Claim:** summing displayed state values into a float and then formatting a prediction can reject a correct engine order. There is no operand precision or uncertainty representation.

**Evidence:** vanilla `localization/english/diplomacy_l_english.yml:2430` formats country state values to one decimal. The capture instructions say those displayed state lines sum to the raw subtotal. Read-only arithmetic demonstrates the loss: an actual raw subtotal 10.24 displays as `10.2`; under ×0.95 and ×0.5 its total displays `4.9`, while using 10.2 as exact input predicts `4.8`. The same boundary issue applies to A: actual 80.24 versus transcribed 80.2 gives displayed totals 19.1 versus 19.0 under ×0.5 severity, ×0.95 and ×0.5 rule. Summing several rounded state lines increases the uncertainty. These are constructed counterexamples, not claims about the actual Morocco tooltip.

**Fix:** retain the precision of each operand and fit orders against consistent rounding intervals, or collect a sufficiently precise engine raw subtotal under the correct holder/target scopes. Do not “fix” vanilla constants or adjust a transcription to obtain a fit. Preserve observed clamp thresholds and multipliers as their own quantities; they are not necessarily running totals.

**Cheap check:** add the 10.24/10.2 and 80.24/80.2 cases as rounded transcripts. The true order must remain admissible, and ambiguity must still be reported when the retained precision cannot distinguish classes.

### B6 — MAJOR — Fixture data does not bind the capture or preserve the observed multipliers

**Repo:** `tools/hsi/ordering.py:13`–`:26`, `:44`–`:57`, `:83`–`:89`; `tools/hsi/generate.py:145`–`:147`.

**Claim:** the loader discards holder, target, date, tick and sample identity and has no field for an observed severity/general/rule multiplier. It cannot implement the specified tick-0 binding or validate every transcribed line.

**Evidence:** adding `holder=XXX`, `target=XXX`, `date=1900-01-01`, `tick=100`, `hook=monthly`, `sample=3` to every synthetic fixture leaves `load_fixtures()` accepting all four unchanged. No start snapshot is built or compared in generation. A multiplier-only line has `running_text=None` and is ignored numerically by `fits()`. Its decimal count does not preserve the actual multiplier value. State-factor lines cannot be represented in the Line stage enum at all. Vanilla's severity localization explicitly displays a multiplier (`localization/english/diplomacy_l_english.yml:2433`), and clamp localization displays a threshold (`:2434`–`:2435`); the current schema only distinguishes a running value from no value.

**Severity hypothesis:** a valid above-floor, unclamped A capture containing a sufficiently precise raw subtotal, the observed ×0.50 severity, the actual holder modifier, rule factor and total can confirm or refute the multiplier inference. The probe itself logs state values/modifiers, not goal-level severity behavior. The current fixture structure does not retain or check the observed multiplier, and does not verify the supplied general modifier against the capture's FRA COUNTRY record. Thus screenshots/manual reasoning might supply the observation, but the implemented gate does not establish the full claimed observation chain.

**Fix:** retain capture metadata, source precision, labels and typed quantities (running value, multiplier, clamp threshold, raw subtotal, total). Verify tick/date/rule/holder and required fixture state coverage against the same start capture. Retain state-factor observations for documentary/oracle-A cross-reference even when oracle B deliberately does not recompute them. Require the needed capture classes and exactly one final total; reject invalid/non-finite inputs and duplicate stages/IDs.

**Cheap check:** wrong holder, nonzero tick, wrong sample/rule, changed severity multiplier, mismatched general modifier and missing required captures must each fail. A multiplier-only severity line must be numerically checked rather than dropped.

### B7 — MAJOR — Equivalence classes omit the fixtures themselves

**Repo:** `tools/hsi/ordering.py:59`–`:64`, `:73`; `tools/hsi/generate.py:146`.

**Claim:** equivalence is evaluated only on ledger GoalInputs. Spec §3 also includes every fixture in the numerical domain. Orders with unequal fixture charges can therefore be collapsed into one accepted class.

**Evidence:** read-only reproduction: use an above-floor protectorate as the ledger domain and a Conquer State fixture with raw 1.5, general modifier −0.05, Very Low, total `1.0` at one decimal. Both `SCGRF` and `SCRFG` fit the displayed fixture and are equivalent on the ledger, but their exact fixture charges are 1.0 and 0.95. `select_order()` accepts `SCGRF` instead of refusing the two fixture-domain classes. UI equality establishes fit; it is not the spec's exact numerical equivalence relation.

**Fix:** include fixture operands, with their appropriate rule domain, when constructing numerical equivalence signatures. Preserve the separation between displayed fit and numerical equivalence, including the precision policy fixed in B5.

**Cheap check:** the reproduction above must raise `OrderingAmbiguous` under the approved exact-operand contract. Add a separate genuinely equivalent fixture-domain pair to guard against an overstrict fix.

### B8 — BLOCKER — Restore selects a global “latest” backup rather than this run's original playset

**Repo:** `research/measurement/boot_probe.sh:8`–`:13`; `research/measurement/restore_playset.sh:5`; `research/measurement/PROCEDURE.md:26`; `research/acceptance/ACCEPTANCE.md:24`.

**Claim:** restoration is not bound to the backup that belongs to the boot. Retrying a launch or creating another backup can cause “restore” to leave the probe enabled while reporting success.

**Evidence:** the scripts' exact control flow suffices: run 1 backs up original playset P, then writes probe playset Q. A later retry backs up current Q under a newer name. Restore chooses that newer backup and copies Q, never P. A different task's newer backup can win in the same way. No run identity/original digest is retained. `exec` also leaves restoration entirely to a later manual action after launch failures. The staging `cp -Rf` at `boot_probe.sh:10` merges into an existing probe directory, so deleted/renamed source scripts can survive as stale enabled content. The timestamp has only second precision and does not exclude an existing backup name.

**Fix:** preserve a unique run receipt with the exact backup path and original digest; refuse a nested boot that would replace its original backup. Restore that exact file and verify byte-for-byte equality. Guarantee cleanup/restoration on launch failure and normal exit through a wrapper that waits for the game rather than replacing itself with `exec`, or require an explicit receipt argument for a reliably managed manual restore. Stage an exact clean copy in a task-owned directory, not a merge. Leave the original backup recoverable until verification succeeds.

**Cheap check:** test against a temporary fake HOME with P and Q: two launch attempts, a newer unrelated backup, a launch failure, and a stale staged script. The final playset must be P in every restoration case, and the staged file set must exactly match the source. Do not run these tests against Eric's real playset.

### B9 — MAJOR — Evidence is collected after restoring its playset and without a log-completeness checkpoint

**Repo:** `research/measurement/PROCEDURE.md:23`–`:31`; `tools/hsi/measurement.py:45`–`:52`, `:218`–`:227`.

**Claim:** the written sequence loses the direct source for `playset.txt`, and does not protect a one-shot capture against log loss/rotation.

**Evidence:** step 6 restores `content_load.json`; step 7 then asks for `playset.txt` containing the file used. Copying the current file at that point records the original playset, not the probe playset. Neither boot script retains the staged JSON as evidence. Extraction reads only the named `debug.log`; the CLI validates syntax/duplicates but neither builds complete snapshots nor establishes required evidence. There is no live capture or pre-quit check for the full receipt. I could not measure whether this particular run would rotate on quit or exceed a log limit; the finding is the absence of recovery/verification for that contingency, not a claim that rotation definitely occurs here.

**Fix:** retain the actual staged playset JSON and loaded-mod/version evidence before restoration. Preserve the debug stream (including relevant rotated segments if they occur), system/error logs and tick-0 screenshots before another launch can overwrite them. Before leaving the running session, check that both start receipts and the configured monthly receipts are complete and parseable. Bind the collected original/staged playsets to the run receipt in B8.

**Cheap check:** dry-run the collection sequence with distinct original/staged JSON and a log split across two segments. The retained playset must be the staged one, and omission of any required record must be diagnosed before evidence is declared ready.

### B10 — MINOR — The documented prerequisite commands do not address the actual CLIs

**Repo:** `research/measurement/PROCEDURE.md:3`–`:4`; `tools/hsi/probe_gen.py:160`–`:165`; `tools/hsi/validate.py:70`–`:72`.

**Claim/evidence:** from the repo root, `python3 -m hsi.probe_gen --research research --out research/probe` cannot import the package located under `tools/` without setting a module path. The documented `tools/hsi/validate.py --probe` is neither the implemented option (`--probe-only`) nor a complete invocation: the CLI requires `--repo` and `--game-dir`. CLAUDE.md has the correct working-directory/module form.

**Fix:** replace the prerequisite snippets with the actual `cd tools` module invocations, correct relative paths and required flags. This is documentation correction, not a need to change the tools' interfaces.

**Cheap check:** check the documented argument vectors against each argparse parser from the stated working directory, then run the corrected read-only validation before boot.

## 2. Formula and replay findings

I found no verified mismatch in the implemented vanilla numeric constants, state cap/standing/else-if branches, unrecognized gate, goal severity/clamp values or subject-block membership. Relevant comparisons are `tools/hsi/constants.py:4`–`:45` and `tools/hsi/formula.py:22`–`:63`, `:76`–`:97` against vanilla `common/defines/00_defines.txt:1000`–`:1006`, `:1113`–`:1175`, `common/script_values/00_infamy_values.txt:1`–`:285`, `common/script_values/00_diplomacy_values.txt:1068`–`:1073` and the named goal files. All listed goal types' subject block membership was checked against their scripts. This is a bounded source comparison, not engine-order verification. H1 still needs the repaired captures/gate; H2 and continuous decay remain approved assumptions.

### F1 — MINOR — Emission thresholds the rounded balance instead of the finished balance

**Repo:** `tools/hsi/generate.py:89`–`:94`.

**Claim:** balances in roughly `[0.045, 0.05)` can be emitted although spec §7 says to emit only finished balances ≥0.05, then round their values.

**Evidence:** a read-only fixture computation with a pending accrual on 1835-10-23 and a nominal charge `0.046 + 70*5/365.25` produced a horizon balance `0.04599999999999993`, then an emitted Standard entry `EGY: 0.05`. The code rounds before testing `final >= EMIT_MIN`. Vanilla `common/defines/00_defines.txt:1000`, `:1001`, `:1006` supplies balance bounds and base decay; it does not supply this project-specific emission threshold. This disagrees with the approved output contract, not a vanilla multiplier.

**Fix:** compare the unrounded replay balance with 0.05; round only the value of an eligible entry. Fix the emission code, not constants.py or the fixture operands.

**Cheap check:** finished balances 0.0449, 0.046, 0.0499 must be omitted; 0.05 and 0.0501 must be emitted. Compare raw horizon rows as well as output tables.

## 3. Ledger, generator, validator and save-checker findings

### L1 — MAJOR — A surviving holder may opt into the absent-actor modifier fallback

**Repo:** `tools/hsi/ledger.py:167`–`:170`; `tools/hsi/generate.py:29`–`:33`.

**Claim:** only one direction of the modifier-source invariant is enforced. A goal with a real holder tag and `general_mult_source=none` silently gets both generation modifiers zero.

**Evidence:** replacing fixture `g_pending.general_mult_source` with `none`, keeping EGY's tag, passes `validate_ledger()`. Its Standard table changes from EGY 5.42 to 5.75. Spec §5 permits `none` for actors without a 1836 tag, and requires measured data for present actors. Vanilla applies the root's unrecognized modifier at `common/script_values/00_infamy_values.txt:277`; the general generation modifier is defined at `common/modifier_type_definitions/00_modifier_types.txt:409`–`:424`. This is not a reason to change either constant or historical discount choice.

**Fix:** require `measured_1836` whenever the holder tag is present, and `none` when absent. Validate required country modifier fields before computation. Fix the ledger invariant/source declaration, not constants.py.

**Cheap check:** the mutation above must raise `LedgerError`; add a genuinely absent holder whose zero-modifier accrual still causes a surviving victim's reduction, as required by the spec.

### L2 — MAJOR — Manifest verification binds whatever was listed, not the required evidence set

**Repo:** `tools/hsi/measurement.py:179`–`:210`; `tools/hsi/generate.py:139`; `tools/tests/test_generate.py:23`–`:26`.

**Claim:** a manifest can omit system.log, the tooltip transcript, screenshots and playset evidence and still be accepted. Unlisted files inside directories are also invisible to the unexpected-file check.

**Evidence:** the successful end-to-end test itself writes only `debug.log` and `engine.txt` to its manifest. `verify_manifest()` compares top-level file names and hashes of supplied entries; it never enforces the named evidence required by spec §7. `engine.txt` is not interpreted to check the claimed measurement version, either. Recursive screenshots can be listed, but recursive unexpected files are not enumerated. Duplicate manifest names overwrite previous entries in the dictionary.

**Fix:** distinguish generic digest checking from measurement acceptance. Require the measurement artifact set and capture-specific screenshots, validate version/run provenance, define the allowed saves exclusion, enumerate other evidence recursively, and reject duplicate/noncanonical entries. A current-input hash cannot establish what vanilla files were used by a different measurement run.

**Cheap check:** omission of each required artifact, an unlisted nested screenshot and duplicate manifest names must fail measurement acceptance. A small generic manifest test may still exist, but must not stand in for the production gate.

### L3 — MAJOR — Derivation output omits the component and goal-processing intermediates

**Repo:** `tools/hsi/generate.py:35`–`:44`, `:68`–`:73`, `:165`–`:168`.

**Claim:** `derivation.csv` contains final charges and timeline steps, not the promised full derivation.

**Evidence:** the writer has only `rule, actor, kind, goal_id, date, before_decay, after_decay, delta, after_event, value`. There are no component IDs/slice contributions, caps, standing/predicate multipliers, per-state floor values, raw goal subtotal, subject multipliers or S/C/G/R/F running values. `goal_inputs()` calculates then discards component construction details, and the charge row retains only `nominal_charge`. Spec §7 expressly requires every component, intermediate goal charge and replay event/balance step. Vanilla's stages are independently visible in `common/script_values/00_infamy_values.txt:39`, `:77`, `:124`, `:172`, `:195`, `:208`, `:258`, `:281`, and subject stages in `common/war_goal_types/03_conquer_state.txt:64`–`:93`.

**Fix:** retain and serialize the actual intermediate computations, their component/slice identities and chosen stage order. Keep raw and emitted balances separate. This is a generator/output fix; do not reverse-engineer intermediate numbers from rounded output.

**Cheap check:** a multi-slice component and a multi-component subject goal must produce rows from which their final nominal charge can be independently reconstructed, then reconciled to timeline and emission rows.

### L4 — MAJOR — Static validation can say OK for absent content and omit the binding checks

**Repo:** `tools/hsi/validate.py:65`–`:85`.

**Claim:** missing roots/files and omitted measurement arguments turn required checks into an empty successful validation. Probe rule flags are never checked, even with a game directory supplied.

**Evidence:** a read-only invocation of `validate.main()` with a nonexistent repo/game path and `--probe-only` prints `validate: OK` and returns 0. Missing roots are filtered away at `:76`. Full mode checks rule flags only if the effect exists and checks header/manifest only if both optional arguments are supplied. Neither metadata nor shipped hook is required. In probe mode it skips rule validation entirely. Spec §9 static acceptance requires the hashes and manifest, and vanilla's actual flags are at `common/game_rules/00_game_rules.txt:97`–`:117`.

**Fix:** require the files appropriate to each phase and validate the game directory. Full generated-mod validation must require measurement/fixture inputs and the shipped metadata, hook and effect. Validate flags in the probe too. Keep the stated limitation that BOM/braces are not an engine grammar checker.

**Cheap check:** nonexistent probe, missing hook/effect, one omitted binding argument and a misspelled probe flag must each exit nonzero. Invoke header validation on a generated test artifact, mutate a listed evidence file and a generator source independently, and require failure.

### L5 — MAJOR — Non-finite infamy/tolerance values can pass save acceptance

**Repo:** `tools/hsi/savecheck.py:98`, `:102`–`:129`, `:136`.

**Claim:** the save path bypasses the project's finite-number refusal, and tolerance is not constrained by the spec's acceptance bound.

**Evidence:** replacing `infamy=2.29` with `infamy=nan` in the synthetic EGY save yields no problems for the Very Low table. Both `got <= 0` and `abs(got-want) > tolerance` are false for NaN. Separately, passing `tolerance=nan` accepts a doubled EGY value 4.58 for expected 2.29. A large finite tolerance can likewise hide doubled application. Spec §7 refuses non-finite numbers; §9 requires a finite tolerance below half the smallest emitted amount. Vanilla bounds infamy to 0–1000 (`common/defines/00_defines.txt:1000`–`:1001`).

**Fix:** reject non-finite/out-of-range save values and table values; require finite nonnegative tolerance strictly below the relevant half-minimum bound, with a stated policy for an empty table. Use observed storage precision to select a valid tolerance, not to bypass positivity/doubling checks.

**Cheap check:** NaN/±Inf in save, table or tolerance must fail with named reasons. A tolerance large enough to admit a doubled boundary entry must be rejected before comparison.

### L6 — MAJOR — The “structural” save reader accepts missing required records and incompletely validates structure

**Repo:** `tools/hsi/savecheck.py:14`–`:69`, `:92`–`:100`, `:124`–`:129`; `tools/tests/test_savecheck.py:99`–`:111`.

**Claim:** the parser is a brace counter/regex scanner, not a complete structural validation of the save. It can return a green result for evidence that does not establish the required roster or lifecycle assertions.

**Evidence:** read-only mutations of the existing SAVE string each returned `[]` from `check_save()`:

- Remove the complete BOL country record: vanilla 50 is never required unless BOL happens to be parsed.
- Append an unclosed unrelated top-level block: the file is truncated/malformed but the individually searched blocks still parse.
- Change `other_flag` to a second `hsi_applied`: conversion to a set hides multiplicity.

There is no requirement that `country_manager.database` exists or is unique, no uniqueness check for country definitions, and no full-file balance/quote validation. `block_at()`, `children()` and `depth1_scalars()` count braces inside quoted strings as structure. `top_block()` tests column-zero text, not actual nesting depth. Missing zero-infamy country records are undetectable without a roster. Spec §9 requires every other country at zero except BOL at 50 and the reload guard present once. The one actual-save test is absent/skipped, so none of this establishes compatibility with a real 1.14.5 `-debug_mode` save; I did not read any prohibited external save.

**Fix:** parse a quote/comment-aware token stream, validate the entire save/container and required manager/database structure, reject duplicate country definitions, require BOL and a known bookmark/baseline roster, and inspect global-variable entries structurally including multiplicity and value. Retain a real permitted sample and run the failure mutations on it before acceptance is certified.

**Cheap check:** all mutations above plus an embedded quoted brace, duplicate definition, missing database and missing zero-infamy roster entry must fail appropriately. Check actual plaintext storage/header shape on the retained acceptance artifact; do not claim it from the synthetic fixture.

### L7 — MINOR — The documented vanilla lookup helper reports no language matches

**Repo:** `research/scripts/vanilla_lookup.py:25`–`:28`, `:43`, `:50`–`:55`.

**Claim:** this helper still reads a `traits` language representation that vanilla 1.14.5 does not use, contrary to CLAUDE.md's gotcha and the author script's corrected implementation.

**Evidence:** vanilla `common/cultures/00_cultures.txt:3221` has French `language = language_francophone`; Spanish at `:2668` and Mexican at `:13770` both use `language_hispanophone`. The actual helper invocation printed `FRA … langs=[]` and empty `shared_language_via` lists. It searches only for `traits = { … }`. `research/scripts/author_ledger.py:18` correctly reads the language field, so this finding does not imply the current CSV language flags were generated by the broken helper.

**Fix:** read the real `language` field in the lookup helper and preserve independent raw homeland/language truths in reported evidence. Correct the research helper, not constants.py or already generated CSVs by hand.

**Cheap check:** SPA against a Mexican homeland should report the shared hispanophone language; FRA should have a nonempty francophone language set.

## 4. False greens — regression cases the current suite misses

These are proposed tests and concrete wrong changes/data mutations, not claims that all proposed mutants were run. The preceding counterexamples were executed in memory; no repository implementation was mutated.

### T1 — `bom.py`

**Change:** encode ASCII with `errors='ignore'` while still writing the correct BOM and normalizing newlines. **Required test:** write a script containing `debug_log = "Kütahya — test"` and require the exact UTF-8 payload after one BOM. **Why green now:** `tools/tests/test_bom.py:4` and the probe/effect writers exercise ASCII text only. Byte preservation for non-ASCII script text is not checked.

### T2 — `constants.py`

**Change:** set `SHARED_LANGUAGE_BONUS_FACTOR` to −0.2. **Required test:** independently parse the vanilla define and compare, plus a language-only component with `language_bonus=True` and a hand-calculated result. **Why green now:** `tools/tests/test_formula_component.py:36` exercises the homeland bonus branch; its language bonus flag is bypassed by homeland precedence. The synthetic DIAG records have both bonuses zero. No test reads the actual defines to verify the constants.

### T3 — `formula.py`

**Change:** turn off `GOALS['regime_change'].subject_blocks` while keeping its severity/clamps. **Required test:** a loyal regime-change target and a rebellious one must receive the respective scripted ×0.25 raw multipliers, including both true. **Why green now:** `tools/tests/test_formula_goal.py:24` checks only regime-change clamp values; subject arithmetic at `:28` covers annex_country and liberation, and regime ordering fixtures supply a ready raw subtotal. The real ledger contains no regime-change goal. Add analogous arithmetic cases for the other goal types rather than relying solely on a table of booleans.

### T4 — `timeline.py`

**Change:** give refund a lower kind rank than reduction. **Required test:** all three event kinds on the same date must produce step rows in accrual/reduction/refund order with stable goal-ID ties under input permutations, including a bound-clamping case. **Why green now:** `tools/tests/test_timeline.py:35`'s name promises all three kinds, but its actual inputs are only a refund and an accrual. Other tests combine accrual and reduction separately. Negative deltas can commute in the final balance while the contractual derivation order is wrong.

### T5 — `ledger.py`

**Change/data:** retain a holder tag but choose `general_mult_source=none`; or change a slice owner to a syntactically valid nonexistent TAG and the state key to `STATE_NOWHERE`. **Required test:** refuse the first before computation; static pre-boot validation must resolve every planned state/owner slice and living holder against bookmark history. **Why green now:** `tools/tests/test_ledger.py:64` tests only the opposite missing-tag/measured-source direction, and the validator receives only definition tags. Current production slices were independently checked in this review, but the suite never checks the real ledger against vanilla history. Also add duplicate act/component, empty country-goal, bad type/standing and return-state-without-claim cases: the code contains these checks, but the “every refusal” claim is broader than the exercised cases.

### T6 — `probe_gen.py`

**Change/data:** use a fixture holder outside the ledger and a fixture state outside its slice list, or misspell a localization function inside the generated string. **Required test:** independently verify fixture guard/DIAG coverage and start STATE keys; resolve generated tokens/functions against engine documentation when available, then retain a real smoke-capture line for extractor compatibility. **Why green now:** `tools/tests/test_probe_gen.py:8` uses FRA, but only asserts its COUNTRY text, not its guard/diagnostics; no fixture-target slices are supplied. The tests assert string fragments, not engine grammar or localization evaluation.

### T7 — `measurement.py`

**Change/data:** remove all diagnostics or the whole last sample, mix dates within a sample, or omit a required numeric field. **Required test:** reject each incomplete/unaligned receipt and run diagnostics on every complete sample; validate schema and legal numeric codes. **Why green now:** `tools/tests/test_measurement.py:50` checks missing last-sample slices/countries, not participant diagnostics, configured sample completion or start receipts. The synthetic log's dates are always aligned. Add consistency checks between printed raw quantities, denominators and weighted shares so a coordinated bad logger cannot supply internally unrelated operands.

### T8 — `ordering.py`

**Change/data:** wrong tick/holder/rule/sample metadata, a wrong multiplier-only severity line, quantized raw subtotal, or orders equivalent only on the ledger. **Required test:** B5–B7 counterexamples must either bind and fit correctly or refuse for a named ambiguity/input error. **Why green now:** `tools/tests/test_ordering.py:51` and `fixtures_ok.json` use invented exact running values, omit capture metadata and use an equivalence domain without fixture operands. Add loader refusals for non-finite operands, duplicate capture/stage IDs and a total not in final display position. Reading a `capture_plan` envelope also needs a defined JSON shape: plan Task 10 describes one, while the current loader only iterates a top-level list.

### T9 — `generate.py`

**Change:** drop victim reductions when the creator has no runtime tag, return early with `[]` diagnostics, round before thresholding, or omit all component-stage derivation rows. **Required test:** absent holder → surviving positive victim, complete expected DIAG coverage, F1 threshold boundaries and a reconstructable multi-slice/multi-component derivation. **Why green now:** the end-to-end test at `tools/tests/test_generate.py:82` uses only tagged creators, and at `:96` checks only that the derivation file exists. The positive diagnostic test accepts the returned empty problem list without requiring an expected comparison count. No boundary balance test covers 0.046.

### T10 — `hashes.py`

**Change:** hash only `generate.py` as the generator source set, or omit one otherwise unasserted vanilla input. **Required test:** compare header key coverage with an independently enumerated required input set, then mutate each kind of source/input and require stale validation. **Why green now:** `tools/tests/test_generate.py:89`–`:91` asserts a few key presences, not exhaustive source coverage. Producer and validator call the same helper, so a shared omission stays self-consistent. Preserve conservative coverage of every war-goal file; do not reduce coverage merely to keep tests green.

### T11 — `validate.py`

**Change/data:** return success for an absent probe, skip hash verification, misspell a rule in probe mode, or leave an unterminated string with balanced outside braces. **Required test:** L4's phase-specific absence/binding/flag failures plus unterminated quoted-string rejection and an actual generated-header tamper test. **Why green now:** `tools/tests/test_validate.py:24` supplies one existing arbitrary script and only checks BOM/braces. No test calls `check_header()`. `check_braces()` does not require `in_str=False` at EOF. Also test dispatch coverage, not just flag spelling: a known flag wired to the wrong table is semantically wrong while static flag-name validation is green.

### T12 — `savecheck.py`

**Change/data:** NaN infamy/tolerance, a missing BOL/database/zero-infamy record, duplicate tag/guard, quoted braces or truncation after the searched blocks. **Required test:** L5/L6's explicit failures on a retained real plaintext sample as well as synthetic inputs, with a roster and bounded tolerance. **Why green now:** failure directions at `tools/tests/test_savecheck.py:67` mutate ordinary finite scalars; truncation at `:99` cuts through an already searched block, and global flags are tested only for membership. The real-save test remains skipped until evidence exists. Add a measured storage-precision assertion rather than assuming the target tolerance is valid for every serialization.

### T13 — Author/lookup research scripts and operational shell scripts

**Change:** restore traits-based language parsing in the author script; silently pick a newer unrelated playset backup or merge a stale probe script. **Required test:** author tables/CSVs must agree under the installed language representation, with hand-checked shared-language examples; the lookup helper must report the same language facts; fake-HOME boot/restore tests must pass B8's retry/failure cases. **Why green now:** none of these scripts is exercised by the pytest suite. Tests operate on a separate synthetic ledger and never execute operational boot/restore behavior. Keep game launching excluded from these tests.

## 5. Owner decisions — choices, not defects

The accepted fixed-snapshot reconstruction, historical claims/standing/adjacency/interest judgments, composition from whole 1836 slices, holder=creator restriction, absence of Nationalism bonuses in historical mode, base continuous decay, canonical same-day ordering, one claim/resolution per goal, no primary-demand surcharge, post-horizon exclusions and unmeasured H2 remain the approved model. I have not treated their approximation error as a code defect.

Likewise, pending Ladakh/Belgium mappings, Cambodia's subject predicate choices, Bolivia being computed but never emitted, and the stated excluded historical candidates are owner judgments. Current vanilla tags/slices and author-table transcription check out structurally. I did not obtain external historical evidence for the precise territorial coverage of any slice, so that coverage is not independently certified by this review. A particular whole-slice boundary must still be justified by its source; the runtime ownership check cannot supply that judgment.

The Low/High/Very High unbooted dispatch residual remains accepted. Shipped metadata/hook/README creation and first generation are Task 13, still pending; their present absence is not itself a completed-task defect. When created, they must be required by full validation as L4 describes.

The next capture design must decide whether D remains the specified Conquer State fixture or is an explicitly accepted alternative. Numeric boundaries, nonzero FRA modifier, actual code-side target eligibility, UI formatting and calculation/display ordering must be observed, not asserted from the current population guesses. No promise is made here that three months will satisfy 2% stabilization; retain the approved refusal if they do not.

## 6. Verdict

**FIX BEFORE BOOT** — the planned B and D captures are unavailable, fixture states are not measured, and restoration/evidence gates do not protect the owner's one-shot session.

Ordered changes required before that boot:

1. Repair B and D eligibility and fallbacks, resolve D's goal-type contract, and statically audit every capture's prerequisites and intended discriminating boundary (B1/B2).
2. Make the capture plan machine-readable, add all fixture slices and independent fixture/BOL participant coverage, regenerate the probe and verify its exact generated file set (B3).
3. Repair fixture precision, typed observed quantities, tick-0 binding and fixture-inclusive equivalence; add the discriminating counterexamples before relying on the ordering gate (B5–B7).
4. Establish strict start/monthly receipts and diagnostic coverage/alignment checks, including every sample, and make pre-quit completeness verification part of the procedure (B4).
5. Bind backup/staging/restore/collection to one run, preserve the staged playset and logs before restoration/overwrite, and pass fake-HOME retry/failure tests (B8/B9).
6. Correct the prerequisite commands and make probe validation require its actual files and known flags; enforce the holder modifier-source invariant and required measurement evidence set (B10, L4, L1, L2).

F1 and L3/L5/L6/L7 must also be corrected before generation/acceptance is certified; they do not require another probe boot if the repaired boot retains complete evidence. Runtime script loading/localization and stabilization still need an early, explicit observation checkpoint during the authorized boot; this read-only review cannot certify them in advance.

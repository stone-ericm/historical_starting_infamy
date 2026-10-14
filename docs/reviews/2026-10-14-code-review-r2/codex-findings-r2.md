# Historical Starting Infamy — code review R2 (HSI-C2)

## 0. Disclosure

No injected memory summary was visible. No memory file or shared context corpus was read or used. The session identifies the model as Codex based on GPT-6; the precise variant/effort is not visible.

Reviewed `build/v1` at `b503dd0105fbbfd507f303e602086703704319cd`, including changes after `dfed034`. Read the log/diff before the R1 triage, then the changed implementations, procedures, tests and relevant vanilla files. The initial status already contained untracked `docs/reviews/2026-10-14-code-review-r1/`; it was left untouched.

Ran the specified capture audit exactly, without `--write-config`: it exited 0 and printed AUDIT OK. Attempted the exact suite command `cd tools && uvx pytest -q` twice; the retained completion result exited 2 because uvx tried to fetch pytest index metadata and DNS/network access failed. The first tool call yielded without a retained completion result. No suite completion/pass result is claimed for this round, and no network data was retrieved. I did not broaden the allowed test command, launch a game, execute boot scripts independently, use herdr/agents, or access anything under the Victoria 3 user directory outside this repo.

Read-only Python checks verified the renderer matches every committed generated probe file, 5,552 effect lines, 32 configured fixture slices, BOM/braces/rule names, current ledger validation, the new emission boundaries, the corrected language lookup, Russian fallback coverage, and the receipt/oracle counterexamples below. No computation scratch files were needed. Only this deliverable was authored.

Vanilla paths below are relative to `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`; other paths are repo-relative. Engine effect/trigger/link registries were not available among the permitted inputs. Source comparisons support the new state `ScriptValue`/variable reads in their state scope; the shared script chain evaluates `siv` immediately before logging. The log envelope remains `HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v…`. The monthly guard and fixture-holder loop now match the configured participant sets. I found no new unsupported script construct, but neither file size nor source comparison certifies engine loading, numeric formatting, pulse dates or stabilization. Those still require the actual boot.

## 1. Round-1 disposition

“NOT FIXED” below includes intentional deferrals. Acceptance of a deferral means the implementation can wait; it does not certify that quantized captures will necessarily determine one order class.

| R1 | Disposition | Applied evidence and deferred-item ruling |
|---|---|---|
| B1 | FIXED | The specific SAR relation blockers are removed: B now names MAS/Algiers and BEL/Flanders (`research/measurement/capture-plan.json:34`–`:52`). Neither has a France truce or French claim in the inspected history. Full eligibility certification is still overstated by the audit, as N3 explains. |
| B2 | PARTIAL | The nonexistent SIC release and blocked AUS/LOM are gone (`capture-plan.json:89`–`:109`). Optional liberation D is a recorded scope choice. Its runtime movement conditions and numeric usefulness remain unverified; “optional” permits another capture boot if the measured domain needs it. See N3/N7 and the risk ranking. |
| B3 | PARTIAL | Fixture slices, independent fixture/BOL guard membership and fixture-holder DIAG coverage are added (`tools/hsi/probe_gen.py:89`–`:94`, `:137`–`:149`). Current config matches the audit. Cmax/RUS is deliberately excluded and has only 5 of 73 required STATE slices through other inputs (N2). |
| B4 | PARTIAL | Required start/monthly keys and DIAG pairs are checked (`tools/hsi/measurement.py:143`–`:194`), and generation runs every monthly oracle (`tools/hsi/generate.py:149`–`:159`). State operands are local to each DIAG, but its modifier is not (N1); receipt schema/window checks still give false greens (N4). |
| B5 | NOT FIXED — deferred | `tools/hsi/ordering.py:23`, `:46`–`:57`, `:88` still treats displayed raw subtotals as exact. **Accept deferring the interval fitter** if full displayed numbers/precision, all selected A/D nested state breakdowns, tick-0 COUNTRY/STATE records and capture identities are retained. Current instructions need N7's clarification, and RUS needs N2. Monthly records cannot replace tick-0 operands. |
| B6 | NOT FIXED — deferred | The fixture dataclass/loader still omit capture binding and typed multipliers (`tools/hsi/ordering.py:13`–`:26`, `:83`–`:89`). **Accept schema implementation after the boot**, provided screenshots preserve labels, quantities, display order, holder/target/goal, date/rule context, and the chosen candidate is recorded against the exact run. N6/N7 supply the missing collection/capture requirements. |
| B7 | NOT FIXED — deferred | Equivalence still covers only ledger GoalInputs (`tools/hsi/ordering.py:59`–`:64`, `:73`). **Accept algorithm deferral**; it needs the same retained fixture operands, not a different boot solely to change the code. A missing/non-discriminating D can still require a further observation; no algorithm can manufacture it. |
| B8 | PARTIAL | Clean staging, active receipt and post-launch EXIT restore replace the old latest-backup restoration (`boot_probe.sh:12`–`:35`; `restore_playset.sh:14`–`:24`). Pre-launch rollback/integrity and archive-identity gaps remain (N5/N6). |
| B9 | PARTIAL | Staged playset JSON is now retained and collected, and a live count/schema checkpoint exists (`PROCEDURE.md:24`–`:47`). Collection still chooses the latest archive and copies current source config, and does not preserve a pre-quit log copy (N6). |
| B10 | FIXED | Prerequisites use the actual module working directory, relative paths and flags (`PROCEDURE.md:7`–`:9`). There is a separate persistent-shell cwd issue later in the procedure (N8). |
| F1 | FIXED | `tools/hsi/generate.py:61`–`:66`, `:96`–`:104` threshold the unrounded balance. Read-only checks omit 0.0449/0.046/0.0499 and emit 0.05/0.0501. `tools/tests/test_generate.py:103` adds the boundary cases. |
| L1 | FIXED | Both modifier-source directions are enforced (`tools/hsi/ledger.py:169`–`:173`). The real ledger validates; changing a tagged holder to `none` is refused in a read-only mutation. |
| L2 | NOT FIXED — deferred | Manifest checking remains generic (`tools/hsi/measurement.py:249`–`:270`). **Accept enforcement after collection, before generation.** Retain debug/system/error/extract, all required screenshots/transcripts, actual engine version, staged playset, exact run receipt/config and capture plan. The last items must be captured from the launched run, not reconstructed from mutable source afterward (N6). |
| L3 | NOT FIXED — deferred | Component/stage derivation rows remain absent (`tools/hsi/generate.py:35`–`:44`, `:175`–`:178`). **Accept deferral before first generation**: the complete measured shares/modifiers plus ledger/constants are sufficient to serialize the intermediates later. No additional game observation is needed beyond fixing the operand coverage/timing defects above. |
| L4 | FIXED | Missing roots/rules/empty file sets fail; probe flags are checked; full mode requires shipped files and bindings (`tools/hsi/validate.py:75`–`:99`). Read-only missing-root invocation exits 1. This remains a bounded static checker, not engine grammar validation. |
| L5 | NOT FIXED — deferred | Save values/tolerance still lack finite/range validation (`tools/hsi/savecheck.py:98`, `:119`–`:129`, `:136`). **Accept deferral before acceptance**; no extra probe tooltip/record is needed. |
| L6 | NOT FIXED — deferred | Missing BOL/roster, duplicate guard and limited structural validation remain (`tools/hsi/savecheck.py:14`–`:69`, `:92`–`:100`, `:124`–`:129`). **Accept deferral before acceptance certification**, using a retained real plaintext sample, which can come from the already planned acceptance baseline. A general parser for every save subsystem is unnecessary; a reader of the protected blocks must still respect quoted strings, and roster checks do not repair a misparsed block. The current probe screenshots/logs alone are not save-format evidence. |
| L7 | FIXED | `research/scripts/vanilla_lookup.py:26`–`:29` now reads `language`. Actual read-only runs report FRA francophone/Wallonian sharing and SPA/Mexican hispanophone sharing. |

I accept the triage's central disagreement: B5–B7's **code** need not precede the capture boot. The requirements that cannot be deferred are preserving the actual operands, contextual screenshots and run identity, and collecting a genuinely discriminating fixture when the domain requires one.

## 2. New findings

### N1 — MAJOR — DIAG remains dependent on a differently timed COUNTRY modifier

**Repo:** `tools/hsi/probe_gen.py:71`–`:79`, `:148`; `tools/hsi/generate.py:55`; `tools/hsi/measurement.py:179`–`:189`.

**Claim:** the advertised self-contained diagnostic lacks the holder's unrecognized-generation modifier. Oracle A still borrows that value from the sampler's COUNTRY record, despite deliberately permitting different country pulse dates.

**Evidence:** new DIAG records contain shares/standing/base/siv, but no `unrec_mult`; the generated first DIAG confirms that omission. `diagnostic_check()` reads `snap.country(holder)['unrec_mult']`. Vanilla `common/script_values/00_infamy_values.txt:258`–`:277` reads the root modifier while calculating that state value. In a constructed, read-only sample with GBR's diagnostic on April 9 using the original −0.3 modifier and the sampler's April 1 COUNTRY record at −0.4, receipt checking returns `[]`, while oracle A reports `generator 7.7481 vs engine 9.0394` for GBR/HEDJAZ/HDJ. This demonstrates a wrong refusal for a correctly evaluated differently timed state value; it is not a claim that that modifier actually changes during this campaign.

**Fix:** materialize/log the root modifier with each DIAG in the same country-rooted evaluation block as `siv`, and consume that operand in oracle A. Require it in the DIAG schema. Keep the sampler's aligned COUNTRY values for reconstruction, as intended. Do not solve the problem by substituting another sample or changing constants.

**Cheap check:** different per-root firing dates and modifiers must pass when each `siv` agrees with its own recorded modifier; perturb that local modifier and require a named oracle mismatch. Add an unrecognized-owner case so the test actually exercises the gate. This additional operand must be captured in the probe boot; it cannot be recovered at its original firing time afterward.

### N2 — BLOCKER if the fallback is used — Cmax/RUS has deliberately incomplete fixture coverage

**Repo:** `research/measurement/capture-plan.json:79`–`:84`; `research/scripts/capture_audit.py:160`–`:161`; `research/measurement/capture-plan.md:5`–`:6`, `:37`.

**Claim:** the procedure offers Russia as a usable Cmax fallback while suppressing its fixture records. That contradicts the promised complete tick-0/monthly evidence per candidate.

**Evidence:** Russia owns 73 state slices in the installed history. The union of ledger slices and the 32 configured fixture slices logs only five Russian slices: Armenia, Azerbaijan, Dobrudja, Kaunas and Vilnius. Thus 68 Russian STATE operands are missing. The audit test at `tools/tests/test_capture_audit.py:45` checks equality with `fixture_slices()`, which implements this exclusion, not equality with every candidate's actual priced slices. Oracle B can sometimes identify an above-max clamp without all those state operands, but that does not supply the required snapshot cross-reference or certify the deferred fixture-binding contract.

**Fix:** include every priced Russian slice, regenerate the probe/receipt expectations, or remove Russia from the authorized fallback list and explicitly require another complete Cmax candidate. An unchecked fallback must not be presented as interchangeable with Austria.

**Cheap check:** independently resolve each candidate's formula target states against history and compare them with generated STATE coverage in both start hooks and monthly samples. Russia must have 73/73 coverage if it remains offered. Do not derive both sides of the assertion through the same exception-bearing helper.

### N3 — MAJOR — AUDIT OK is narrower than the documented eligibility claim

**Repo:** `research/scripts/capture_audit.py:16`–`:20`, `:97`–`:131`; `research/measurement/capture-plan.md:10`, `:40`–`:50`.

**Claim:** the audit omits documented eligibility conditions and the procedure incorrectly says Regime Change has no interest requirement. Code-side eligibility remains a live risk, especially for Cmin.

**Evidence:**

- Vanilla `common/diplomatic_plays/diplomatic_plays.md:2` says `requires_interest_marker` defaults to yes. `dp_regime_change` at `common/diplomatic_plays/00_diplomatic_plays.txt:54`–`:67` does not disable it. Absence of the separate war-goal `requires_interest` setting is not proof that starting this play needs no interest.
- Regime Change explicitly carries `validate_regime_change` (`common/war_goal_types/20_regime_change.txt:12`). `common/defines/00_defines.txt:1107` bars ideological opinion above −5; `localization/english/diplomatic_plays_l_english.yml:163`–`:164` also documents the non-marginalized installable-IG requirement. Neither is checked or even flagged by this audit.
- D requires a potentially seceding movement with both popular support and activism: the latter is shown at `localization/english/diplomatic_plays_l_english.yml:160`, with protesting threshold 0.50 at `common/defines/00_defines.txt:312`. The plan/audit mention only 10% support.
- Make Protectorate carries `validate_subject_relation` and subject rank/type restrictions (`common/war_goal_types/16_make_protectorate.txt:15`; `common/subject_types/00_subject_types.txt:10`, `:32`–`:53`). The audit does not validate ranks. It also never reads `00_truces.txt`, or checks the Conquer State claim predicate at `03_conquer_state.txt:36`.

For the **current** candidates I checked those static histories: all targets are alive, independent and non-decentralized; FRA is independent/recognized; B has no French claim; none of the listed France-target pairs has a history truce. France owns relevant North African, Southern European and Western European slices. Ownership is a reasonable interest proxy: `00_defines.txt:1314` guarantees target involvement 1500 for ownership/claims, and `interest_tier_types.txt:34`–`:53` associates engaged interest with diplomatic plays. It does not prove the precise tick-0 tier. Austria shares Southern Europe with France; Russia does not share an owned region. These observations remove several concrete blockers, not the omitted runtime checks.

**Fix:** distinguish verified static eligibility, unresolved runtime conditions and numeric estimates. Parse/check the available truce/claim/subject rules and play-level interest default; emit named UNVERIFIED conditions for code-side regime/rank/movement checks rather than imply they passed. Require a valid Cmin/Cmax draft and its intended clamp observation before starting the observer phase. Preserve refused-goal tooltips.

**Cheap check:** mutate an otherwise passing candidate to add a France truce or claim and require failure; an unresolved regime-change condition must remain visibly unverified. Inspect the actual Cmin/Cmax eligibility tooltip at tick 0 before investing in the remainder of capture. I am not claiming any specific C candidate is definitely illegal without the engine's ideological/clout values.

### N4 — MAJOR — Receipt COMPLETE still admits missing required fields and an unexpected measurement window

**Repo:** `tools/hsi/measurement.py:140`, `:154`–`:198`, `:207`–`:212`, `:285`–`:293`; `tools/hsi/generate.py:149`–`:160`.

**Claim:** key presence is improved, but the live checkpoint can still certify evidence the generator cannot consume, or consume a later sample outside the configured three-month receipt.

**Evidence:** in-memory mutations of the updated synthetic log produced these results:

| Mutation | `check_receipt()` result |
|---|---|
| Delete `gen_mult` from every COUNTRY | `[]` |
| Delete `claim` from every DIAG | `[]`; later oracle raises `KeyError('claim')` |
| Change start_b RULE to Standard | `[]` |
| Give every DIAG a date in May 1840 | `[]` |
| Append a complete monthly sample 4 to a months=3 receipt | `[]`; `choose_snapshot()` selects 4 |

The DIAG required-field list omits its predicates/types; other kinds have no complete schema. `check_receipt()` only iterates required groups and never rejects extra groups/keys. `monthly_snapshots()`/`choose_snapshot()` then consume those unchecked extra groups. Sample identity/date consistency within one root's diagnostic firing is not checked. No expected capture rule is retained in the config/receipt. `build_snapshot()` can raise uncaught KeyError/ValueError for malformed fields/keys rather than a named receipt problem.

**Fix:** validate the full per-kind schemas, key arities, finite values and legal bool/type/interest codes; reject unexpected hook/sample/key sets and validate each root's firing identity/date within the boot. Require the configured last sample, not the last arbitrary group. Carry the expected capture rule into the receipt and verify start_b against it while preserving start_a as an independent observation. Keep oracle A validation distinct from mere record counting.

**Cheap check:** all rows above must fail for the intended reason, while different legitimate per-country pulse dates with local operands pass. Add tests for malformed keys and missing GLOBAL/COUNTRY fields that assert a useful INCOMPLETE message, not a traceback. Do not impose a guessed universal monthly firing day; use the actual recorded format and per-root dates.

### N5 — MAJOR — Rollback is installed after mutation, and restore validates backup integrity after copying it

**Repo:** `research/measurement/boot_probe.sh:16`–`:35`; `research/measurement/restore_playset.sh:14`–`:20`; `tools/tests/test_boot_scripts.py:65`–`:74`.

**Claim:** the new safety path covers binary failure but not failures during setup; restore can overwrite the playset before discovering that its backup is invalid, and cannot recover a missing destination file.

**Evidence:** playset replacement is at boot line 23; the EXIT trap is not installed until line 35. Failure opening/writing `receipt.txt` after that replacement, or interruption during this interval, exits with Q still enabled and no automatic restore. If the original backup copy fails, an empty `active/` can remain: a subsequent boot refuses it, while manual restore returns “nothing to restore.” In restore, line 14 hashes the current playset under `set -e`, so a missing/unreadable destination can prevent recovery despite a valid backup. Line 15 copies the backup before lines 17–18 inspect its expected digest. The bad-digest test checks error/active retention but never asserts that the destination was left untouched.

These are source control-flow findings; the prohibited independent shell executions were not run.

**Fix:** acquire an atomic active-run lock, complete and validate the backup, then install cleanup before any external mutation. Track setup phases so an abandoned pre-backup lock can be safely diagnosed/recovered. Validate backup digest/JSON and receipt binding **before** replacing the destination; a missing current destination must not block restoration. Stage/replace the JSON atomically and keep recoverable originals.

**Cheap check:** extend the existing fake-HOME suite with setup failure after Q replacement, failed original copy, missing destination, and a genuinely altered backup plus a live Q destination. Require automatic P restoration where possible and no overwrite from an invalid backup. No test should touch the real playset.

### N6 — MAJOR — Archive and collection are not bound to one unique launched run

**Repo:** `research/measurement/restore_playset.sh:23`–`:24`; `research/measurement/boot_probe.sh:21`–`:30`; `research/measurement/PROCEDURE.md:39`–`:45`.

**Claim:** exact backup selection is improved, but evidence identity can still be lost through same-second archive collisions, “latest archive” selection, mutable config copying and a check-only pre-quit checkpoint.

**Evidence:** archive destination uses seconds only. If that directory already exists, `mv active existing_directory` nests the new receipt as `existing_directory/active`; the printed archive path and collection's top-level receipt then refer to the older run. Current tests use separate fake run directories and do not test two fast launch failures in one run directory. Collection again uses `ls … | tail -1` instead of the receipt path emitted for this run. `probe-config.json` is copied from current repo source, not the staged run. The tree hash is also of the source after staging, not the staged copy. The live check preserves no log bytes; the only copy remains after quit, whose rotation behavior has not been measured here.

**Fix:** allocate a unique run ID at acquisition, archive without destination merging, and collect through that exact ID/path. Retain the staged probe config and capture-plan identity in the receipt before launch, hash the staged tree and copy those retained files afterward. Preserve a log/evidence copy at the successful pre-quit checkpoint as well as the final post-quit logs; keep attempts distinct.

**Cheap check:** two same-timestamp fake runs must yield separate retrievable receipts. Change repo config after fake launch and require collection to retain the launched config. Add an unrelated newer archive and ensure it cannot change the selected receipt. Simulate post-quit log replacement and retain the complete checkpoint copy.

### N7 — MAJOR — “First draft allowed” and one nested screenshot do not establish the intended fixture

**Repo:** `research/measurement/capture-plan.md:18`–`:27`, `:32`–`:45`; `research/measurement/PROCEDURE.md:20`–`:21`.

**Claim:** the procedure chooses by availability instead of observed discrimination, makes an invalid population-to-GDP inference for Cmin, and is ambiguous about collecting every constituent state's deeper breakdown.

**Evidence:** Cmin says that if Lucca lacks a minimum line, none of the larger targets will have one. `capture_audit.py:83`–`:87` assumes GDP share equals population share; actual GDP share is independent. A constructed legal arithmetic counterexample with capital standing and neutral interest has Lucca shares `(0.4,15)` → severity value 4.08 (no minimum), but Parma shares `(1.77,0.1)` → 1.374 (minimum binds). These are not measured Lucca/Parma values. Population ordering cannot eliminate the alternatives.

For A, the chosen MAS target has two states; MOR has four. Vanilla `localization/english/diplomacy_l_english.yml:2428` opens the country state list, `:2429`–`:2430` give its one-decimal entries, and `:2431` supplies each individual state's deeper breakdown. “Hover the … from N states line” is not an unambiguous instruction to capture each state's base/share/factor tooltip. One selected state's detail cannot preserve the other state's operands. The same issue applies to multi-state D. Contextual identity/date/rule screenshots are not specified explicitly, although the deferred schema needs them.

**Fix:** try the next Cmin/Cmax candidate when the first is unavailable **or does not show the required clamp**. For A and any useful D, capture each constituent state's nested breakdown, or an equivalent retained precise subtotal/operand observation. For Cmin near a boundary, retain its state detail too. Record candidate identity and keep at least the draft/holder/target/goal and tick-0 date/rule context with the screenshots. Preserve unsuccessful/out-of-range observations, but do not silently call them a discriminating fixture. Optional D may still be skipped under the recorded owner choice.

**Cheap check:** a procedural rehearsal with “first draft legal, wrong boundary; second draft legal, correct boundary” must select the latter. For a two-state A, the capture inventory must contain both state breakdowns plus the full goal breakdown and context. This supports deferring B5–B7 without losing irreplaceable observations.

### N8 — MINOR — The documented blocks change cwd without restoring it

**Repo:** `research/measurement/PROCEDURE.md:28`, `:37`–`:47`.

**Claim/evidence:** the live checkpoint ends in `tools/`. If the next collection block is pasted into that same shell, its relative `research/measurement/…`, `.run/…`, `research/probe/config.json` and subsequent `cd tools` resolve under `tools/` and fail or create the wrong destination. Prerequisites correctly return to root, but these blocks do not. Independent Codex command cells happen to avoid the issue; the document does not require separate shells/root cwd for each block.

**Fix:** bind an explicit repo path and cwd for each block, or run the module commands in subshells that leave the caller's cwd unchanged. Use the exact archived receipt from N6. Update the boot window's “step 6” collection reference to the actual step 7.

**Cheap check:** run the documented checkpoint and collection sequence in one fake-home shell inside the operational test harness and assert the root measurement destination is used.

### N9 — MINOR — Audit estimates conceal neutral modifiers beyond the declared GDP approximation

**Repo:** `research/scripts/capture_audit.py:82`–`:87`, `:132`–`:145`; `research/measurement/capture-plan.json:5`.

**Claim:** estimates described as the vanilla formula with a population/GDP proxy also hard-code interest tier 3, unrecognized modifier 0 and no shared-language/bonus calculation. Adjacent is taken directly from the candidate, not derived from geometry.

**Evidence:** France's history applies tier-1 technology (`common/history/countries/fra - france.txt:5`), which researches era 1 (`common/scripted_effects/00_starting_inventions.txt:5`), including Colonization's −0.1 unrecognized modifier (`common/technology/technologies/30_society.txt:245`–`:251`). All A candidates and B/MAS are unrecognized. Holding the audit's other proxy operands fixed, their unfloored state sums must therefore be multiplied by 0.9, unlike the audit's zero-modifier calculation. Interest tiers can change costs by +25%, +10% or −20% (`common/script_values/00_infamy_values.txt:208`–`:255`); owning a region is not synonymous with tier 3 or tier 5. The arithmetic for caps, current-owner standing, severity and [3,10] clamp is otherwise correct under its chosen operands. Cmin's three Emilia slices are each their owner's incorporated capital, correctly ×2; released states correctly retain the current opponent's standing, not the future release's capital standing.

**Fix:** state all proxy assumptions, use the statically established holder modifier, and report conservative ranges for unknown GDP/interest values where appropriate. Mark literal adjacency as needing the actual factor-line observation. Do not edit constants to match the audit estimate.

**Cheap check:** an unrecognized target under a recognized Colonization holder must receive the discount. Test tier 2/3/5 sensitivity and separate true static eligibility from boundary confidence. The current wide-margin A/Cmax choices need not be replaced solely because their estimates move.

## 3. Capture-plan risk ranking and candidate audit

**Most at risk overall: D/GBR→WLS. Most at risk among mandatory captures: Cmin/LUC.** D needs a sufficiently active secession movement as well as a useful numeric boundary; Cmin needs code-side regime eligibility, which the audit never examines.

The following ranking concerns capture success, not historical ledger judgments. Every listed target is alive and independent in the inspected bookmark history; none is decentralized. France has no listed truce with any candidate. For B, Algiers/MAS and Flanders/BEL exist, have no French claim and pass the below-cordial relations test. Current opponent tags for the release states are correct, and WLS/LIT/POL do not already own bookmark territory.

| Risk order | Candidates | Verified facts and remaining risk |
|---|---|---|
| 1 — optional D | GBR/WLS; RUS/LIT; PRU/POL | Release definitions exist at `common/country_creation/00_releasable_countries.txt:108`, `:151`, `:347`. Relations are −20/0/−20, no France truces/overlords. Wales is GBR-owned Western Europe, where France owns states; Lithuania is two unincorporated RUS slices; Prussia owns the three required Polish release regions. Runtime movement/activity/support and relevant interest remain decisive. History seeds an Irish movement in GBR (`common/history/political_movements/00_movements.txt:210`), a Polish one in RUS (`:164`) and a Polish one in PRU (`:161`), not explicit Welsh/Lithuanian ones. This makes the first two especially speculative; automatic initial movement creation was not measured, so absence of explicit seeding is not proof of impossibility. Prussia's seeded movement still has unmeasured activism/support, and its proxy charge is well above the floor-sensitive range. |
| 2 — mandatory Cmin | LUC, PAR, MOD | All have distinct incorporated capital slices of Emilia, owned-region interest proxy through French Corsica, no subject/truce obstacle and no regime-play relation blocker. History gives reactionary politics (`common/history/countries/luc - lucca.txt:6`, corresponding PAR/MOD `:6`), while France's government contains its Industrialist ruler and added Intelligentsia. Actual ideological opinion and an installable non-marginalized IG must be observed, not inferred from those labels. The population/GDP proxy gives 11.6/16.9/19.5 raw, suggesting a minimum case but not proving actual GDP or eligibility. Try every alternative if necessary (N7). |
| 3 — Cmax fallback | RUS | Numeric ceiling is robust, but interest/default play eligibility is unresolved and 68 priced slices are unlogged (N2). It is not currently a complete fallback. |
| 4 — mandatory Cmax primary | AUS | Independent recognized target; relations 20 do not block this particular play. Austria owns Southern European states where France has the ownership interest proxy, so “no interest anywhere” is not established. Code-side regime conditions still require inspection. A conservative population-source computation with GDP contribution 0 and the maximum interest discount on every state gives raw ≈152.13, severity ≈15.21, still above max 10. This is a static arithmetic bound under the stated population source, not a measured tooltip. RUS has an analogous ≈501.29 raw bound. |
| 5 — B | MAS/Algiers; BEL/Flanders | Relations −50/−1; neither has a France truce, French claim or subject/overlord blocker. Relevant ownership proxies exist. The audit takes adjacency on trust. MAS shares the Algiers region with France's slice; BEL is France's geographic border candidate. The actual “Borders France by land” factor must be seen in the selected state's tooltip. The files do not independently certify the draft UI or province adjacency here. |
| 6 — A | MAS; MOR; CON | Independent unrecognized targets, North African ownership-interest proxy, no France truce. Protectorate rank/type validation remains a runtime check, though France's expected great-power status and these targets make rejection less likely. The audit's severity 0.5 and subject-free target choice are correct. Above-floor margins remain broad despite the omitted modifier/interest assumptions; record the actual ×0.50, nonzero holder modifier, rule line, all state entries and total. |

**Full-chain limitations:** `aggressive_diplomatic_plays_permitted`, valid subject ranks, regime ideological/clout conditions, activity/support of secession movements, actual interest tiers, any relevant code-side treaty/war/draft restrictions and UI availability cannot be promoted to measured facts by AUDIT OK. The inspected `common/history/diplomacy/00_truces.txt` contains NET–BEL, EGY–TUR, ASH–GBR, GRE–TUR and SIA–DAI pairs; none is a France candidate pair. French claims are absent on B's states (`common/history/states/00_states.txt:3123`, `:3953`). Existing play/release script checks and defined code-side refusals should be reflected in the audit or the tick-0 preflight, with a refusal screenshot when encountered.

## 4. Owner decisions

Optional liberation D and the possibility of a later tooltip capture are recorded choices. Accepting that choice means accepting that this boot may not settle floor placement; the ordering gate must still refuse genuinely different fitted classes. A per-state floor of 1 and absence of a Conquer State claim do not by themselves prove that every French charge exceeds 2; a complete domain argument would also need standing, modifiers, population/GDP, interest and adjacency. I am not reopening the recorded D ruling or asserting that a replacement Conquer State target has been verified.

GDP=population is a declared planning proxy, not a reconstruction input. Numeric guesses must not become transcription values. Unknown engine formatting, initial movement creation, pulse cadence and stabilization remain observations for the boot. If the configured third sample fails 2%, preserve the refusal rather than choose another sample.

The scope of the save reader can stay narrow. It need not parse every subsystem; it must reliably locate/read its protected data, reject missing/duplicate required records and apply bounded finite comparisons. The existing baseline/acceptance work can provide the real serialization sample without adding a mandatory probe save.

The deferred formula/output/save-checker code changes can follow the boot once their necessary evidence is retained. Conversely, deliberately missing observations, mutable run identity and unsafe restore paths are pre-boot defects, not reasons to defer more implementation.

## 5. Verdict

**FIX BEFORE BOOT** — local DIAG modifiers, complete fallback coverage and run-safe restoration/collection are still missing, and the capture/receipt checkpoints can certify incomplete or non-discriminating evidence.

Ordered changes required before the boot:

1. Capture and consume the DIAG-local unrecognized modifier; regenerate and independently verify the probe/receipt sets (N1).
2. Fully measure RUS if it remains the Cmax fallback, or replace/remove that fallback explicitly (N2).
3. Close setup/restore failure paths and allocate one unique, exactly selected run receipt containing staged config/plan; preserve a pre-quit evidence copy (N5/N6).
4. Strengthen receipt schemas, expected hook/sample sets and the start_b rule check; consume only the configured window (N4).
5. Correct the live capture instructions: observe required boundaries, try alternatives when they fail, capture each needed nested state breakdown and identity/rule/date context, and fix shell cwd handling (N7/N8).
6. Make audit/procedure eligibility claims match the checks actually performed, flag the documented runtime regime/movement/rank conditions, and disclose/correct the extra numeric proxies (N3/N9). Resolve mandatory Cmin/Cmax availability at tick 0 before proceeding to observer sampling.
7. Obtain a successful run of the authorized suite, including the fake-HOME shell tests and new regression cases; this review's dependency-resolution failure is not a test pass.


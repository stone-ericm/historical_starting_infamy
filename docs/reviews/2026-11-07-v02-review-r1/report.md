# Disclosure

No memory summary is visible in the supplied conversation, and I read no memory files, `MEMORY.md`, or conversation logs. Before the brief, I received the user-provided AGENTS.md instructions, including project status and engine gotchas; those are supplied prior context, not independently established facts. The preceding exchange contained only READY. I checked the claims below against repository files, both supplied vanilla trees, and executed checks. No other agents were used.

All review-created files and private-copy changes are under `.codex-review/v02-r1/`. No release was built, installed, launched, committed, pushed, or published. The repository's tracked working tree remains unchanged.

Paths below are repository-relative unless prefixed `V115/` or `V114/`, which mean:

- `V115/`: `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`
- `V114/`: `/Volumes/EORScratch/eor-tools/vanilla-1.14.5-build25629520/game/`

# Assessment

**No verified BLOCKER or MAJOR in the current shipped arithmetic or output. Three MINOR findings follow.** The tables reproduce exactly with the declared old measurement and new formula. A fresh 1.15 measurement could plausibly change emitted whole numbers by at least one; neither this review nor the proposed acceptance smoke boot establishes the size of that difference. Reusing inputs is an explicit approximation, so I do not classify that choice itself as a defect.

# Findings

## R1 — MINOR: disclose the cross-version inputs consistently, without implying population stability bounds GDP error

**Locations:** `README.md:22`; `docs/release/steam-workshop-description.md:18`; `docs/release/steam-workshop-description.bbcode.txt:14`.

The README correctly identifies the population/GDP shares as 1.14.5 measurements, but describes 1.15 history changes as “mostly Russian” and follows that with the small world-population change. The Workshop descriptions say the 1.15 calculation uses the game's day-one shares/modifiers/ranks without saying those inputs are reused from 1.14.5. Mentioning that the formula check ran on 1.14.5 does not disclose the input reuse. The README also does not say as explicitly that **modifiers and ranks**, as well as shares, come from that same old snapshot (`tools/hsi/generate.py:28`, `:35`, `:45`).

The GDP-related changes extend beyond Russian history: 1.15 adds copper (`V115/common/goods/00_goods.txt:314`), starts six levels of copper-mine ownership in the West Country (`V115/common/history/buildings/00_west_europe.txt:2317`), and changes pot-still inputs and grocery output (`V115/common/production_methods/01_industry.txt:194`). These are differences against V114, not just examples recalled from patch notes. They can affect the global GDP denominator even where the ledger state's own buildings did not change. Their actual day-one effect is **reasoning only**, not measured here.

**Failure scenario:** a Workshop reader interprets 12/2 as estimates using 1.15 economic inputs, or treats the 0.08% population difference as evidence the rounded outputs are stable. They are not demonstrably stable: changing only Aleppo's logged GDP contribution from 2.3 to 2.2 changes Standard Egypt from 12 to 11; changing Peshawar's from 3.9 to 4.0 changes High Punjab from 4 to 5. These are executed sensitivity checks, not claims those changes occurred in 1.15 (`research/derivation.csv:2`, `:178`, `:465`, `:598`; review `numerical_results.txt`).

**Cheap fix/check:** say in all three descriptions: “Priced with the 1.15 formula using 1.14.5 day-one population/GDP shares, modifiers and ranks. 1.15 economic changes were not measured; rounded values may differ with fresh inputs.” Narrow “mostly Russian” to the population/history comparison actually established. A fresh probe is the check if tighter accuracy is wanted; it is unnecessary merely to make the approximation honestly stated.

## R2 — MINOR: the historical capture audit combines the old tree with new arithmetic

**Locations:** `tools/tests/test_capture_audit.py:11`, `:23`; `research/scripts/capture_audit.py:101`, `:106`; `tools/hsi/formula.py:80`.

The test now correctly selects the 1.14.5 tree, but `estimate_state()` still calls `component_value()` without a version. Its default is 1.15. This is a concrete version leak outside the shipped-table generator.

I ran the audit on V114 and reran its calculations with an explicit `game="1.14.5"`. The Mascara A estimate changes from raw approximately 20.1 to 34.3. More decisively, optional capture D for Wales changes from `BOUNDARY?` (standard approximately 1.02) to `OK` (approximately 1.73). The committed test passes both because it accepts an optional capture with no passing candidate (`tools/tests/test_capture_audit.py:43`).

**Failure scenario:** someone audits or revisits the historical capture plan and concludes its floor fixture no longer works, based on a formula the historical boot never ran. This does not change the shipped tables or Oracle A.

**Cheap fix/check:** pass an explicit formula version through `Vanilla`/`estimate_state`, with the historical test selecting `K.MEASUREMENT_GAME`; keep current-tree audit use able to select 1.15. Add an assertion for the historical Wales estimate or its D status so changing only the tree cannot silently leave the arithmetic unpinned.

## R3 — MINOR: pinning the factor tests exclusively to 1.14.5 leaves a demonstrable 1.15 regression hole

**Locations:** `tools/tests/test_formula_component.py:28`, `:48`, `:63`; `tools/tests/test_shipped.py:26`; `tools/hsi/generate.py:73`.

Pinning observed old tooltips to the old formula is correct. However, the ordinary modifier/precedence tests were also pinned exclusively to 1.14.5, while the added 1.15 tests mostly cover baseline/caps/minimum. Oracle A intentionally exercises 1.14.5. The shipped-output recomputation checks final tables, which can conceal incorrect charges that subsequently decay to zero.

**Executed concrete mutant:** in a private copy only, replace `tools/hsi/formula.py:73`:

```python
if holder_type == "recognized" and c.owner_type != "recognized":
```

with:

```python
if game == "1.14.5" and holder_type == "recognized" and c.owner_type != "recognized":
```

The complete copied suite still reported **139 passed, 1 skipped**. This disables the unrecognized-target discount in every 1.15 calculation, contrary to `V115/common/script_values/00_infamy_values.txt:262`. For example, the real ledger's French Algiers component would become 4 instead of 3.6 (`research/derivation.csv:126`), but France still emits zero, so the shipped-table test stays green.

**Failure scenario:** a version-specific refactor breaks an inherited factor and the old engine oracle plus final-output test both approve it.

**Cheap fix/check:** parameterize the factor/precedence tests over both games, using above-floor operands. The review's `test_115_discount_review.py` independently expects `(4.6+3.9)*1.5*0.9*1.1*0.9 = 11.36025`: it failed on this mutant (12.6225) and passed after restoring the original formula. No production formula change is needed for this finding. The private formula was restored afterward.

# Independent vanilla and formula audit

I diffed every vanilla file named by the generated header, then compared the wider dependencies: defines, script values, all war goals, ranks, game rules, on-actions, history, country definitions, cultures, state/strategic regions, country creation, laws, technology, character traits/templates, static modifiers, power-bloc principles, goods, buildings and production methods. The complete file inventory and unified diffs are retained beside this report (`vanilla_changes.json`, `common_*.diff`, `map_data_state_regions.diff`). This is a file audit; closed-source engine arithmetic or initialization changes are **reasoning only** unless reflected in the logged old measurements.

The relevant changes and dispositions are:

| Change | Effect on this ledger / handling |
|---|---|
| Flat state baseline 5 becomes a floor of 1 for each share | Correctly implemented in `tools/hsi/formula.py:42`; V114 defines line 1121 versus `V115/common/defines/00_defines.txt:1080`, and `V115/common/script_values/00_infamy_values.txt:34`. |
| Conquer State supplies `infamy_ignores_claim`; Return State supplies `infamy_assumes_claim` | `V115/common/war_goal_types/03_conquer_state.txt:61`, `V115/common/war_goal_types/21_return_state.txt:61`, and `V115/common/script_values/00_infamy_values.txt:170`. The ledger validator already rejects conquest claims and requires return-state claims (`tools/hsi/ledger.py:183`), so no current charge is missed. The replica's claim boolean represents the effective historical condition on this restricted domain. |
| Annex gains the Russian-unification multiplier | `V115/common/war_goal_types/00_annex_country.txt:93`; only applies to `dp_unify_russia`. There are no annex-country goals or Russian-unification plays in the current ledger. No emitted-number effect; extending the model to that context would require another input. |
| Strait-access validity changes; ship-transfer defines disappear; an obligation/infamy threshold is added | None of these goals/actions is priced by this ledger. No numerical change required. |
| Rank file and game-rule file | Byte-identical between trees. Infamy rank coefficients and rule flags/multipliers remain correct (`V115/common/country_ranks/00_country_ranks.txt:29`, `:67`, `:125`, `:161`, `:196`, `:228`; `V115/common/defines/00_defines.txt:1081`). |
| Diplomacy script values | Other sections change, but the used interest factors/thresholds remain 0.25/0.1/-0.2 and 2/5 (`V115/common/script_values/00_diplomacy_values.txt:1163`). |
| On-actions refactor and additional startup effects | After-lobby hook still has the same documented new-campaign/rootless contract (`V115/common/on_actions/00_code_on_actions.txt:10`); mod registration remains additive (`common/on_actions/zz_hsi_on_actions.txt:4`). No dispatch change found necessary. |

I reread the define names used by the constants: world scale, weights, caps/slope, standing, homeland/language/claims/adjacency/unification, subject factors, goal minimum/clamps, refunds, victim reduction and decay. The baseline is the only changed numerical constant used here (`V115/common/defines/00_defines.txt:987`, `:1072`, `:1103`, `:1126`). The signs in `K.REFUND` and `K.VICTIM_REDUCTION` are intentionally converted to positive fractions, then negated when creating events (`tools/hsi/generate.py:127`).

The cap/floor ordering is correct for these constants: vanilla softens the excess above 10, floors each contribution at 1 and caps it at 15, then applies standing. The extra population floor before softening in vanilla has no additional effect: the soft-cap branch can only run above 10, already above the floor of 1. Thus `max(capped(x),1)` is equivalent here (`V115/common/script_values/00_infamy_values.txt:36`, `:51`, `:71`; `tools/hsi/formula.py:26`, `:48`). The per-state minimum is after all state factors, before summing goals and applying subject factors (`V115/common/script_values/00_infamy_values.txt:285`; `tools/hsi/formula.py:78`, `:136`).

Severity, goal clamp, general modifier, additive rank block, rule multiplier and final minimum retain the observed order (`tools/hsi/formula.py:147`). The final goal floor is justified by the unchanged define comment, not newly measured engine evidence (`V115/common/defines/00_defines.txt:1103`). No file-visible change in that order was found.

# Hand traces from the real derivation

These calculations use the recorded operands, independently of the replica's helper functions.

- **Aleppo:** population 2.1 and GDP 2.3 are above the floor and below the soft cap. Base `2.1+2.3=4.4`; homeland standing `×1.5`; shared language `×0.85`; neutral interest, no adjacency/claim; unrecognized Egypt does not receive the recognized-aggressor discount. Component `5.61`. Conquest severity 1, no clamp, general modifier 0, rank `1+0.4+0.2=1.6`; Standard charge **8.976** (`research/derivation.csv:2`, `:5`).
- **Ladakh:** shares 1.3 and 0.6 become `1.3+1=2.3`; capital `×2`; adjacency `×0.9`; component **4.14**. Tributary severity `×0.5`; general 0; Punjab aggressor +0.5 and declared unmeasured-target fallback -0.5 cancel; Standard charge **2.07** (`research/derivation.csv:184`, `:187`). This exercises the new GDP floor.
- **Dongola:** `(1.3+1.7)×0.5×0.85×0.9×0.8=0.918`; per-state minimum makes the component **1**. Its Standard rank block makes the goal **1.4** (`research/derivation.csv:32`, `:35`). This distinguishes the state floor from the goal floor.

**Whole Punjab balance:** Peshawar gives `(4.3+3.9)×0.9=7.38`, then rank `1+0.5-0.4=1.1`, giving 8.118 on 1834-05-01. After 92 days, `8.118−5×92/365.25=6.858588638`. Add Ladakh 2.07 on August 1: 8.928588638. Decay another 518 days: **1.837555099**, rounded half up to **2**. No refund/reduction applies to Punjab in this replay (`research/derivation.csv:178`, `:181`, `:497`, `:498`, `:499`).

Cross-check Egypt: the Sudan balance has decayed completely before the five Syrian conquests. Their Standard charges sum to **32.4704**; 1,522 days of decay gives `32.4704−5×1522/365.25=11.635355510`, rounding to **12** (`research/derivation.csv:459`, `:460`, `:464`, `:465`).

# Reused measurement: what is established and what remains unknown

The sum of uncommented history-pop sizes is **1,022,466,685 → 1,021,666,179**, a decrease of approximately **0.07829%**. All ledger slice population sizes remain unchanged, including Egyptian Syria, Punjab's Peshawar slice and Ladakh. Six ledger-state pop blocks change culture labels without changing sizes; for example Aleppo's slave culture changes from north_caucasian to circassian (`V115/common/history/pops/08_middle_east.txt:557`; exact diffs and totals in review `history_selected.txt:1`). The README's population statement is supported.

Among ledger-state building blocks, the changed one is Flanders ownership levels, 6 to 8 (`V115/common/history/buildings/00_west_europe.txt:5487`). The priced Egyptian and Punjabi state building blocks are unchanged. The ledger-state history change found is removal of the Armenian homeland from Azerbaijan (`V115/common/history/states/00_states.txt:6452`); regeneration of the authored CSVs against V115 is byte-identical, so no current authored language/homeland flag changes.

Country types, capitals and primary-culture lists for every ledger holder/victim are unchanged. Egypt/Punjab country-history files retain their starting technology/law setups (`V115/common/history/countries/egy - egypt.txt:2`, `pan - panjab.txt:2`); their rulers retain their traits (`V115/common/character_templates/country_egy.txt:20`, `country_pan.txt:20`). I found no direct new infamy-modifier source for these two actors. These checks do **not** prove identical GDP or engine-assigned ranks: rank thresholds depend on average/highest prestige (`V115/common/country_ranks/00_country_ranks.txt:3`, `:158`, `:193`).

Executed sensitivity checks, holding other inputs fixed:

| Perturbation | Changed output |
|---|---|
| Only the history-pop denominator change, continuously rescaled | No whole-number table changes. This does not emulate engine requantization. |
| Every GDP share ×0.99 | Standard Egypt 12→11; Low Egypt 4→3. |
| Every GDP share ×1.05 | Standard Egypt 12→13; High Punjab 4→5. |
| Aleppo GDP 2.3→2.2 only | Standard Egypt 12→11; Low 4→3; High 20→19. |
| Peshawar GDP 3.9→4.0 only | High Punjab 4→5. |
| Egypt one unrecognized rank lower | Standard Egypt 12→10. |
| Punjab one unrecognized rank lower | Standard Punjab 2→1. |

The computations are in `numerical_audit.py` / `numerical_results.txt`. **Reasoning only:** these perturbations are plausible magnitudes given economic initialization changes, but I am guessing about their actual direction and size on 1.15. They establish sensitivity, not a measured correction. Other countries remain absent throughout the tested ±10% uniform GDP-share scenarios; this is not an exhaustive error bound. A Standard smoke start showing 12/2 verifies delivery of the fixed table, not the repricing that produced it (`research/acceptance/ACCEPTANCE.md:14`).

# Verification and items found correct

- Original suite: **139 passed, 1 skipped**. The skip is the real acceptance-save test. The private-copy mutant suite also passed 139/1 after completing the private copy's supporting files; an initial incomplete-copy run failed only for missing capture-plan/boot-script files, not mutation assertions.
- Private generation against V115: **1,754 diagnostic records, three monthly samples, zero mismatches**; validation: **OK**. Generated `tables.json`, `derivation.csv`, effect and README are byte-identical to the checked-in files. The three ledger CSVs regenerated privately against V115 are also byte-identical.
- Every original effect header hash agrees with current generator sources, V115 hashed inputs and the named boot logs/config (`tools/hsi/hashes.py:6`, `:10`, `:18`; `common/scripted_effects/zz_hsi_effects.txt:2`). Both shipped scripts have BOMs and pass braces/rule-flag checks.
- The version split is internally consistent for the supplied inputs: Oracle A explicitly passes `K.MEASUREMENT_GAME` at `tools/hsi/generate.py:73`; both component derivation and raw charges use the 1.15 default at `:99` and `:108`. Downstream goal stages/timeline contain no separate state-base arithmetic. No hidden 1.14.5 pricing path was found in shipped-table generation. Version selection is configured in constants, not inferred from `--game-dir`; the current arguments/constants match, but arbitrary future trees are not automatically supported.
- The changed synthetic hand calculation in `tools/tests/test_generate.py:60` agrees with the fixture, and the old observed tooltip tests correctly pass `game="1.14.5"` (`tools/tests/test_formula_goal.py:71`). The new baseline tests distinguish addition from per-share flooring and exercise soft/hard caps. R3 describes the remaining coverage hole.
- Effect dispatch/guard and values match all five tables: Very Low empty; Low EGY 4; Standard EGY 12/PAN 2; High 20/4; Very High 28/7. Standard is the `else`, Bolivia is absent, and the guard is set even for the empty rule table (`common/scripted_effects/zz_hsi_effects.txt:68`). Vanilla Bolivia still receives 50 in unchanged country history (`V115/common/history/countries/bol - bolivia.txt:39`).
- Metadata is version 0.2.0 / supported 1.15.* (`.metadata/metadata.json:4`). `bash -n tools/build_release.sh` passes. Its descriptor now reads `supported_game_version` from the copied metadata and therefore emits 1.15.* (`tools/build_release.sh:65`). I did not execute the build. Its thumbnail source still points at the explicitly old Notorious screenshot (`:10`); consider replacing it after the author's new capture so the release image reflects the new balance.
- Acceptance's Standard 12/2 and empty Very Low expectations match the generated tables (`research/acceptance/ACCEPTANCE.md:14`, `:24`). Actual 1.15 delivery, reload, late-enable, multiplayer behavior and fresh engine inputs remain unverified here. The document dates the historical acceptance waiver and limits it to v1 (`:27`); this review grants no new waiver.
- README and both Workshop table/value lists agree with `research/tables.json`. Broader Workshop claims such as “everyone else” having exhausted their acts and refunding “the way the game does it” remain shorthand for a selected ledger and the declared victim-basis assumption, rather than independent historical/engine proof (`docs/release/steam-workshop-description.bbcode.txt:11`, `:14`; `README.md:3`, `:20`). R1 is the specific new cross-version disclosure correction.

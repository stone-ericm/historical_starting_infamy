# Historical Starting Infamy — design spec (v3.1)

**Status:** APPROVED by Eric on 2026-10-13 (v3.1) after three Codex review rounds (`docs/reviews/2026-10-13-spec-review-r1/`, `-r2/`, `-r3/`). Owner rulings on round 3 section 3: the v1 scope restrictions stand (holder = creator, whole slices only, `liberate_subject` and `reduce_autonomy` excluded); the declared counterfactuals stand (one claim and one resolution per goal, no primary-demand surcharge, continuous base-rate decay, canonical same-day order); H2 stays an assumption for v1; the Low, High and Very High dispatch branches stay a declared residual with static flag validation. Next: implementation plan.
**Target:** Victoria 3 vanilla 1.14.5 (Mac Steam install; `launcher-settings.json` reports rawVersion 1.14.5).
**Owner:** Eric Stone. **Repo:** `~/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/`.

## 1. Purpose

In vanilla every country except Bolivia starts 1836 with 0 infamy. Bolivia gets `change_infamy = 50` in its history file for the 1835–36 conquest of Peru. This mod extends that precedent to the whole roster: each country starts with the infamy that its conduct between 1816 and 1835 would have generated under the game's 1.14.5 rules, replayed as one decaying balance per country and read off on 1836.1.1.

The result is a **fixed-snapshot approximation**, not an exact simulation. The engine's formula is applied as written, but its inputs for 1816–1835 do not exist in the game, so they are reconstructed: 1836 population and GDP shares stand in for shares at the time of each act; 1836 technology and ruler modifiers stand in for historical ones; standing, claims, adjacency and interest are hand-authored historical judgments; decay runs at the base rate. Section 10 lists every approximation. The README states them.

A second purpose is documentary. The derivation is published in full, so the mod also answers "what does the vanilla formula say about the pre-1836 world?" The working expectation is that the world forgets fast: at 5 points per year most acts before about 1826 contribute nothing by 1836 unless a country's balance was kept up by later acts, and a typical peripheral state is worth about 8–11 points when taken. That result is acceptable and is not tuned toward earlier hand estimates.

## 2. Non-goals for v1

- No relations penalties toward the victims. Vanilla history already sets starting relations and truces for the recent wars.
- No change to the infamy formula, thresholds or decay rate.
- No in-mod game rule. The mod respects the vanilla `infamy_generation` rule only.
- No Workshop or Paradox Mods publication; that is a separate step requiring Eric's explicit approval.
- Bolivia is not touched; vanilla's 50 stands and BOL is excluded from every emitted table.

## 3. Engine facts the design relies on

Read from the 1.14.5 files on this machine on 2026-10-13. Paths are relative to the game directory.

| Fact | Where |
|---|---|
| `START_INFAMY = 0`, `MIN_INFAMY = 0`, `MAX_INFAMY = 1000`, thresholds 25 / 50 / 100, `BASE_YEARLY_INFAMY_DECAY_RATE = 5.0`; the infamy tooltip displays decay per week | `common/defines/00_defines.txt` 1000–1006; `localization/english/interfaces_l_english.yml` 6298 |
| Per-state formula (`state_infamy_base`, `state_infamy_value`, `country_infamy_value`) is entirely in script; standing is one else-if chain; homeland vs shared language and claim vs scripted unification are else-if pairs; the unrecognized multiplier requires root recognized AND state owner unrecognized or decentralized; per-state floor 1 | `common/script_values/00_infamy_values.txt` |
| Share constants: baseline 5, world share scale 10000, pop and GDP weights 0.375, soft cap 10 with slope 0.5, hard max 15 each; denominators floored at 1 | `00_defines.txt` 1113–1121; `00_infamy_values.txt` 1–26 |
| Standing multipliers 2.0 incorporated capital / 1.5 incorporated homeland of owner's culture / 1.0 incorporated / 0.5 unincorporated | `00_defines.txt` 1149–1152 |
| Aggressor factors: homeland −0.25, shared language −0.15, claim −0.75, scripted unification −0.7, adjacency −0.1 | `00_defines.txt` 1153–1163 |
| Interest-tier factors +0.25 (tier < 2), +0.10 (tier < 3), −0.20 (tier ≥ 5); tiers 3 and 4 neutral | `common/script_values/00_diplomacy_values.txt` 1068–1073 |
| `WAR_GOAL_INFAMY_MINIMUM = 1` floors both a state and "a war goal's total infamy after all multipliers"; loc has separate "Minimum of X for this war goal" and "Maximum of X" lines | `00_defines.txt` 1148; `diplomacy_l_english.yml` 2434–2435 |
| `infamy_severity` is a multiplier: loc `INFAMY_WAR_GOAL_SEVERITY_FACTOR` reads "×VALUE from war goal severity". Values: 0.5 protectorate / dominion / tributary / personal union, 0.4 transfer subject, 0.1 liberate country, 0.6 release as subject, 0.1 regime change with min 3 / max 10, 0.1 restore union; conquer state, return state and annex have none | `diplomacy_l_english.yml` 2433; `common/war_goal_types/*.txt` |
| Subject multipliers live INSIDE each goal's `infamy` script value as two independent multiply blocks: loyal subject (target is root's subject with LD < 25) ×0.25; rebellious subject (target is root's subject, root's play enemy, and initiated the play) ×0.25. Liberate country, release as subject, restore union lack them | `00_annex_country.txt` 53–92; `03_conquer_state.txt` 57–93; `13_liberate_country.txt` 45–56 |
| `liberate_country` and `release_as_subject` sum `every_releasable_state` of the target, "the states that would be released", not all of the target's states | `13_liberate_country.txt` 48–54; `38_release_as_subject.txt` 44–50; loc 2432 |
| `conquer_state` and `return_state` act on one `scope:target_state`; a multi-state conquest is several goals | `03_conquer_state.txt` 24, 57–62 |
| Refunds: back down −0.75 of dropped initiator/target goals, −1.00 of dropped backer goals, −0.5 on capitulation or negotiated peace without enforcement; the victim's infamy is reduced by 0.5 of the goal value on enforcement; making a secondary goal primary adds 0.5 of base | `00_defines.txt` 1064, 1172–1175 |
| A general `country_infamy_generation_mult` exists beside the unrecognized one; era-1 Empiricism gives −0.05; personality traits give ±0.1 | `common/modifier_type_definitions/00_modifier_types.txt` 409–424; `common/technology/technologies/30_society.txt` 353–362; `common/character_traits/personality_traits.txt` 125–126, 253–255 |
| Decay modifiers exist: excess influence up to +25 %, the Imposing trait −25 % (Nicholas I has it) | `common/static_modifiers/00_code_static_modifiers.txt` 596–600; `personality_traits.txt` 831–832; `common/character_templates/country_rus.txt` 5–20 |
| Game rule multipliers 0.5 / 0.75 / 1.25 / 1.5 apply to **calculated** infamy; the Standard setting has NO flag, the others are `infamy_generation_very_low`, `_low`, `_high`, `_very_high` | `00_defines.txt` 1122–1125; `common/game_rules/00_game_rules.txt` 97–117 |
| `on_game_started` fires "when bookmark initialization is complete but players are still in the lobby"; `on_game_started_after_lobby` fires "after everyone enters the game from the lobby for the first time for each campaign"; both have no root; vanilla reads `has_game_rule` and sets a global variable in the after-lobby block. Whether game rules are already readable in the earlier hook is not established by the files; the probe's two RULE records observe it | `common/on_actions/00_code_on_actions.txt` 3–23, 89–92 |
| Mods append to a vanilla on_action only through `some_vanilla_on_action = { on_actions = { my_on_action } }`; a second `effect` block conflicts | `common/on_actions/_on_actions.md` 115–128 |
| There is no weekly code-fired on_action. Monthly pulses exist rootless (`on_monthly_pulse`) and country-rooted (`on_monthly_pulse_country`); `trigger_event = { on_action = X days = N }` fires a custom on_action later | `_on_actions.md` 4–40; `00_code_on_actions.txt` 123–124, 474–475 |
| `on_diplomatic_play_started` has root = the play, `scope:initiator`, `scope:target` | `00_code_on_actions.txt` 2485–2489 |
| `change_infamy` block form nests the arithmetic under `value = { ... }`; scalar form `change_infamy = 50` is used by history | `common/treaty_articles/14_treaty_port.txt` 248–259; `common/history/countries/bol - bolivia.txt` 39 |
| `global_var:` is valid inside script values; rootless `set_global_variable` / `has_global_variable` and `has_game_rule` are used in vanilla's rootless on_action blocks | `common/journal_entries/01_paris_commune.txt` 234–236; `00_code_on_actions.txt` 16–19, 89–92, 123–160 |
| Numeric printing in loc data functions: `[SCOPE.sState('x').MakeScope.ScriptValue('name')|3]`, `[GetGlobalVariable('v').GetValue|3]`, `...MakeScope.Var('v').GetValue`; `debug_log` accepts data functions | `diplomacy_l_english.yml` 2414–2415; `content_104_l_english.yml` 1184; `00_code_on_actions.txt` 854 |
| A `STATE_` key names a region that can hold several owner slices, each its own formula state (STATE_PUNJAB: PAN and BHW; STATE_CAMBODIA: SIA, CAM, KLO) | `common/history/states/00_states.txt` 4195–4203 |
| Vanilla has no `has_game_rule` or `change_infamy` in history other than Bolivia's (absence of usage, not proof of invalidity) | grep of `common/history/` |
| Measured by the EoR project on build 25207758: a paused Load Game fires no `on_game_started`. Not yet measured for the after-lobby hook; section 9 measures it | EoR notes; re-verify per build |

**Hypothesis H1 (ordering).** The engine's order for a goal is assumed to be: script `infamy` value (state values with aggressor factors, subject multipliers inside) → × severity → clamp to the goal's min/max where defined → × (1 + general generation modifier) → × game-rule multiplier → floor at `WAR_GOAL_INFAMY_MINIMUM`. The files do not fix this order. `formula.py` holds an **ordering registry** of candidate placements of five stages: severity S, clamp C, general modifier G, rule multiplier R and final floor F. Two candidates are **equivalent** when they produce identical nominal charges `A_r` for every loaded ledger goal under all five rules and for every fixture (numerical equivalence on that domain, which subsumes commuting multiplications and clamp/floor identities). A candidate **fits** a fixture when, applied to the fixture's typed operands (section 6), it reproduces every transcribed line in the displayed order after the generator formats its prediction with the same UI formatting (totals to one decimal, shares and severity to two). Gate: zero fitting classes is a measurement or model failure and refuses generation; two or more fitting classes that are not equivalent is ambiguity and refuses generation until a further discriminating capture is added; exactly one class fixes the order.

**Hypothesis H2 (victim basis).** The −0.5 enforcement reduction on the victim is assumed to use the same calculated goal charge as the creator's accrual. It is declared, not measured.

## 4. Repository layout

```
historical_starting_infamy/
  .metadata/metadata.json                      shipped
  common/on_actions/zz_hsi_on_actions.txt      shipped
  common/scripted_effects/zz_hsi_effects.txt   shipped, GENERATED
  README.md                                    table section GENERATED between markers
  docs/superpowers/specs/                      this spec; later the plan
  docs/reviews/                                archived review rounds
  research/acts.csv                            ledger: historical acts
  research/goals.csv                           ledger: one row per Vic3 war goal
  research/goal_states.csv                     ledger: one row per formula-state component of a goal
  research/sources.md                          one citation block per act
  research/derivation.csv                      GENERATED: every intermediate value and the replayed timeline
  research/measurement/<YYYY-MM-DD>/           debug.log, system.log, probe-extract.log, oracle-tooltips.md + screenshots, manifest.sha256, engine.txt, playset.txt
  research/probe/                              throwaway probe mod, never shipped
  tools/hsi/                                   formula.py ledger.py probe_log.py timeline.py generate.py savecheck.py validate.py
  tools/tests/                                 pytest suite + fixtures
```

Only `common/` and `.metadata/` are loaded by the launcher. `research/probe/` is copied to a sibling mod folder (`mod/hsi_probe/`) for the measurement boot only.

## 5. The ledger

Three CSV files, hand-authored, every act sourced. Historical actors and 1836 runtime tags are kept apart: every participant is a historical actor id, and a 1836 TAG is attached only where the engine needs one (measurement of modifiers and slices, and emission of a balance).

**`acts.csv`**, one row per historical act: `act_id`, `title`, `start_date`, `end_date`, `source` (citation key in `sources.md`), `notes`.

**`goals.csv`**, one row per Vic3 war goal the act maps to:

| column | values |
|---|---|
| `goal_id`, `act_id` | keys |
| `wargoal` | one of `conquer_state`, `return_state`, `annex_country`, `make_protectorate`, `make_dominion`, `make_tributary`, `make_personal_union`, `transfer_subject`, `liberate_country`, `release_as_subject`, `regime_change`, `restore_union`. `liberate_subject` (severity falls to 0 at LD ≥ 75) and `reduce_autonomy` are excluded: no act in the window needs them |
| `holder` | historical actor id of the country that holds the goal and pays for it. **v1 restriction:** holder and creator are the same actor; a goal created for another participant is out of scope and is not represented. Root-dependent factors are evaluated for this actor |
| `holder_tag_1836` | TAG if the actor exists in 1836, else empty. Needed for measured modifiers and for emitting a balance; an actor without one still generates events (its victims' reductions are kept) and uses the declared fallbacks `general_mult = 0` and `unrec_mult = 0`. For an actor with a TAG, missing modifier data in the snapshot is a refusal, never a fallback |
| `holder_type` | `recognized`, `unrecognized`, `decentralized` as of the act; gates the unrecognized discount |
| `target` | historical actor id of the goal's formula target: the state owner for state goals, the subjugated or released country for country goals (for `transfer_subject` the subject, with the overlord recorded as `stakeholder`) |
| `stakeholder` | historical actor id or empty |
| `victim_tag_1836` | TAG of the actor whose balance receives the −0.5 enforcement reduction, if it exists in 1836 |
| `claim_date` | date the goal is treated as claimed; infamy accrues here. Convention: the start of the war or crisis in which the demand was made. Must lie in 1816-01-01..1835-12-31 |
| `resolution` | `enforced`, `dropped_peace` (−0.5), `dropped_backdown` (−0.75), `dropped_backer` (−1.0), or `pending` (still open on 1836-01-01) |
| `resolution_date` | date of enforcement or drop; may be on or after 1836-01-01 (then it has no effect on the balance, see the horizon rule in section 7); empty for `pending` |
| `loyal_subject` | 0/1, the full vanilla predicate: target is the holder's subject with liberty desire below 25, sourced |
| `rebellious_subject` | 0/1, the full vanilla predicate: target is the holder's subject, is the holder's enemy in the play, and initiated the play, sourced |
| `general_mult_source` | `measured_1836` (the holder's probe-measured modifiers) or `none` (actor without a 1836 TAG: both modifiers 0) |
| `notes` | the mapping judgment in words, including why the goal is a charged demand |

**`goal_states.csv`**, one row per formula-state component of a goal. Components are **disjoint historical formula states**:

| column | values |
|---|---|
| `goal_id`, `component_id` | keys; `conquer_state` and `return_state` have exactly one component; country-level goals have ≥ 1; `liberate_country` and `release_as_subject` list the released country's states, not the opponent's |
| `state_key` | vanilla `STATE_` region key |
| `slices_1836` | semicolon list of distinct 1836 owner TAGs whose slices of that region compose the historical state. Coverage is whole slices only; a historical demand that took part of one 1836 slice cannot be represented and is refused, not approximated. Within one goal no slice may appear in two components. The component's population and GDP shares are the sums of the slices' measured shares, taken before the baseline, caps and standing (declared approximation; merging two slices gives a different value from two separate states because of the baseline and caps, and the component boundary is therefore a recorded modeling input) |
| `owner_type` | `recognized`, `unrecognized`, `decentralized` as the historical owner was |
| `standing` | `capital`, `homeland`, `incorporated`, `unincorporated` under the historical owner, validated to the else-if meaning (an unincorporated capital is `unincorporated`) |
| `aggressor_homeland`, `shared_language`, `claim`, `scripted_unification`, `adjacent` | 0/1 **raw truths**. Both members of an else-if pair may be 1; the generator applies vanilla's precedence (homeland before language, claim before unification) |
| `interest_tier` | 1–5; default 3; 5 for the holder's home strategic region; 1–2 only with a stated reason |
| `justification` | one line per nontrivial predicate and for the component boundary |

**Inclusion rules.** Goals whose `claim_date` lies in the window and whose Vic3 analog is a charged demand: an initiator's territorial or subjugation demand, or a demand a defender added. Humiliation, independence, secession, unification and colonization rights generate none, so Greek and Belgian independence count only for their backers under `liberate_country` at 10 % of the released states. Vanilla's automatically supplied initial target goals carry no infamy and are not ledger goals. Conquests of decentralized or unrecognized polities are included; the discount applies only when `holder_type = recognized`. A goal still open on 1836-01-01 is `pending`. Nothing is excluded from the computation because of its size; thresholds apply only to finished balances (section 7). Actors without a 1836 TAG are computed but never emitted; BOL is computed and never emitted.

**Sourcing standard.** Every act cites at least one general reference in `sources.md`, enough to verify dates and territorial outcome. Where the mapping from a historical outcome to a goal is a judgment, `notes` says so.

## 6. Measurement

A throwaway probe mod in `research/probe/`. It ships nothing and is removed from the Vic3 mod folder after the boot.

**Hooks.** Rootless start records from both `on_game_started` and `on_game_started_after_lobby` (registered additively). Country-rooted monthly records from `on_monthly_pulse_country`, guarded to the holders the ledger names, the fixture holder and BOL, for the first three months. The actual firing dates are logged, not assumed. There is no weekly hook.

**Samples.** A sample is one hook firing and is self-contained: every record it emits carries `hook`, `sample`, `date` and its key, so records from different samples are never mixed.

- `GLOBAL`: `global_population`, `global_gdp`.
- `STATE`, per 1836 owner slice named in `goal_states.csv` and per fixture target: `state_key`, `owner`, `owner_type`, `pop`, `gdp`, `pop_share_uncapped`, `gdp_share_uncapped`, `incorporated`, `capital`, `owner_homeland`, `base` (`state_infamy_base`).
- `COUNTRY`, per holder tag, fixture holder and BOL: `country_type`, `country_infamy_generation_mult`, `country_infamy_generation_against_unrecognized_mult`, `country_infamy_decay_mult`, `infamy`.
- `DIAG` (country-rooted samples only), per (holder = root, slice): the 1836 value of every predicate the state formula reads, evaluated by the same triggers the formula uses: `aggressor_homeland`, `homeland_bonus_bool`, `shared_language`, `language_bonus_bool`, `claim`, `scripted_unification`, `adjacent`, `interest_bucket` (below 2, below 3, 3–4, 5+), `root_type`, `owner_type`; and `siv`, the value of `state_infamy_value` materialized inside the state scope with `set_variable` while root is the holder, then logged from the variable, together with `root_tag` to assert the root. `DIAG` records are diagnostic 1836 inputs and are never used as historical flags.
- `RULE` from both start hooks: which `infamy_generation` flag is active, or `standard` when none is. Equal readings from the two hooks are an observation, not a failure.

Numbers are printed through named wrapper script values and `MakeScope.ScriptValue('...')|3`, globals through `GetGlobalVariable(...).GetValue|3`, variables through `.Var('...').GetValue|3`; no abbreviations or percent formats. The extractor rejects missing, duplicate or non-numeric records and incomplete samples.

**Oracle fixtures.** Before observing, playing as a chosen holder with a known nonzero general generation modifier (an advanced country with Empiricism, −0.05), under the **Very Low** rule, open draft diplomatic plays and transcribe the complete infamy breakdown, every line in order with its number, into `oracle-tooltips.md` with screenshots. Each fixture is a **typed operand record**: capture id, date and tick, holder, target, rule, and every breakdown line transcribed in display order with its label and number, including the engine's own raw scripted subtotal (the sum of state values before severity), the severity line, any clamp line, the modifier and rule lines, and the total. Oracle B consumes the raw subtotal as its operand and tests only the goal-processing stages S, C, G, R and F; it does not validate the state formula, which oracle A does from the monthly `DIAG` records. Tick-0 `STATE` and `COUNTRY` records for the fixture's states and holder are kept with the capture for cross-reference, never substituted by later samples. Required fixtures: (A) `make_protectorate` against a non-subject target with cost well above the floor (severity line, rule line); (B) `conquer_state` against a state with at least one aggressor factor active (factor lines); (C) `regime_change` in a below-minimum and an above-maximum case (clamp of 3 / 10, an allowed ledger type); (D) a `conquer_state` whose Standard value lies between 1 and 2, so the final floor binds under Very Low and discriminates floor-before-rule from floor-after-rule. Fixtures are evaluated only against the tick-0 sample records of the same capture (section 9, oracle B). Concrete holder and targets are chosen while developing the probe and recorded with the fixtures.

**Procedure** (Eric, about fifteen minutes; Claude writes `research/measurement/PROCEDURE.md`): playset with only `hsi_probe`; launch with `-debug_mode`; New Game as the chosen holder; set the infamy rule to Very Low in the lobby; enter the game; capture the fixtures; Observe; run until the third monthly sample has fired; quit. Claude copies `debug.log` and `system.log`, extracts the `HSI;` lines, writes the manifest (section 7) and records the game version.

**Snapshot selection.** Historical reconstruction uses one aligned snapshot: the last country-rooted monthly sample supplies shares, denominators and all country modifiers together. Stabilization is a sampling policy, not proof of convergence: for every share the reconstruction uses, the relative change between the last two samples must be at most 2 %; two zero readings pass; a zero-to-positive or positive-to-zero transition fails; a failure is reported as a refused measurement rather than resolved by choosing another sample.

## 7. The generator (`tools/hsi/`)

Pure arithmetic over the ledger and the measurement. Constants are copied into `formula.py` with the defines file and line beside each.

**Per component:** `pop_share = Σ_slices pop / max(global_population, 1)`, likewise GDP, each × 0.375 × 10000; `capped(x) = min(15, x if x ≤ 10 else 10 + 0.5·(x − 10))`; `base = 5 + capped(pop) + capped(gdp)`; × standing; × (1 − 0.25) if aggressor homeland else × (1 − 0.15) if shared language; × (1 − 0.75) if claim else × (1 − 0.7) if scripted unification; × (1 − 0.1) if adjacent; × interest factor; × (1 + unrec_mult of the holder, 0 for an actor without a 1836 TAG) only if `holder_type = recognized` and `owner_type ≠ recognized`; floor 1. The historical model does not apply the homeland or shared-language bonus booleans (no actor in the window is assumed to have Nationalism); the diagnostic mode (oracle A) applies them when the `DIAG` record says they hold.

**Per goal and rule, the nominal charge `A_r(g)`**, computed exactly once per (goal, rule) in the registry order fixed by the fixtures: raw = Σ components; × 0.25 for each subject predicate that holds, only for goal types that carry that block; × severity; clamp to the goal's min/max where defined; × (1 + general_mult) when `general_mult_source = measured_1836`; × rule multiplier r ∈ {0.5, 0.75, 1.0, 1.25, 1.5}; floor 1. `A_r` is the nominal charge, independent of any country's current balance.

**Events** (all deltas are finished amounts; the timeline applies no further scaling):
- `+A_r(g)` to the holder at `claim_date`;
- `−f·A_r(g)` to the holder at `resolution_date` for a dropped goal, with f = 0.5 (`dropped_peace`), 0.75 (`dropped_backdown`), 1.0 (`dropped_backer`);
- `−0.5·A_r(g)` to `victim_tag_1836` at `resolution_date` for an `enforced` goal (H2);
- nothing for `pending`, and nothing for any event dated on or after 1836-01-01. **Horizon rule:** the balance is read at the beginning of 1836-01-01, before any event dated that day; only events dated 1835-12-31 or earlier are processed.

**Per country timeline** (`timeline.py`), per rule r: start at 0 on 1816-01-01; process the country's events in canonical order (`date`, then kind rank accrual 0 / reduction 1 / refund 2, then `goal_id`); before each event `I = max(0, I − 5·elapsed_days/365.25)`, then `I = min(1000, max(0, I + δ))`; after the last processed event decay again to the start of 1836-01-01 with the same `max(0, ·)`. Same-day accruals therefore precede same-day subtractions; this is a declared canonical order, not engine chronology, and ledger row order cannot change the result. Two simultaneous 20-point goals leave 35 after a year, not 30; a balance that reached zero before a new goal receives the whole new charge.

**Emission.** For each rule table, a country is emitted if it has a `holder_tag_1836`, is not BOL, and its finished balance is ≥ 0.05; values are rounded to two decimals. A correct table may be empty.

**Outputs:** `common/scripted_effects/zz_hsi_effects.txt` (UTF-8 BOM; header carrying the SHA-256 of every file in `tools/hsi/`, of the three ledger files, of `manifest.sha256`, and of the vanilla inputs `00_infamy_values.txt`, the defines infamy block, `00_diplomacy_values.txt`, `00_game_rules.txt` and every `war_goal_types/*.txt`); the README table between `<!-- hsi:table:start -->` and `<!-- hsi:table:end -->`, one column per rule; `research/derivation.csv` with every component, goal charge per rule, event and balance step.

**Measurement manifest.** `manifest.sha256` is a canonical listing of the named evidence files (`debug.log`, `system.log`, `probe-extract.log`, `oracle-tooltips.md`, screenshots, `engine.txt`, `playset.txt`) with their digests; it excludes itself. `validate.py` re-hashes every listed file and fails on any mismatch, missing or unexpected file.

**Refusals** (exit non-zero, nothing written): a slice not present in the chosen snapshot; an unknown war goal; a `holder_tag_1836` or `victim_tag_1836` absent from `common/country_definitions/`; `resolution_date` before `claim_date`; `claim_date` outside the window; `pending` with a date or a non-pending resolution without one; duplicate ids; orphan rows; a `conquer_state` or `return_state` goal with ≠ 1 component; a country-level goal with no components; a slice repeated within a goal; `claim = 1` on `conquer_state` or `claim = 0` on `return_state`; stabilization failure; ordering ambiguity (section 3); non-finite numbers.

**Tests** (pytest, stdlib only), written before the code: every per-component branch with hand-computed values, including the soft cap, the hard max, the floor, the unrecognized gate in both directions and both members of an exclusive pair set; per-goal severity, clamp and subject blocks per goal type; `A_r` above the floor and floor-binding across all five rules; the timeline with overlapping accruals, an exhausted balance followed by a new accrual, a refund after the balance would have been zero in isolation, a victim reduction, a pending goal, a post-horizon resolution, same-day ties at both bounds, row-order permutation invariance, and clamping at 0 and 1000; the ordering registry with fixtures that admit exactly one class, fixtures that admit two non-equivalent classes (refusal), fixtures that admit none (refusal), and two candidates that are numerically equivalent on the domain (accepted as one class); an absent recognized holder enforcing against a surviving unrecognized victim with positive infamy (fallback modifiers 0); horizon boundaries with events on 1835-12-31 (processed), 1836-01-01 and 1836-01-02 (not processed); a fixture ledger plus fixture probe extract producing golden outputs; one test per refusal; manifest verification with a modified listed file and an unchanged manifest (must fail); BOM on the generated file; `savecheck.py` failure paths (section 9).

## 8. Shipped mod content

**`.metadata/metadata.json`**: name "Historical Starting Infamy", version 0.1.0, supported_game_version "1.14.*", short description, tags Historical and Balance, no relationships.

**`common/on_actions/zz_hsi_on_actions.txt`**, the vanilla-documented additive form:

```
on_game_started_after_lobby = {
	on_actions = { hsi_on_game_started }
}
hsi_on_game_started = {
	effect = { hsi_apply_starting_infamy = yes }
}
```

**`common/scripted_effects/zz_hsi_effects.txt`** (generated):

```
hsi_apply_starting_infamy = {
	if = {
		limit = { NOT = { has_global_variable = hsi_applied } }
		if = { limit = { has_game_rule = infamy_generation_very_low }  hsi_table_very_low = yes }
		else_if = { limit = { has_game_rule = infamy_generation_low }  hsi_table_low = yes }
		else_if = { limit = { has_game_rule = infamy_generation_high } hsi_table_high = yes }
		else_if = { limit = { has_game_rule = infamy_generation_very_high } hsi_table_very_high = yes }
		else = { hsi_table_standard = yes }
		set_global_variable = hsi_applied
	}
}
hsi_table_standard = {
	c:EGY ?= { change_infamy = 17.4 }   # egy_syria_1831: g1..g5
	...
}
```

Scalar `change_infamy` lines use the form vanilla's own history uses. Standard is the `else` branch because it has no flag. No runtime arithmetic remains.

The after-lobby hook is used because `on_game_started` fires while the player is still in the lobby, where the game rules can still change, and vanilla's own rule-dependent start logic lives in the after-lobby hook. The after-lobby hook runs when the map opens, before the first tick, so the values are present on 1836.1.1 in a game that has never been unpaused; acceptance step 3 saves exactly that state. Its once-per-campaign behavior is measured by step 5, not assumed.

All script `.txt` files carry a UTF-8 BOM; files are written through a helper that adds it and `validate.py` enforces it.

## 9. Verification and acceptance

1. **Static.** `tools/hsi/validate.py`: BOM on every script file; brace balance ignoring quoted strings and comments; every `has_game_rule` flag named in the effect exists in vanilla's `00_game_rules.txt`; the generated header's hashes match the current generator sources, ledger files, measurement manifest and vanilla inputs, and the manifest's own entries verify (any mismatch fails). Run before every commit that touches game files.
2. **Oracle checks (derivation).** A: for every `DIAG` record, the generator in diagnostic mode, fed that sample's slice shares and denominators and the record's own 1836 predicates (bonus booleans included), reproduces `siv` within 0.005. B: for every fixture, exactly one registry class (section 3) fits its typed operand record, reproducing each transcribed line in order under the UI's formatting; zero or two or more non-equivalent fitting classes refuse generation. These tie the arithmetic to the engine; the unit tests tie it to hand computation. Neither validates the historical judgments in the ledger, which remain review inputs with their justifications.
3. **Acceptance boot, Standard rule** (Eric): playset with only the shipped mod, `-debug_mode`, New Game, Observe, and without ever unpausing save as `hsi_accept_std_1836_01_01`. `savecheck.py` parses the plaintext save structurally: locates the country database, maps records to tags via their `definition`, checks the game date is 1836.1.1 and no infamy rule flag is set, finds `hsi_applied` among global variables, requires every country in the Standard table to be present with a positive `infamy` within the tolerance of the table value, and requires every other country at 0 except BOL at 50. The tolerance is set from the storage precision observed in the retained sample save and must be below half the smallest emitted amount (target 0.005). A missing expected positive record fails. An empty table is accepted only if the Standard replay produced one.
4. **Acceptance boot, Very Low rule** (Eric): the same against the Very Low table, with the flag checked in the save.
5. **Lifecycle checks** (Eric, two short loads): load the Standard acceptance save paused and save again: values unchanged, `hsi_applied` present once. Load any pre-existing vanilla save with the mod enabled: no country's infamy changed. These measure the once-per-campaign claim.
6. **Failure-direction tests of `savecheck.py`** (pytest, on the retained sample save and mutated copies): no hook applied, wrong country, doubled application, a boundary entry set to zero, a boundary entry doubled, a truncated save and a missing record must each fail with the named reason.
7. **Error log.** `error.log` after each boot is diffed against a same-day vanilla-only boot; new distinct messages are explained or fixed; full logs retained; the mod's presence in the loaded playset is confirmed from the launcher database, not inferred from a quiet log.
8. **Observer A/B**, evidence rather than gate: a test-only additive `on_diplomatic_play_started` logger writes `initiator;target;date` to `debug.log` in both arms; same seed, six game-years, mod on and off; the README reports initiations per ledger country as one matched-seed observation, not a causal estimate.

Residual, declared: the Low, High and Very High dispatch branches are not exercised by a boot. They share the exact code shape of the two booted branches and their flag names are validated statically; a diagnostic boot per branch is available as a follow-up if wanted.

Acceptance is steps 1–7 passing with their artifacts recorded under `research/measurement/`.

## 10. Approximations, risks and assumptions

Declared approximations, all stated in the README:
- 1836 population and GDP shares, and the holder's 1836 generation modifiers, stand in for their values at the time of each act; actors without a 1836 tag use 0 for both generation modifiers.
- Split regions are composed by summing whole 1836 slices into one hypothetical historical state before the baseline and caps; partial slices are not representable.
- Holder and creator are the same actor; goals created for another participant are out of scope.
- Standing, claims, adjacency, shared language, interest tier and the subject predicates are hand-authored historical judgments recorded with justifications; the bonus booleans are assumed absent.
- Decay is continuous linear at the base rate between events; the engine's update cadence is not measured and no error bound is claimed; decay modifiers such as excess influence or the Imposing trait are ignored.
- Goal events are one claim and one resolution per goal; the primary-demand surcharge (0.5 of base) and mid-war enforcement timing are not modeled, which can understate a goal by up to half its base.
- Same-day events follow a declared canonical order, not engine chronology; the balance is read at the beginning of 1836-01-01, so events dated that day are not processed.
- The victim reduction uses the creator's calculated charge as its basis (H2, unmeasured).
- Finished balances are rounded to two decimals and dropped below 0.05.

Open points resolved by measurement before numbers are generated: H1 ordering (fixtures A–D and the registry gate); whether shares have stabilized by the third monthly sample (sampling policy with refusal); the after-lobby lifecycle (acceptance steps 3 and 5); the probe's numeric printing and root preservation (first boot).

Risks: a patch that changes `00_infamy_values.txt`, the defines block or the goal scripts invalidates the numbers, and `validate.py` fails on the hash mismatch; the remedy is re-measurement and re-review of the changed semantics. A country in the table that does not exist at the bookmark is skipped by `?=`; `savecheck.py` treats a missing expected positive record as a failure, so the mismatch surfaces.

## 11. Follow-ups, not in v1

Relations penalties toward victims; an in-mod rule (Off / Standard / Long memory); publication to Workshop and Paradox Mods with explicit approval; re-measurement when the game updates.

## 12. Change log

**v3 → v3.1 (after Codex round 3, 3 majors, 1 minor, verdict REVISE; cap reached).** Adopted: declared zero fallbacks for both generation modifiers of actors without a 1836 tag, with refusal for present actors lacking data (P1); fixtures are typed operand records carrying the engine's raw subtotal, so oracle B tests goal-processing stages only while oracle A validates the state formula; the fixture holder joins the monthly guard (P2); the ordering registry now includes severity, defines equivalence numerically on the loaded domain, fits under UI formatting with ordered lines, and refuses on zero or multiple non-equivalent classes (P3); the horizon is the beginning of 1836-01-01 with events dated that day excluded, stated identically in sections 5 and 7 (P4). Round 3's section 3 lists owner decisions, not defects; they are for Eric.

**v2 → v3 (after Codex round 2, 2 blockers, 10 majors, 1 minor, verdict REVISE).** Adopted: the nominal charge `A_r` is computed once per goal and rule and the timeline applies no further scaling (N1); the balance is floored at zero during decay and again at the horizon (N2); a canonical same-day order with permutation invariance (N3); fixtures with a nonzero general modifier, a floor-binding case and an allowed clamp type, plus an ordering registry that refuses ambiguous fits (N4, N12); `DIAG` records carrying every 1836 predicate and a root-asserted `siv` so oracle A has real inputs (N5); fixtures bound to their own tick-0 sample, one aligned reconstruction snapshot, and zero handling in the stabilization policy (N6); holder = creator restriction, full subject predicates, explicit target and stakeholder (N7); disjoint whole-slice components, raw-truth flags with vanilla precedence, denominators floored at 1 (N8); pending resolutions, post-horizon dates, actors without a 1836 tag kept in the computation, thresholds only on finished balances (N9); cadence claims removed (N10); a canonical manifest excluding itself with verified entries and generator-source hashes (N11); tolerance from observed storage precision, positivity, boundary mutations, empty tables accepted when the replay says so, flag names validated statically with the three unbooted branches declared (N13, bounded). Wording softened on the hook rationale; commit language removed from procedures.

**v1 → v2 (after Codex round 1, 17 findings, verdict REVISE).** Adopted: one decaying balance per country replayed from dated events instead of independent per-act decay (F1); five rule-specific tables with scaling applied to accruals before decay, replacing runtime multiplication (F2, F12); the aggressor-type gate on the unrecognized discount (F4); goal-level modeling with the goal floor after all multipliers (F5); per-goal-type subject blocks with explicit predicates (F6); released-state components for liberation goals (F7); drop of `liberate_subject` (F8); claim/resolution events with the four refund kinds and victim reductions (F9, bounded: no primary-demand surcharge or mid-war enforcement); owner slices and separate credited/victim identities (F10); monthly country-rooted probe (F11); controlled oracle captures (F13); the fixed-snapshot framing and stabilization check (F14, bounded: cadence not measured, modifiers declared ignored); derivation oracles, structural save parsing, failure-direction and lifecycle tests (F15); a play-started logger for the A/B (F16); binding hashes over all numerical inputs (F17). General generation modifier included as a 1836 snapshot with ordering under H1 (F3). Also corrected: "vanilla never evaluates `has_game_rule` in history" is now stated as absence of usage; Standard has no rule flag; the earlier "weekly for eight weeks" probe is withdrawn.

**v1.** Delivery moved from a history file to the after-lobby hook after Eric asked whether the values exist before the first unpause.

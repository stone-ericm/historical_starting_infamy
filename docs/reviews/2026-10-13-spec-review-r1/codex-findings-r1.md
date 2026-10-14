# Historical Starting Infamy — spec review R1

## 0. Disclosure

No memory summary was injected into this review, and I did not read any memory file or use context remembered from another session. The supplied conversation contains Eric's global AGENTS.md instructions and the review request. The spec itself cites EoR observations; I treated those citations as unverified assertions, not independent evidence, and did not read EoR files.

The developer instruction identifies this agent as Codex based on GPT-6. An exact model identifier and reasoning-effort footer are not visible to me through the permitted review interface, so I cannot truthfully report their footer values.

Reviewed repository HEAD: **202905f**, confirmed by git log. The initial tracked worktree was clean. The installed launcher/launcher-settings.json reports rawVersion **1.14.5**. I read the supplied spec and local vanilla scripts/documentation, performed read-only arithmetic checks, and wrote only this deliverable. I did not launch the game, inspect an actual save, access the network, run herdr, start agents, or mutate git. Numerical counterexamples below are synthetic calculations, not engine measurements.

Citation convention: **S** means docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md in this repository. All common/, events/, and localization/ paths are relative to /Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/. References to launcher/ are relative to the installation directory.

## 1. Findings

### 1. BLOCKER — §7: independent decay per act destroys the country timeline

**Claim:** Derive a remaining value for each act, clamp it separately, and sum those remaining values (S:129–131).

**Evidence:** common/defines/00_defines.txt:1000–1006 defines a country's infamy bounds and BASE_YEARLY_INFAMY_DECAY_RATE = 5.0. localization/english/interfaces_l_english.yml:6297–6298 describes the country's infamy and its decay rate. It does not give each historical incident a separate five-point annual decay allowance.

Under the spec's own idealized five-point decay interval, two simultaneous 20-point acts leave 15 + 15 = **30**. A country with 40 infamy loses five points once and retains **35**. I checked both with Python Decimal. Separately clamped act refunds also cannot reduce infamy accrued by another act after the refunded act's isolated balance has reached zero. Consequently §1's claim that sufficiently old acts are necessarily gone is overstated: persistent aggregate infamy can retain their contribution.

**Proposed fix:** Build one ordered event stream per country, decay the country's balance once between event dates, apply additions/refunds/target reductions to that balance, and clamp it after each transition. Retain per-goal accrued amounts to determine refunds, but do not maintain independently decaying act balances. Add overlapping-act and delayed-refund counterexamples to the tests.

### 2. BLOCKER — §§7–9: scaling the decayed result does not respect the generation rule

**Claim:** Compute Standard-rule remaining infamy and multiply that result at game start; Very Low acceptance expects exactly half (S:133,147,157).

**Evidence:** common/game_rules/game_rules.md:25–28 and common/defines/00_defines.txt:1122–1125 say the rule multiplies **calculated infamy**. The decay define at :1006 is separate. Scaling generation does not scale the subsequent time spent decaying.

Synthetic example: an act generates 10 before a five-point decay interval. Standard leaves 5. Very Low generation leaves max(0, 10 × 0.5 − 5) = **0**, whereas the spec emits **2.5**. Very High leaves **10**, whereas the spec emits **7.5**. An act generating 5 and losing 5 disappears under Standard but leaves **2.5** under Very High; omitting countries with no Standard residual loses that case entirely.

**Proposed fix:** Generate an independently replayed country timeline for each of the five rule settings and select the correct finished table at runtime. Apply scaling to accrued goal amounts and associated refunds/reductions before decay, with engine-tested floor ordering. Acceptance must compare against those five independent results. If proportional scaling of the final historical surcharge is intended instead, explicitly describe it as a custom policy rather than vanilla generation semantics.

### 3. MAJOR — §§3,6,7: general infamy generation modifiers are missing

**Claim:** The generator needs the listed state factors and the aggressor's unrecognized-target modifier only (S:112,123–127).

**Evidence:** localization/english/diplomacy_l_english.yml:522 has INFAMY_EFFECT_FROM_GENERATION_MULT, distinct from the game-rule factor at :523. common/modifier_type_definitions/00_modifier_types.txt:409–424 separately defines country_infamy_generation_mult and country_infamy_generation_against_unrecognized_mult. common/technology/technologies/30_society.txt:353–362 gives era-1 empiricism a **−0.05 general generation modifier**. common/history/countries/mex - mexico.txt:5 explicitly grants empiricism. Advanced powers receive all era-1 technology through common/scripted_effects/00_starting_inventions.txt:4–5, called by common/history/countries/fra - france.txt:5 and gbr - great britain.txt:26. Personality traits also supply general modifiers, e.g. cautious −0.1 and reckless +0.1 in common/character_traits/personality_traits.txt:125–126,253–255.

This is an additional game calculation outside the state script, not another unrecognized-target discount. The exact engine ordering relative to floors/clamps still needs measurement.

**Proposed fix:** Probe general generation modifiers as well; specify whether historical modifiers or 1836 proxies are used and include the appropriate factor in each goal's calculation. Verify its ordering with a tooltip/actual accrued-infamy check. If intentionally omitted, narrow the claim of using the game's own rules and quantify the approximation.

### 4. MAJOR — §§5,7: the unrecognized-target discount lacks its aggressor-type gate

**Claim:** Whenever target_type is unrecognized or decentralized, multiply by 1 + the aggressor's measured unrec_mult (S:98,125).

**Evidence:** common/script_values/00_infamy_values.txt:262–277 requires BOTH:

- root is neither unrecognized nor decentralized;
- the actual state's owner is unrecognized or decentralized.

Only then does it add root.modifier:country_infamy_generation_against_unrecognized_mult. The spec has no historical aggressor-type column and uses one act-level target_type even when formula states need distinct owners.

**Proposed fix:** Record the formula root's country type at accrual and each formula state's owner/type. Apply the discount only when both conditions hold. A measured nonzero modifier on an unrecognized aggressor is not sufficient authorization to use it.

### 5. MAJOR — §§3,5,7: the war-goal minimum and actual goal boundaries are missing

**Claim:** Floor each state at one, then aggregate an act and apply severity/explicit goal min/max (S:31,127).

**Evidence:** common/defines/00_defines.txt:1148 says WAR_GOAL_INFAMY_MINIMUM = 1 is a floor both for a state and for “a war goal's total infamy after all multipliers.” localization/english/diplomacy_l_english.yml:2412 distinguishes the war-goal minimum from the state minimum at :2436. A state floored at 1 followed by protectorate severity 0.5 produces 0.5 in §7, which omits the additional goal floor. Legitimate zero-infamy goals are special cases; liberate_subject explicitly zeroes severity in finding 8.

Moreover conquer_state and return_state each operate on one scope:target_state (common/war_goal_types/03_conquer_state.txt:24,57–62; 21_return_state.txt:24,57–62). A historical act containing several such states represents several goals, not one aggregate goal. Floors after subject/rule multipliers must therefore be applied at each real goal boundary.

**Proposed fix:** Distinguish historical act/war IDs from goal IDs. Compute each actual goal through its final minimum, treating explicit zero-infamy cases separately; aggregate country events afterward. Measure whether the global minimum follows game-rule scaling, and do not invent that engine ordering from the state script.

### 6. MAJOR — §§3,5,7: subject discounts have the wrong placement and an insufficient predicate

**Claim:** A single subject_relation enum picks a discount, applied after severity and min/max; reduce autonomy gets ×0.5 (S:34,78,127).

**Evidence:** common/war_goal_types/20_regime_change.txt:46–84 places both subject factors **inside the infamy script value**, before that value is consumed by engine severity/clamp handling. Its explicit min/max are at :42–44. Assuming the spec's severity-then-clamp semantics, a raw sum of 4, loyal-subject discount 0.25 and severity 0.1 is clamped to 3; §7 instead clamps 0.4 to 3 and then emits **0.75**.

The two multipliers are independent multiply blocks, not an else_if chain (00_annex_country.txt:60–90). “Rebellious” specifically means the target is root's subject, is root's diplomatic-play enemy, and initiated the play (:75–86). It does not mean a rebellious AI attitude or merely high liberty desire. A low-LD target satisfying the rebellion predicate can receive both factors.

The listed goal types also do not uniformly have these blocks: liberate_country, release_as_subject, liberate_subject and restore_union lack them (13_liberate_country.txt:45–56; 38_release_as_subject.txt:41–52; 14_liberate_subject.txt:61–67; 29_restore_union.txt:69–75). reduce_autonomy has severity **0.2**, uses ×0.5 only below the LD threshold, and has a separate rebellion factor (19_reduce_autonomy.txt:42–82); it is not in the ledger's permitted wargoal list.

**Proposed fix:** Replicate each goal's own infamy block. Record target_is_subject_of_holder, target liberty desire, play initiator and enemy relationship separately; permit stacked factors when their predicates overlap. Apply them inside the raw goal value before engine processing. Either support reduce_autonomy with its actual 0.2 severity and conditional discount, or declare it excluded.

### 7. MAJOR — §§5,7: liberation counts the wrong collection of states

**Claim:** For every country-level goal, list every state the historical target held (S:84).

**Evidence:** country_infamy_value loops every_scope_state (common/script_values/00_infamy_values.txt:287–295), but liberate_country uses **every_releasable_state**, labelled INFAMY_RELEASED_STATES (common/war_goal_types/13_liberate_country.txt:48–54). release_as_subject uses the same releasable-state iterator (38_release_as_subject.txt:44–50). localization/english/diplomacy_l_english.yml:2432 describes “the states that would be released.”

Using all Ottoman states for a Greek liberation, or all Dutch states for a Belgian liberation, applies the 10% severity to the wrong base. Those examples are mappings mentioned by the spec, not claims that I measured their game costs.

**Proposed fix:** Add the released country/selection and an explicit formula-state set. Separate opponent, release target and actual state owners. For liberation goals, validate against the intended releasable states rather than demanding every state of the opponent.

### 8. MAJOR — §§3,5,7: liberate_subject severity is conditional, including zero

**Claim:** liberate_subject always has severity 0.2 and generates infamy (S:33,75,98).

**Evidence:** common/war_goal_types/14_liberate_subject.txt:47–59 starts at 0.2, then multiplies by zero when target liberty_desire >= WAR_GOAL_INCREASE_AUTONOMY_MIN_LIBERTY_DESIRE. common/defines/00_defines.txt:1109 defines that threshold as **75**. The script comment says “No infamy if target has high liberty desire.”

**Proposed fix:** Record target liberty desire or an explicitly sourced high-LD predicate. Handle the zero-severity branch and verify its interaction with the general goal floor. Do not treat all enemy-subject liberations as 20% charges.

### 9. MAJOR — §§5,7: war_start/war_end and three outcomes cannot reproduce accrual and refunds

**Claim:** Accrue A at war_start; failed always refunds half, backed_down always refunds three quarters at war_end (S:74,79,98,129).

**Evidence:**

- common/war_goal_types/war_goal_types.md:285–286 describes infamy as the cost to **claim** a goal. Claiming in a diplomatic play precedes war outbreak and can also occur later than play initiation.
- common/defines/00_defines.txt:1064 defines an additional **0.5 of base infamy** when an existing goal is made a primary demand.
- :1172 refunds −0.75 for **dropped goals of the initiator/target** on backing down.
- :1173 instead refunds **−1.00 for dropped backer goals**, including a backer switching sides.
- :1174 refunds −0.5 when a goal is dropped on capitulation or negotiated peace without enforcement.
- :1175 reduces the **target's** infamy by −0.5 of the goal value upon enforcement. No target-side event exists in §7.
- common/diplomatic_plays/diplomatic_plays.md:8–9 distinguishes initial initiator goals (infamy enabled by default) from initial target goals (disabled by default). A goal type alone does not determine every accrual. For example dp_revolution uses annex_country but disables starting initiator infamy (00_diplomatic_plays.txt:550–559).

An abandoned historical campaign is not automatically a negotiated-peace refund. When one side backs down, surviving primary demands may be enforced; it is the **dropped goal**, not the entire campaign outcome, that earns a refund. In 1.14.5 some goals can also enforce mid-war through occupation timers (war_goal_types.md:294–298), so war_end is not universally the enforcement date.

**Proposed fix:** Represent goal claim/addition, primary conversion, enforcement and drop events with dates, actual accrued amounts and participant roles. Replay target reductions on the victim's country timeline as well as refunds on the credited country's timeline. If dates/roles cannot be reconstructed historically, state a consistent approximation instead of asserting exact game semantics.

### 10. MAJOR — §§5–7: a STATE_ key and one aggressor/target pair cannot identify all formula scopes

**Claim:** A state row is keyed by act_id plus a vanilla STATE_ key, and each act has one aggressor and historical-owner target (S:73,76,84–96); the probe logs STATE_KEY and owner (S:111).

**Evidence:** A STATE_ key denotes a state region, which can contain multiple country-owned states. common/history/states/00_states.txt:2335–2350 creates NET, FRA and GBR states inside STATE_GUAYANA; :4195–4203 creates PAN and BHW states in STATE_PUNJAB. The infamy formula uses state_population, state GDP and owner-specific standing (00_infamy_values.txt:1–14,77–110), not an arbitrary region total. The caps and flat baseline make “aggregate the whole region” and “calculate each owned state” different operations.

Distinct political roles are also real script scopes: war_goal_types.md:265–273 lists root **holder**, creator_country, target_country and stakeholder separately. Transfer Subject explicitly uses the subject as target and its overlord as stakeholder (26_transfer_subject.txt:7–12,34–37). Conquer State validates target_country as the actual state's owner (03_conquer_state.txt:34–35), even when an overlord leads the opposing play. localization/english/interfaces_l_english.yml:6740–6742 credits goal infamy to the **creator**.

**Proposed fix:** Use a formula-state/component ID, region key, historical owner and territorial/province coverage, plus an explicit mapping to measured 1836 owner slices. Record holder/beneficiary, creator/credited country, goal target, stakeholder/overlord and historical actor-to-1836 output mapping independently. Reject duplicate components and ambiguous matches. For a conquest of only part of a single owner's state, define the counterfactual subdivision or label the whole-state approximation; multiplying a capped whole-state value by a territory percentage is not exact.

Whole-state ownership changes between separate acts ARE expressible through separate act targets and standing rows. What is missing is boundary/component identity and independent political roles, not a blanket inability to record any ownership change.

### 11. MAJOR — §6: no documented code-fired weekly on_action supports the probe

**Claim:** Use a weekly pulse to produce eight weekly snapshots (S:106,119).

**Evidence:** common/on_actions/_on_actions.md:4–33 lists global monthly/yearly pulses and country/character/state monthly and longer pulses; it lists no weekly pulse. I searched all common/on_actions/ files: there is no weekly pulse declaration. The known global hook is on_monthly_pulse, with no root (00_code_on_actions.txt:123–124); on_monthly_pulse_country has a country root (:474–475). An on_weekly_pulse **member of a diplomatic-play definition** exists (common/diplomatic_plays/00_diplomatic_plays.txt:21; diplomatic_plays.md:26). That is not an identically named code-fired global on_action.

Absence in these files does not prove an undocumented engine hook cannot exist. It does mean no exact weekly code hook/name/scope has been established by this spec's evidence.

**Proposed fix:** Schedule a uniquely named custom on_action from the after-lobby effect using trigger_event = { on_action = hsi_probe_sample days = 7 }, then reschedule up to eight samples, with a defined country root chosen once and independent state/country loops. _on_actions.md:36–40 documents delayed on_action firing. Confirm the dates, scope and eight complete records in the boot; do not assume that naming a definition on_weekly_pulse makes the engine call it.

### 12. MAJOR — §8: runtime scaling uses an unverified change_infamy argument shape

**Claim:** Ship change_infamy = { value = <n> multiply = global_var:hsi_rule_mult } (S:147).

**Evidence:** Vanilla's actual arithmetic block usage nests the formula under value, for example common/treaty_articles/14_treaty_port.txt:248–259:

    change_infamy = {
        value = {
            add = 3
            multiply = { ... }
            max = 20
            min = 2
        }
    }

06_transfer_state.txt:147–162 likewise uses change_infamy = { value = { value = 25 ... } }. Every executable block usage I found in common/ and events/ uses that value wrapper; none demonstrates an outer multiply. common/script_values/script_values.md documents general inline formulas, but does not document change_infamy's engine argument parser. Therefore the frozen files do **not** let me prove that the spec's shorter shape is rejected; neither do they establish that its multiplier is accepted instead of ignored.

global_var itself is supported: a country journal entry uses value = global_var:paris_commune_progress_var (common/journal_entries/01_paris_commune.txt:234–236). Global-variable lookup is not dependent on the current country owning that variable.

**Proposed fix:** Use the demonstrated form:

    c:TAG ?= {
        change_infamy = {
            value = {
                value = <n>
                multiply = global_var:hsi_rule_mult
            }
        }
    }

Then verify actual save deltas under both Standard and Very Low. After finding 2's redesign, selecting precomputed rule-specific amounts can eliminate this runtime multiplication. Treat the original shape as unvalidated integration, not as a proven engine fact or a proven parser failure.

### 13. MAJOR — §§3,6,10: the severity confirmation procedure is neither controlled nor sufficiently testable

**Claim:** With any country, hover protectorate and then annex against a target to confirm a 50% relationship, before observing (S:117).

**Evidence:** Annex Country is omitted from the normal goal picker: 00_annex_country.txt:10 sets skip_build_list and :23–27 has possible = { always = no }. Protectorate and annexation are also not simultaneously valid alternative subject transitions against an arbitrary identical target. Their subject discounts sit in the raw infamy scripts, so comparing different targets/relationships does not isolate severity.

The proposed records measure only state_infamy_base and country modifiers, not state_infamy_value for an identified aggressor/holder or a complete goal cost (S:111–112). A casual ratio can therefore leave aggressor factors, goal floor, general modifiers and clamp ordering unverified. Vanilla already provides positive multiplier evidence: localization/english/diplomacy_l_english.yml:2433 literally says “×$VALUE|2$ from ... severity”; :2434–2435 separately labels minimum and maximum clamps.

**Proposed fix:** Choose and document a valid holder/target pair with no subject discounts and a cost well above the final floor. Capture the full draft tooltip breakdown, including its ×0.50 severity line, and compare the goal cost to independently logged country_infamy_value under the SAME holder/root. Check a low and high raw-value case for an explicit clamp (e.g. foreign investment rights, 07_foreign_investment_rights.txt:53–55), and a discounted/clamped case for ordering. Record numeric expectations and pass/fail criteria, not an unrecorded visual impression. This can be done without advancing the campaign if initialized values are available.

### 14. MAJOR — §§1,6,7,10: exact vanilla decay and historical inputs are overstated

**Claim:** Values represent the game's own rules, decayed at the vanilla rate; use exactly 5 per 365.25 days, ignore decay modifiers, and take week 8 as the input snapshot (S:9,119,129,167–168).

**Evidence:** The define establishes five per year, not a 365.25-day integration algorithm. localization/english/interfaces_l_english.yml:6298 presents decay **per week** with yearly base and mitigation. It does not establish whether the engine updates the stored value each tick/day/week; the frozen scripts do not reveal the calendar denominator or update/rounding implementation.

More materially, common/static_modifiers/00_code_static_modifiers.txt:596–600 grants up to **+25% decay from excess influence**. common/character_traits/personality_traits.txt:831–832 gives imposing **−25% decay**. Russia's starting ruler is Nicholas I (common/history/characters/rus - russia.txt:4–5), whose template has imposing (common/character_templates/country_rus.txt:5–20). The ignored factors are not necessarily hypothetical late-game effects. I have not measured Russia's net decay or reconstructed any country's 1816–1835 modifiers.

Week-8 GDP/population, 1836 technology modifiers, historical standing and default tier 3 are a mixed counterfactual snapshot. “Shares move slowly over twenty years” and “GDP is 0 or unsettled before the first ticks” are not established by the supplied measurements: no measurements exist yet. The vanilla after-lobby hook itself uses c:JAP.gdp to set a 135% GDP target (00_code_on_actions.txt:97–103), though that usage alone cannot prove GDP has already settled.

**Proposed fix:** Describe a fixed-snapshot, base-decay approximation explicitly, or model the relevant historical modifiers. Measure raw infamy across tick/day/week/month boundaries with a controlled net decay modifier before claiming exact cadence/denominator. Validate stabilization from the recorded series instead of always choosing week 8. Report sensitivity to snapshot and default-tier choices without inventing an error bound.

### 15. MAJOR — §§6,9: acceptance verifies delivery of its own output, not the derivation

**Claim:** Generated table equality, a global guard and clean log delta are sufficient acceptance (S:155–161).

**Evidence:** The generated effect and README table come from the same arithmetic (S:135,139). A shared error in decay, liberation-state selection, generation modifiers or rule placement can make the effect and table agree exactly. The Very Low test explicitly codifies finding 2's wrong halving oracle. State-base measurements in S:111 do not validate the aggressor/goal calculations. An empty emitted table makes all listed-country equality assertions vacuous; a guard can still exist after a no-op effect.

No real save or save parser is among the frozen inputs. S:156's EoR field-presence anecdote does not establish country-ID/TAG mapping, zero-field omission, serialization precision, container/compression handling, guard location or a validated parser for this mod. Checking arbitrary text for hsi_applied does not establish that the actual persistent global variable is set.

**Proposed fix:** Separate numerical oracle checks from delivery checks. Require independent engine/tooltip comparisons for representative branches and pooled-timeline counterexamples, and require a nonempty positive sentinel in the effect boot. Parse an actual tick-0 save structurally, map country records to tags, validate game date/rule and the global-variable container, reject missing expected positive records, and explicitly establish how omitted zero fields work. Demonstrate that missing hook, wrong multiplier, duplicate application, wrong country mapping and truncated/missing input each produce a failed check. Add paused reload and late-enable tests for the advertised new-campaign/idempotence behavior.

### 16. MINOR — §9: the proposed AI metric has no established persisted source

**Claim:** Count all plays initiated during six years from the final 1842 saves (S:159).

**Evidence:** Nothing in the frozen files establishes that completed diplomatic plays remain as a complete initiation history or counter in that save. Counting only extant plays would measure concurrency, not the number started. The real initiation hook is documented in common/on_actions/00_code_on_actions.txt:2485–2489: root = diplomatic play, scope:initiator = initiator country.

**Proposed fix:** First prove a persisted history/counter with a small run containing a completed play. Otherwise use a test-only additive on_diplomatic_play_started logger/counter in both arms. Present one matched seed as an observation, not an established causal estimate; the changed world state can change the subsequent sequence of random draws.

### 17. MINOR — §§7,9,10: stale-output checks do not bind all numerical inputs

**Claim:** Ledger/measurement header hashes and printing the game version detect stale generation; remeasurement is the patch remedy (S:135,155,165).

**Evidence:** The calculation also depends on formula.py/generator logic, vanilla constants, war-goal scripts, diplomacy script values and measurement extraction/selection. S:135 specifies ledger hashes and the measurement directory used, but does not specify an unambiguous content manifest hash for that directory or hashes for those other dependencies. Merely printing a version is not an invalidation check. Remeasurement cannot repair old constants or old goal logic copied into Python.

**Proposed fix:** Bind the generated outputs to a canonical measurement manifest, generator/formula version or hash, and hashes of the actual vanilla formula/defines/goal inputs. Fail validation on mismatch and require re-extraction/review of changed formula semantics as well as remeasurement.

## 2. Answers to questions 1–9 not already covered by a finding

### Q1. Hook timing, lifecycle and additive registration

The after-lobby hook is the **supported choice**. 00_code_on_actions.txt:3–13 distinguishes bookmark initialization while still in the lobby from first entry into the game for each campaign; both have no root. Its no_dynamic_naming branch reads has_game_rule with no root (:15–23), and it sets a global variable there (:89–92). This directly supports rule-dependent, rootless startup work.

The safe additive registration is documented by common/on_actions/_on_actions.md:115–128:

    on_game_started_after_lobby = {
        on_actions = { hsi_on_game_started }
    }
    hsi_on_game_started = {
        effect = {
            hsi_apply_starting_infamy = yes
        }
    }

Do not put a second effect or trigger block on the existing named vanilla hook. The custom handler can have its own trigger or a NOT-hsi_applied conditional.

“First time for each campaign” supports once-per-campaign intent. The files do not independently prove the exact save/load lifecycle, whether all lobby rule changes precede every initialization path, or the precise first AI evaluation relative to this handler. They also do not say that game rules are necessarily unavailable during on_game_started; they specifically say player identities are unknown. Vanilla's use of the later hook proves its suitability, not exclusivity. S:179's “never evaluates has_game_rule inside history” overstates a search showing no literal uses: lack of usage is not proof of engine invalidity.

Require the paused new-game save at 1836.1.1, a paused reload with no further addition, and a vanilla save with the mod enabled afterward. The spec's EoR load claim concerns on_game_started, not an independently measured after-lobby lifecycle.

### Q2. Severity, clamps and the cheapest engine test

Finding 13 gives positive localization evidence for a severity **multiplier**, and findings 5–6 show missing floor/ordering issues. The absence of this field from war_goal_types.md is real, but the semantics are not wholly unknowable: the explicit × severity localization is stronger evidence than a guessed correlation among goal files.

The executable's ordering of severity, explicit clamps, general generation modifier, rule multiplier and final floor is not fully specified by these files. Cheapest test: on a paused new game, inspect and record one valid protectorate draft breakdown with no subject discounts, verify its severity line against a same-root raw total, then inspect explicit minimum/maximum cases. A below-floor cost under Very Low distinguishes rule/floor ordering. Do not require picking Annex Country as an ordinary alternative.

### Q3. Step-by-step state formula comparison

The state arithmetic in §7 is largely right; the defects are specific:

| Stage | Vanilla evidence | Assessment |
|---|---|---|
| World shares | 00_infamy_values.txt:1–26 | pop/global_pop and GDP/global_GDP, each denominator floored at 1, then ×0.375×10000. The spec does not explicitly state the denominator safeguard; define it or refuse unusable inputs. |
| Soft/hard caps | :39–74 | Each share subtracts (x−10)×(1−0.5) above 10, then caps at 15. §7's capped(x) is equivalent. Synthetic boundary values are 10→10, 12→11, 20→15, 30→15. |
| Standing | :77–110 | One else_if chain: incorporated capital 2; otherwise incorporated owner's-primary-culture homeland 1.5; otherwise incorporated 1; otherwise 0.5. A capital or homeland that is unincorporated still gets 0.5. Encode these conditions in the meaning/validation of standing. |
| Homeland/language | :124–169 | Mutually exclusive. The language branch requires a culture **present in the state**, with a homeland there, sharing a language trait with root's primary cultures. Merely speaking a related language in the region is insufficient. Bonus bool reductions are nested within the corresponding selected branch. |
| Claim/unification | :172–193 | Mutually exclusive. §7 has this right. The scripted-unification predicate uses the actual state owner; verify hand-authored booleans against that meaning. |
| Adjacency | :195–206 | Independent ×0.9 when root is land-adjacent to the actual state. Correct in §7. |
| Interest | :208–255; 00_diplomacy_values.txt:1068–1073 | One chain: below 2 →1.25; otherwise below 3 →1.10; otherwise at least 5 →0.8; otherwise 1.0. Tiers 3 AND 4 are neutral. No-interest/below-tier-1 cases would also take the first branch; ledger's 1–5 range needs a policy for absent interest. |
| Unrecognized owner | :258–279 | Finding 4: conditional on BOTH root type and state-owner type. |
| State floor | :281–284 | min = 1 after these factors; §7's floor placement is correct. |
| Country total | :287–295 | Sum actual owned states; liberation uses a different iterator. |
| Goal processing | Individual war-goal files; defines :1148 | Findings 3,5–8: more than sum×severity×one enum discount. |

The old WAR_GOAL_INFAMY_POPULATION_SCALING_* defines at 00_defines.txt:1158–1160 do **not** occur in this state formula and should not be added to it merely because they exist. They are used by a different operation, e.g. common/diplomatic_actions/43_subjects_handle_states.txt:317 onward.

The spec's decision to omit bonus booleans can be a declared historical assumption. nationalism and pan-nationalism supply them (30_society.txt:693–703,1184–1195). That does not itself establish which hypothetical pre-1836 actors possessed them; there is no completed ledger here proving the universal “none” claim.

### Q4. Decay, floors and refund timing

Five per year and a zero lower bound are supported (defines :1000,:1006); “no floor” is only correct if it means **no positive residual floor**, not no lower bound. The country upper bound is 1000 (:1001). Files show weekly display units, not an independently verifiable daily or monthly update algorithm. Finding 14 explains why 365.25-day exactness and zero modifiers are unsupported.

The constants −0.75, −0.5 and target reduction −0.5 are correct, but their application points are **goal drop on backdown**, **goal drop on capitulation/negotiated peace**, and **enforcement on the victim**, respectively (defines :1172–1175). There is also a −1 backer refund. Finding 9 explains the schema mismatch.

A cheap cadence test logs raw country infamy with a known fixed net modifier before/after successive day boundaries, a weekly boundary and a month boundary. Use tick-level values or saves with known precision rather than the one-decimal main tooltip; keep new accrual/refunds out of the interval.

### Q5. Shipped effect validity and rootless globals

global_var is valid as a numeric script-value input from country context (01_paris_commune.txt:234–236), with further arithmetic examples in 00_code_on_actions.txt:288–293 and 00_victoria_great_game_scripted_effects.txt:269,327–331. The precise outer change_infamy block shape remains unverified; use finding 12's vanilla-demonstrated nesting.

Rootless set_global_variable and has_global_variable are usable: the after-lobby block sets one at :89–92, and the rootless monthly block tests NOT = { has_global_variable = germany_formed } then sets it (:123–124,154–160). has_game_rule works without root in the after-lobby block (:16–19).

Use a conditional guard, not an assumed literal “return” effect:

    if = {
        limit = { NOT = { has_global_variable = hsi_applied } }
        # Select rule and apply every country amount here.
        set_global_variable = hsi_applied
    }

The active nonstandard flag names are infamy_generation_very_low, _low, _high and _very_high. The Standard setting has **no flag** (00_game_rules.txt:97–117); use the fallback value/table rather than testing an invented infamy_generation_standard flag. Persistence/idempotence still needs the reload check.

### Q6. Numeric debug_log syntax, pulse scope and startup hazards

Numeric localization is supported by vanilla patterns:

- diplomacy_l_english.yml:2414–2415 uses [SCOPE.sState('infamy_target_state').MakeScope.ScriptValue('state_population_global_share')|v%2] and the GDP-share equivalent.
- ip4_misc_01_l_english.yml:205 uses [GetPlayer.MakeScope.ScriptValue('two_spains_liberal_pivot')|2v].
- ip4_misc_01_l_english.yml:140 uses [Character.MakeScope.Var('regency_years').GetValue|v0].
- content_104_l_english.yml:1184 uses [GetGlobalVariable('krakatoa_temperature_drop').GetValue|2].
- 00_code_on_actions.txt:854,7399 demonstrates localization data functions inside debug_log.

Use named wrapper script values for built-in numeric accesses, avoiding the assumption that every numeric trigger name is itself a named localization script value. For example, **in the probe's script_values file**:

    hsi_probe_state_pop = { value = state_population }
    hsi_probe_state_gdp = { value = gdp }
    hsi_probe_unrec = {
        value = modifier:country_infamy_generation_against_unrecognized_mult
    }

After saving the actual state as hsi_state and the country as hsi_country, the supported composition is:

    debug_log = "HSI;STATE;pop=[SCOPE.sState('hsi_state').MakeScope.ScriptValue('hsi_probe_state_pop')|3];gdp=[SCOPE.sState('hsi_state').MakeScope.ScriptValue('hsi_probe_state_gdp')|3];base=[SCOPE.sState('hsi_state').MakeScope.ScriptValue('state_infamy_base')|3]"
    debug_log = "HSI;COUNTRY;unrec=[SCOPE.sCountry('hsi_country').MakeScope.ScriptValue('hsi_probe_unrec')|3]"

A variable workaround can instead evaluate inside the actual country/state scope with set_variable = { name = hsi_probe_value value = <numeric access or named value> }, then use .MakeScope.Var('hsi_probe_value').GetValue. For global totals, set_global_variable = { name = hsi_probe_global_pop value = global_population } and [GetGlobalVariable('hsi_probe_global_pop').GetValue|3] avoid a nonexistent world/root country. These are compositions of demonstrated APIs, **not boot-tested snippets**.

Do not print literal [state_population] or [global_var:hsi_rule_mult] as though script syntax were a localization data function. Do not use K, D, %, color/markup or abbreviated formatting for machine input. Verify grouping/decimal formatting and finite parseable values in the selected locale, with enough precision for the arithmetic.

There is no documented weekly code on_action in these inputs; finding 11 provides a delayed custom handler with a chosen country root. on_monthly_pulse has no root; on_monthly_pulse_country has a country root. A same-named weekly member in a JE/play is a different mechanism.

Startup hazards: no root or player identity at the early hook; GetPlayer/ROOT.GetCountry can be meaningless, and Observe changes the player assumption. Log using explicit scopes. state_infamy_value additionally requires root to be the aggressor/holder; a rootless startup loop does not create that root merely by entering c:TAG. Schedule a country-rooted handler for those measurements. The existing after-lobby GDP usage is evidence that the access is legal, not proof of settled GDP or safe early localization initialization. No frozen evidence establishes a debug_log startup crash, and I am not asserting one.

Include hook, sample index, measurement key and owner/component on **every** record. Currently only RULE carries the hook; both tick-0 hooks can otherwise produce ambiguous same-date records. Extract the HSI payload after engine log prefixes. Reject missing/duplicate records, nonnumbers and incomplete snapshots. To cross-check state_infamy_base independently, record the owner's homeland predicate as well as incorporated/capital: S:111 omits it, yet the 1.5 standing branch needs it.

### Q7. Ledger expressiveness

Findings 6–10 cover most missing inputs. The distinctions matter:

- Whole-state ownership changes across acts can be represented by distinct targets/standing rows. Changing borders, multiple historical owners inside one goal, or reconstructing a historical slice from several 1836 owner slices cannot be resolved from STATE_KEY alone.
- A subject state's owner and the play-leading overlord must be separate fields. Transfer/liberate subject use the subject as formula target and overlord as stakeholder; using the overlord's whole territory is wrong.
- An aggressor that is a 1836 subject **can** be named by its TAG. There is no is_subject exclusion in the state-infamy script. The ledger still lacks its historical type, overlord/role changes, and separate holder versus creator. I found no frozen-file basis to assert automatic infamy sharing with an overlord; that behavior must be tested if relied upon.
- An existing owner-held slice of a split region is an actual game state and can be a Conquer State target. A treaty taking only part of that slice needs a stated counterfactual subdivision or approximation.
- A historical target label without a 1836 TAG is expressly allowed by S:76 but ambiguously conflicts with “unknown ... TAG” refusal at S:137. Separate historical entity IDs from runtime output tags; validate only the latter against country definitions.
- A country definition existing is not proof the country is alive at the bookmark. Validate emit recipients against the observed roster and reconcile optional c:TAG ?= skips.
- Record LD, play roles/type, goal claim/drop/enforcement dates, primary conversion, general/unrecognized generation modifiers and their snapshots, aggressor type, released-country selection, state components and owners, and source/justification for standing/culture/claim/interest predicates. Record decay modifiers over time only if claiming their exact historical effect.

Additional refusals should cover state-goal cardinality, duplicate formula-state components, invalid booleans/enums, nonfinite numbers, absent required snapshots and claim/goal contradictions. Conquer State rejects claims; Return State requires them (03_conquer_state.txt:34–36; 21_return_state.txt:34–36).

### Q8. Can the checks fail in the intended direction?

| Check | What it can catch | False greens / required clarification |
|---|---|---|
| Static | Missing BOM, genuinely unbalanced braces, stale inputs actually hashed | Balanced but invalid script, ignored multiply, wrong scope, wrong constants, wrong formula, duplicate definitions, omitted dependencies. Brace counting must ignore quoted strings/comments. |
| Standard tick-0 save | Hook never applies a required positive amount, wrong recipient, wrong amount, duplicate application | Same wrong arithmetic in table and effect; omitted historical acts; empty table; wrong date/roster if not checked; accepting a guard anywhere as sufficient evidence. |
| Very Low save | Missing/wrong runtime multiplier with nontrivial positive fixtures | Wrong proportional oracle; all-zero/vacuous comparisons; no coverage of Low/High/Very High flag branches; thresholds/floors after rule scaling. |
| Error-log delta | Many load/scope/data-function/parser errors | Silent arithmetic mistakes; failed mod activation; a newly introduced occurrence matching a pre-existing “distinct” message; differing DLC/rules/locales or launch stages. Preserve full logs and contextualize counts, not just unique text. |
| Observer A/B | A descriptive result if actual initiation counts exist | A final active-play count is not six-year incidence; one matched seed does not establish an AI effect. It is correctly described as nongating. |

Save reading is a reasonable acceptance mechanism, **not yet a verified parser contract**. Do not regex-search infamy= without country record context. Handle the actual container/text format, object IDs, tag mapping, omitted defaults and numeric precision from a retained sample. ±0.05 is reasonable for delivery of explicitly emitted one-decimal constants only after storage precision is checked; it does not validate unrounded formula accuracy. For a proportional policy, a halved one-decimal amount may need two decimals (e.g. 0.5→0.25). The correct replayed-rule policy has separate expected values.

Treat missing positive-country fields as failures. Only map an omitted infamy field to zero after proving that serialization convention for valid, present country records. Locate hsi_applied within persistent global variables and verify the save's 1836.1.1 date and actual rule setting. Test parser failure paths with corrupted/truncated/missing records. No actual save was inspected in this review.

### Q9. Other load/fire/numerical issues

The initial-history claim has limited support: my search of common/history/ found only BOL's change_infamy = 50 at bol - bolivia.txt:39 and no literal has_game_rule. With START_INFAMY = 0 that supports the proposed baseline, but does not establish every startup effect's final runtime outcome.

Use additive on_action registration and the country-scope guards as above. A global guard can suppress repeat work; it cannot prove all optional country recipients existed or that every preceding line succeeded. Ensure BOL is excluded from **all** rule-specific output tables, retaining its vanilla 50.

There is no supplied evidence that this metadata.json shape fails, nor evidence that BOM alone guarantees script validity. Verify launcher discovery/active playset and actual load. No engine boot was performed here.

The spec's deliberate one-decimal rounding and ≥0.5 emission threshold are additional approximations: they can discard a real positive residual. State this in the documentary claim and apply filtering only after each rule-specific timeline. The country max of 1000 also exists and should be handled or explicitly bounded out of the ledger's supported inputs.

Finally, the spec repeatedly says Claude will commit artifacts (S:117,161). This review authorizes no commit, and Eric's supplied hard rule requires explicit approval for committing. The implementation workflow must retain that boundary.

## 3. What I would design differently

1. Define the historical reconstruction as an explicit fixed-snapshot approximation with sourced counterfactual choices.
2. Separate historical acts, real game goals, territory components and dated infamy events.
3. Keep holder, creator, victim, stakeholder and emitted 1836 country identities distinct.
4. Replay one bounded country balance with all accrual/refund/victim events.
5. Produce five independently replayed rule tables and select one in the rootless after-lobby handler.
6. Measure exact numeric accesses and goal-processing order before freezing formula constants.
7. Use a documented delayed country-rooted probe rather than an assumed weekly code pulse.
8. Keep engine-oracle tests separate from generated-file delivery and parser tests.
9. Bind outputs to generator, vanilla-script and complete measurement hashes.
10. Log initiation events for the optional A/B experiment.

## 4. Verdict

**REVISE** — the after-lobby delivery design is supported, but independent act decay, post-decay rule scaling and incomplete goal/event semantics produce wrong numbers that the proposed acceptance oracle can still approve.

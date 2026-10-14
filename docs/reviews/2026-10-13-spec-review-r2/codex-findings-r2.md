# Historical Starting Infamy — spec review R2

## 0. Disclosure

No memory summary was injected. I did not read any memory file or use remembered context from another session. I used the supplied v2 spec, the round-1 findings file and the current conversation, and reread relevant local vanilla scripts/documentation. The spec's EoR observations remain unverified references; I did not read EoR notes.

The developer instruction identifies this agent as Codex based on GPT-6. The exact model identifier and reasoning-effort footer are not visible through the permitted review interface.

Repository HEAD is **f6fae84**, confirmed with git log; the initial tracked worktree was clean. This was a read-only design review apart from this deliverable. No game was launched, no actual save or tooltip capture was inspected, and no network, herdr, other panes, other agents or git mutations were used. All numerical examples below are **synthetic**, checked with Python Decimal, not engine measurements.

Citation convention: **V2** denotes docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md at the supplied HEAD. Vanilla paths are relative to /Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/. Dispositions assess the specification, not nonexistent implementation or unperformed boots.

## 1. Round-1 disposition table

| Finding | Status | V2 citation and disposition |
|---|---|---|
| F1 — independent act decay | **RESOLVED** | §7, V2:150; tests at :158. One balance per country replaces separately decaying acts. New integration and same-date defects are N2–N3; they do not reinstate independent act decay. |
| F2 — scaling after decay | **REGRESSED** | §§7–8, V2:148–152,181–195. Five separately replayed tables and runtime selection are the right structure, but the per-goal calculation includes the rule and the replay again says to scale every event. This creates an inconsistent, potentially double-scaled amount contract (N1). |
| F3 — general generation modifier | **BOUNDED** | §§1,5–7,10, V2:11,99,130,148,218. Measuring and applying a 1836 proxy is acceptable for the declared fixed-snapshot model. H1 still needs a discriminating test (N4). The optional source none needs an explicit omission policy/justification if used. |
| F4 — unrecognized aggressor gate | **RESOLVED** | §§5,7, V2:93,110,116,146. Both actor and owner type gates are present. This is correct when the formula holder is the credited country; N7 explains the still-implicit identity assumption. |
| F5 — goal minimum and boundaries | **RESOLVED** | §§3,5,7, V2:35,86,107,148,156. Actual goal rows and a final goal minimum are specified. Rule/floor composition remains inconsistent in N1, and H1's measurement is incomplete in N4. |
| F6 — subject placement/predicates | **NOT ADDRESSED** | §§3,5,7, V2:37,98,148. Placement and independent stacking are fixed. The schema still substitutes creator for holder and omits the diplomatic-play-enemy predicate; its declared three predicates do not reproduce the four-part vanilla test without additional assumptions (N7). |
| F7 — liberation state set | **RESOLVED** | §§3,5, V2:38,107. Released-state components replace all opponent states. Ledger authors must still justify the selected released territory; arbitrary selection is not validated by the formula oracle. |
| F8 — conditional liberate_subject severity | **BOUNDED** | §5, V2:91. Explicitly excluding liberate_subject and reduce_autonomy is an acceptable scope reduction if the completed ledger supports the claim that no included act needs them. The faulty constant-severity path is removed. |
| F9 — accrual/refund/victim events | **BOUNDED** | §§5,7,10, V2:95–97,150,221. Explicit claim/drop/enforcement dates, backer refunds and victim reductions fix much of it. A one-claim/one-resolution model with omitted primary surcharges can be accepted as a historical approximation, not exact gameplay. Minimum remaining changes: define charge eligibility, pending resolutions, exclusions and the amount basis (N1,N9), plus same-date ordering (N3). |
| F10 — state slices and political scopes | **BOUNDED** | §§5,7,10, V2:82,92–114,146,217. Summing slices before the caps is a coherent hypothetical-state model. The bound is incomplete: creator/holder/target/stakeholder identities remain conflated, and overlapping or partial slice coverage has no policy (N7–N8). Add those identities or reject/explicitly bound such mappings. |
| F11 — nonexistent weekly code pulse | **RESOLVED** | §§3,6, V2:46,124. on_monthly_pulse_country is a documented country-rooted hook. Exact sample dates and root preservation in numeric evaluation must be checked; the hook name/scope itself is sound. |
| F12 — unverified change_infamy block | **RESOLVED** | §8, V2:178–195. Scalar country-scope additions eliminate the ambiguous arithmetic argument form. The additive rootless dispatch/global guard is supported by vanilla. |
| F13 — weak severity procedure | **NOT ADDRESSED** | §§3,6,9, V2:55,136,204. Full transcripts and screenshots improve the evidence format, but the chosen cases need not identify the order, reporting ambiguity is not a gate, and the clamp fixture is outside the allowed ledger types/current picker path (N4,N12). |
| F14 — exactness/decay/snapshot claims | **BOUNDED** | §§1,6,10, V2:11,140,216–224. The fixed-snapshot/base-decay framing is acceptable. The new numerical bound “difference is under 0.1” and the claim of measured cadence are unsupported; drop them or establish their assumptions (N10). Two-month share stability is a selection policy, not proof that initialization has settled (N6). |
| F15 — circular acceptance oracle | **NOT ADDRESSED** | §9, V2:203–209. Structural parsing, lifecycle and mutation tests are good additions, but oracle A lacks its input predicates, oracle B is not bound to the tooltip snapshot, and tolerance still permits wrong small values (N5–N6,N13). Numerical agreement is not yet a functioning independent oracle as written. |
| F16 — final-save AI metric | **RESOLVED** | §9, V2:210. The documented initiation hook supplies an event logger in both arms, and the result is correctly limited to one matched-seed observation. |
| F17 — incomplete freshness binding | **REGRESSED** | §§6–7,9, V2:138,154,203. Vanilla hashes improve coverage, but “every file” creates a self-referential manifest, the validation contract does not verify the manifest's entries, and generator identity is not checked. These are new/remaining false greens (N11). |

## 2. New findings

### N1. BLOCKER — §7: rule scaling is specified twice, and linear scaling conflicts with the goal floor

**Claim:** Per-goal computation multiplies by the table's rule multiplier and then floors at 1 (V2:148). The replay also scales every accrual, refund and reduction by that setting's multiplier before decay (V2:152).

**Evidence:** These are two different locations for the same operation. Applying both makes a 20-point unfloored Standard charge into 10 under Very Low at the goal stage, then **5** at the event stage. Alternatively, computing a Standard goal amount once and scaling that in the replay does not implement H1's final floor: max(1, 0.5) × 0.5 = **0.5**, whereas max(1, 0.5 × 0.5) = **1**. The two procedures are not interchangeable.

common/defines/00_defines.txt:1122–1125 defines the four rule multipliers. :1148 defines the goal minimum after multipliers. The exact engine order is H1's pending measurement, but v2 already contradicts its own stated H1 in either of the readings above.

**Proposed fix:** Give the amounts explicit definitions:

- A_r is the nominal goal charge computed ONCE under rule r, including the resolved engine ordering and final goal floor.
- The credited-country event is +A_r.
- A refund is −f × A_r, with no additional rule scaling.
- The victim reduction uses a separately defined, engine-verified goal-value basis; if it is A_r, the event is −0.5 × A_r, again without additional scaling.
- The timeline receives finished event deltas and performs only decay and country bounds.

A_r should be the nominal charge before the country's [0,1000] clamp, not silently the observed change to a saturated country balance. Clarify that distinction and check it if relied upon. Test both an above-floor charge and a floor-binding charge across all five rules. The refund/victim signs and constants are correct in V2:150; the unresolved issue is their amount basis, not their signs.

### N2. BLOCKER — §7: zero must be enforced during decay before the next event

**Claim:** Between events, decay linearly; clamp only “after each event” (V2:150).

**Evidence:** Read literally, this allows infamy to become negative between events and uses that negative value when adding the next goal. Synthetic case: start with 2, wait until the specified decay removes 5, then accrue 10. The stated after-event clamp gives max(0, 2 − 5 + 10) = **7**. A country that reached zero before the new goal must instead receive **10**. common/defines/00_defines.txt:1000 says infamy cannot be below zero.

The final interval to 1836.1.1 also has no specified terminal event/clamp, so an exhausted balance can be read off as negative. Filtering negative outputs away does not repair subsequent accruals that were already understated.

**Proposed fix:** Specify the recurrence, including initialization and the final horizon:

    I = max(0, I - 5 * elapsed_days / 365.25)
    I = min(1000, max(0, I + event_delta))

Start each reconstructed country at the declared initial balance (presumably zero on 1816.1.1), and perform the bounded decay again from its last event to 1836.1.1. Add an exhausted-balance-then-new-accrual test and a final-interval-to-zero test. If “a balance” was intended to imply continuous clamping, make that explicit; the existing text places the clamp after events only.

### N3. MAJOR — §§5,7: sorting by date does not determine a bounded timeline

**Claim:** Events have dates and are sorted by date (V2:95–97,150).

**Evidence:** Because the balance is clamped after individual events, same-day additions and subtractions do not commute. From zero, +10 followed by −10 ends at **0**; −10 followed by +10 ends at **10**. A same-day claim and full backer drop of one goal therefore changes its result if the sorting tie is reversed. This is allowed by the date checks: only resolution_date BEFORE claim_date is rejected (V2:156), so equal dates are valid.

The upper bound creates the same problem: starting at 990, +20 then −10 ends at 990; −10 then +20 ends at 1000. Both bounds are real defines (:1000–1001). CSV order, sort stability or goal_id alphabetization is not historical chronology.

**Proposed fix:** Define an explicit deterministic sequence/order key, including same-goal claim-before-resolution, and a policy for independent events sharing a day. If actual intraday chronology is unavailable, use and disclose a canonical order or end-of-day netting approximation; do not claim it reproduces engine chronology. Test both lower-bound and upper-bound tie cases, and ensure harmless ledger-row reordering cannot change the generated table.

### N4. MAJOR — §§3,6,9: the tooltip set does not necessarily identify H1, and ambiguity is only reported

**Claim:** The specified protectorate, conquest and lower/upper investment-rights clamp readings “fix” H1 before generation (V2:55,136,204,224).

**Evidence:** Even granting both C cases, the concrete targets and general modifier are unrestricted. Consider these two orders, both with a final goal floor:

    H1: raw → severity → explicit clamp → general multiplier → rule → floor
    H2: raw → severity → general multiplier → explicit clamp → rule → floor

For an actor with general factor 1, they produce the SAME entire numerical breakdown for all specified cases: moving an inert general operation provides no evidence about its position. Synthetic Very Low readings are:

| Case | Raw / severity / clamp | H1 | H2 |
|---|---|---:|---:|
| A: protectorate above floor | 80 / 0.5 / none | 20 | 20 |
| B: conquest with factors already in raw | 10 / 1 / none | 5 | 5 |
| C: below explicit minimum | 10 / 0.05 / [2,5] | 1 | 1 |
| C: above explicit maximum | 200 / 0.05 / [2,5] | 2.5 | 2.5 |

They disagree for other supported inputs: with general factor 1.1, that upper-clamp case is **2.75 under H1** and **2.5 under H2**. A general modifier exists and varies by actor (common/modifier_type_definitions/00_modifier_types.txt:409–424; common/technology/technologies/30_society.txt:353–362; personality_traits.txt:253–255). V2 does not require a nonzero measured general modifier in its ordering experiment.

The final floor is also not guaranteed to be exercised decisively. Moving it before the rule can fit all four synthetic readings above when the general factor is 1. With factor 0.95, only the lower-clamp reading changes, from 1 to 0.95, which is still within the stated 0.05 tolerance. A low-cost unclamped case of 1.2 under Very Low instead gives 1 versus 0.6 and would discriminate. This is a mathematical identifiability example, not a claim that the engine actually floors early; the defines comment favors a floor after multipliers.

Vanilla goal totals are displayed to **one decimal** (localization/english/interfaces_l_english.yml:6740–6742). Detailed transcripts may provide additional ordering evidence, but v2's numerical acceptance checks only totals. “Any other order that also fits is reported” (V2:204) still permits generation under an order not established by those readings.

**Proposed fix:** Design the measurements to activate each disputed boundary: a known nonzero general modifier interacting with an explicit clamp, a decisively binding final floor under a nonstandard rule, and the severity/clamp cases. Capture exact numeric inputs and sufficiently precise outputs, as well as meaningful breakdown lines. Enumerate candidate noncommuting orders and refuse generation while two orders that give different results for supported ledger inputs still fit. Do not demand a unique ordering of ordinary adjacent multiplications: general × rule and rule × general commute and are functionally equivalent.

### N5. MAJOR — §§6,9: oracle A's 1836 inputs are not in the measurement schema

**Claim:** Feed the generator “measured 1836 slices with 1836 standing and factors” to reproduce every SIV value (V2:131,204).

**Evidence:** STATE records (V2:129) include population, GDP and owner standing. COUNTRY records (:130) include two generation modifiers and infamy. Neither records the actual holder-relative homeland/language, claim, scripted unification, adjacency, interest tier, current actor/owner country type, or the bonus booleans needed for an 1836 SIV reconstruction.

Those are direct inputs to common/script_values/00_infamy_values.txt:124–169,172–193,195–255,262–277. Historical flags in goal_states.csv (:112–113) are explicitly historical judgments, not an independent observation of their 1836 values. If oracle A reuses those flags, a historical mismatch can reject correct arithmetic; if it tunes them to fit SIV, it can approve incorrect arithmetic. country_infamy_value also sums EVERY actual state of the target (:287–295), while the existing STATE coverage is only ledger slices. A target total cannot generally be reconstructed from an arbitrary subset of its states.

Country-rooted monthly dispatch is a sound starting point. It does not by itself establish that a localization call on a state's MakeScope preserves the original country ROOT. The vanilla .MakeScope.ScriptValue examples at diplomacy_l_english.yml:2414–2415 evaluate root-independent share values; they do not prove that particular SIV call chain.

**Proposed fix:** Emit complete 1836 diagnostic inputs keyed by holder + owner slice + sample, including all actual branch predicates and bonus booleans. Expand coverage to every current state of each country whose country_infamy_value is checked. Keep diagnostic 1836 inputs separate from historical flags. Evaluate SIV in actual script math within the country-rooted handler, optionally materialize it in a variable before logging, and log/assert the root identity. Check the same state under two actors with different factors. If predicates are instead derived from vanilla data, specify and hash that additional extraction pipeline.

The historical model may continue assuming bonus booleans absent. The diagnostic mode must honor the actual 1836 booleans when claiming equality with the engine.

### N6. MAJOR — §§6–7,9: oracle B is not bound to the snapshot it measures

**Claim:** Capture tooltips before Observe/unpause, select the last monthly population/GDP snapshot, and reproduce the tooltip totals from the measurement (V2:136–140,204).

**Evidence:** The tooltips occur at tick 0; the chosen reconstruction shares occur in April. Country modifiers and SIV records are also monthly. No rule says oracle B must use the tick-0 STATE/COUNTRY values associated with each capture, or captures diagnostic states/actors outside the ledger. Target choice is deferred to implementation.

The 2% last-two-sample check does not solve this temporal mismatch. A share series 1.00, 1.20, 1.21, 1.22 from tick 0 through the three monthly samples passes the final test (about 0.83%), despite a 22% difference from the tooltip snapshot. Below the soft cap, an uncapped contribution of 4.00 versus 4.88 changes an incorporated neutral state's raw cost by 0.88; under Very Low a Conquer State total changes by 0.44. Thus correct arithmetic can fail the 0.05 tooltip oracle.

Further, a fixed-snapshot generation modifier cannot silently mean a different month for each country, and slices composing one component must share a global denominator and sampling instant. A country-rooted pulse supplies a root; the supplied pulse documentation does not promise all samples occur at the asserted exact calendar date/initialization stage.

**Proposed fix:** Give every tooltip fixture its capture ID, date/tick, holder, target, raw components, modifiers and rule, and evaluate it using the SAME contemporaneous records. Measure the union of ledger and diagnostic targets. Define which COUNTRY modifier snapshot supplies historical reconstruction. Select one complete, aligned snapshot for reconstruction, and separately use each contemporaneous snapshot for oracle A. Verify actual monthly firing dates rather than relying solely on their names.

Describe the 2% rule as a sampling policy, not proof of initialization convergence. Define zero handling: consecutive zero shares should have change zero; a zero-to-positive transition needs an explicit failure/absolute-tolerance rule. Ordinary relative change with a zero previous share is undefined, and non-finite-number rejection does not supply that rule. Legitimate ongoing economic change can also violate 2%; if that happens, report the refused measurement rather than choosing a convenient sample without a declared policy.

### N7. MAJOR — §§5–7: “credited” still substitutes for the formula holder, and rebellion lacks an enemy check

**Claim:** credited is the goal creator, credited_type gates unrecognized discounts, target_is_subject_of_credited drives subject reductions, and SIV ROOT equals credited (V2:92–99,131,146–148).

**Evidence:** Vanilla documents root as the **holder country**, with creator_country separate (common/war_goal_types/war_goal_types.md:265–273). Goal infamy is credited to the creator in localization/english/interfaces_l_english.yml:6740–6742. Goals can be added for another participating country (war_goal_types.md:129–130; 03_conquer_state.txt:9; 26_transfer_subject.txt:8). The state formula's culture, claims, adjacency, interest and unrecognized modifier use root (:124–277), not a generic creator alias.

The rebellion block additionally requires is_diplomatic_play_enemy_of = root, as well as being root's subject and the play initiator (00_annex_country.txt:79–86). V2's three fields do not encode that enemy predicate. Nor do they specify an invariant guaranteeing it. Transfer Subject's target is the subject and its stakeholder is the overlord (26_transfer_subject.txt:34–37); a historical-owner victim label alone does not encode that distinction for validation and counterfactual mapping.

**Proposed fix:** Add holder and goal target/stakeholder identities, use holder inputs in root-dependent calculations, and keep credited solely for the payment timeline and whatever engine processing is demonstrated to use the creator. Record the exact enemy predicate or define a combined sourced rebellion predicate containing all vanilla conditions. Alternatively, explicitly restrict every historical mapping to creator = holder, identify the formula target independently, and reject cases outside that bound. The current spec does neither.

The existence of a subject aggressor TAG is not itself a problem. The problem is substituting one political role for another; no unsupported automatic overlord infamy-sharing rule is assumed here.

### N8. MAJOR — §§5,7: slice summing is coherent, but overlapping and partial components are not defined

**Claim:** A component sums its selected 1836 owner slices before applying one baseline/cap/floor; components are then summed into a goal (V2:107–114,146–148). Duplicate IDs are refused (:156).

**Evidence:** The merger itself is coherent for a declared hypothetical single historical state. Two slices with uncapped population contributions 12 each, GDP zero and neutral incorporated standing give:

- One merged state: 5 + capped(24) = **20**.
- Two separate states: 2 × (5 + capped(12)) = **32**.

That difference follows exactly from vanilla's baseline and per-state caps (00_infamy_values.txt:34–75); it is not evidence that the declared merger is mathematically wrong. It does make component boundaries a substantive modeling input.

Distinct component IDs can currently reuse the same (state_key, owner TAG) slice within one goal, or one slices_1836 list can repeat a TAG. Duplicate-ID checks do not detect either double count. No fraction/province selector can represent only part of an 1836 slice; no restriction or substitution policy declares what happens when a historical demand does exactly that. The label “split-region approximation” does not resolve overlapping components or an unrepresentable partial slice.

The revised refusal of both exclusive flags also needs a semantic definition. Vanilla's if/else_if selects one branch even when both underlying predicates are true (homeland/language at :124–169, claim/unification at :172–193). Branch exclusivity is not proof that those predicates cannot both be true.

**Proposed fix:** Define components as disjoint historical formula states. Require unique slice members and nonoverlapping slice coverage within each goal; allow reuse across different goals/acts where historically appropriate. Declare full-slice-only coverage and reject partial mappings, or add sourced coverage weights/province mappings BEFORE caps and standing. Record the boundary judgment in derivation output. Specify whether flags represent raw truths (allow both and follow vanilla precedence) or selected branches (mask the lower branch and explain that encoding).

Use max(global_population,1) and max(global_gdp,1) consistently when constructing shares; the denominator safeguard is stated in V2:31 but omitted from :146's written equation. If unusable global totals are instead refused, specify that alternative explicitly.

### N9. MAJOR — §§5,7,10: pending goals and exclusion reasons can remove valid events from other countries

**Claim:** All dates must be inside 1816–1835; every goal has a resolution kind/date; absent credited countries and below-threshold goals can have exclude_reason (V2:95–100,116,156).

**Evidence:** A goal claimed in late 1835 and resolved in 1836 has already accrued infamy at the read-off horizon, but its future resolution is outside the window and is refused. There is no pending/null-resolution value. The scope is conduct during the window, not exclusively campaigns completely resolved inside it (V2:9,116). This is a representational defect even without identifying a particular historical act.

An absent creator can still have an enforced goal that reduces a surviving victim's balance. Blanket removal of an excluded goal would remove that victim event. Yet credited is required to be a runtime TAG (:92), only credited-country modifiers are measured (:130), and a TAG absent from country definitions is refused regardless of exclude_reason (:156). There is no historical creator/fallback-input representation for a vanished actor with no usable runtime definition.

Likewise, below_threshold is attached to a GOAL, whereas filtering is defined for a country's final RULE-SPECIFIC balance (:152). An old goal with no isolated residual can keep the pooled balance up, and a Standard-zero country can be positive under Very High. Dropping that goal before replay would revive the original mathematical error in another form.

Finally, the input has no charge-eligibility field or explicit counterfactual rule for automatically supplied initial goals. Vanilla starting target goals default to no infamy (common/diplomatic_plays/diplomatic_plays.md:8–9), and dp_revolution uses annex_country with initial initiator infamy disabled (00_diplomatic_plays.txt:550–559). Saying that the analog “generates infamy” (:116) is a ledger-author inclusion criterion, but the goal type alone cannot enforce it.

**Proposed fix:** Bound the inclusion window by claim date and replay only events at/before 1836.1.1; permit pending or later resolutions. Separate “do not emit this country's balance” from “do not calculate this goal/event.” Preserve surviving-victim events from excluded creators using explicit historical actor IDs and declared fallback modifiers where necessary. Remove below_threshold as a pre-replay goal exclusion; apply the threshold only to each finished country/table. State whether all ledger goals are deliberately charged secondary/initiator demands; otherwise encode eligibility/play role and reject zero-charge analogs.

The one-claim/one-resolution historical approximation is acceptable if intentional. It does not justify discarding a goal whose single claim predates the horizon merely because its resolution is later.

### N10. MINOR — §§6,10: neither the “under 0.1” bound nor decay cadence is established

**Claim:** The engine displays weekly steps, continuous decay differs by under 0.1, and BOL's monthly decay is a free cadence check (V2:130,220).

**Evidence:** localization/english/interfaces_l_english.yml:6298 labels a decay RATE “/ week” and its yearly base. It does not establish weekly changes to the stored balance. common/defines/00_defines.txt:1006 supplies five per year, not the engine's update denominator, phase or rounding behavior. Two readings a month apart can match daily, weekly or monthly implementations; they do not identify update cadence.

BOL is also an uncontrolled normal-game country. The probe does not log its net country_infamy_decay_mult or relevant accrual/refund/victim events. Excess influence can alter decay (00_code_static_modifiers.txt:596–600), so a disagreement with base five need not be a cadence bug. I have not measured BOL's actual net modifier or any such events.

Under a SPECIFIED weekly step size, constant rate and denominator, a single-phase discretization error can indeed be small. The spec does not establish those assumptions, so I am not asserting a measured bound violation; I am rejecting an unsupported numerical guarantee.

**Proposed fix:** Keep continuous base decay as the declared model choice. Remove “the engine displays weekly steps” and “difference is under 0.1,” or replace them with an explicitly conditional, derived bound whose assumptions are verified. If measuring cadence, sample successive tick/day/week/month boundaries with a known constant net modifier and no new events, log the modifier, and record the raw precision. Treat ordinary BOL monthly readings as observations, not a conclusive cadence oracle.

### N11. MAJOR — §§6–7,9: the manifest is self-referential, and checking its hash does not check its files

**Claim:** manifest.sha256 covers “every file in the directory” (V2:138); the generated header hashes the manifest, and validation compares header hashes to the current manifest/vanilla/ledger (V2:154,203).

**Evidence:** The manifest itself is a file in that directory. A digest of its prior/empty content becomes wrong when the manifest is written; including the manifest in its own finished-content listing is self-referential. The procedure must explicitly exclude it.

Even with that corrected, hashing the manifest alone is not verification of the entries it contains. Editing probe-extract.log while leaving manifest.sha256 unchanged leaves its header-bound hash unchanged, so the stated validator can still pass. The generator version is recorded (:154) but :203 does not require matching the current generator/formula/probe-extractor implementation. A formula.py edit can leave all checked data and vanilla hashes unchanged.

Oracle C may also use the investment-rights treaty-article wargoal, whose file is absent from the stated vanilla input set (see N12). A war_goal_types hash does not bind a different live treaty-article formula.

**Proposed fix:** Build a canonical manifest over named immutable evidence files, excluding itself and any generated artifact that embeds its hash. Verify every listed content digest, plus missing/unexpected files according to a declared policy. Bind and check generator/formula/extractor identity or an enforced version. Hash the actual oracle source files, including treaty_articles when used. Add failure-direction checks for a changed extract with an unchanged manifest and for changed formula code with unchanged data.

### N12. MAJOR — §§5–6,9: the clamp fixture has no specified supported generator/UI path

**Claim:** Oracle C is foreign_investment_rights, fed to the same generator for H1 acceptance (V2:136,204).

**Evidence:** foreign_investment_rights is absent from goals.csv's allowed wargoal list (V2:91), and no diagnostic-only fixture path is defined. It cannot be represented as an ordinary valid ledger goal under that schema.

The legacy common/war_goal_types/07_foreign_investment_rights.txt sets skip_build_list (:8) and target_type = treaty_article (:17). war_goal_types.md:97–98 says it is converted to an investment-rights article. The current article has its own wargoal block in common/treaty_articles/07_foreign_investment_rights.txt:507–541. That block supplies severity 0.05 and bounds 2–5 but has no legacy loyal/rebellious multiply blocks; the legacy goal does have them (:64–94). The ordinary legacy picker therefore cannot simply be assumed to expose the desired diagnostic, and recording the display label alone does not identify the evaluated formula.

This is also a limitation of my round-1 clamp example: naming the legacy war-goal file was insufficient to specify an operational capture route. V2 needs that route to make the measurement concrete.

**Proposed fix:** Either add an explicit diagnostic fixture format/calculator for the actual investment-rights article, with its source path and target/role inputs, or choose an allowed ledger goal with explicit clamps, such as regime_change, and establish valid concrete targets. Test the capture path during probe development and include both diagnostic input coverage and source hashes. Do not reject the fixture as unsupported, silently bypass validation, or equate legacy/article formulas in subject cases.

### N13. MAJOR — §9: delivery tolerance can accept zero or doubled small values, and three runtime branches remain untested

**Claim:** Two-decimal outputs are emitted at 0.05 or above, while save equality allows an absolute error of 0.05 (V2:152,205–208).

**Evidence:** For an emitted expectation of **0.05**, a present country record with infamy = **0** is within tolerance; infamy = **0.10** from duplicate application is ALSO within tolerance. Presence of the country/field and hsi_applied does not repair that numerical false green. The no-hook mutation may still fail because the guard is missing, while a handler that sets the guard but skips small entries can pass. The text does not specify a stricter positivity check to override its equality tolerance.

The empty-table rule also needs separation from diagnostic fixtures. A fully correct Very Low table can be empty while Standard is positive: a synthetic pre-decay charge of 6 followed by five points of decay gives Standard 1 and Very Low 0. Step 4 says “the same” as step 3, which rejects an empty table. If it inherits that rejection, it rejects a correct result; if empty tables are accepted, a separate nontrivial sentinel is required to test the branch.

Only Standard and Very Low are booted. Low, High and Very High select separate helpers via separate predicates (V2:181–185). Arithmetic tests for five tables do not execute those engine-side dispatch branches.

**Proposed fix:** Establish actual save storage precision from the retained sample and choose a tolerance well below the smallest emitted amount (for example 0.005 if the observed storage supports it). Explicitly require expected positive values to be positive, and mutate boundary entries in the failure-direction tests. Distinguish valid empty historical tables from a diagnostic dispatch test that has a guaranteed, distinguishable positive amount in each branch. Exercise all five runtime selections with such a fixture, retaining the two real-table acceptance boots.

No actual save is among the frozen inputs, so I cannot verify the promised country definition field, global-variable container, compression/text handling or omitted-zero convention. The retained fixture must establish these before parser tests become evidence. Likewise, do not count a silent log diff as proof the correct mod was loaded.

## 3. Unresolved disagreements to surface to the owner

The five-table, scalar-effect delivery structure is sound. Vanilla supports additive on_action registration (_on_actions.md:115–128), a rootless after-lobby has_game_rule check and global-variable write (00_code_on_actions.txt:10–19,89–92), and scalar country-scope change_infamy (bol - bolivia.txt:39; events/tanzimat_events.txt:586). Standard as else matches the absence of its flag (00_game_rules.txt:97–117). I found no proven syntax/load failure in that shipped skeleton. V2:190's 17.4 is an illustrative placeholder, not a validated derived value.

The remaining choices that need to be explicit are:

- **Historical scope:** I would accept a documented one-claim/one-resolution, base-decay model. Omitting a primary-demand surcharge can omit half a goal's base charge (00_defines.txt:1064), so it is not a rounding error. Describe the mod as reconstructing that chosen counterfactual, and decide whether claimant/holder equality and whole-slice-only territory are additional restrictions.
- **Measurement gate:** Merely reporting alternative H1 orders does not resolve them. Ambiguity that changes supported outputs should block generation; swapping commuting multiplication steps should not. The probe needs independent actual predicates and capture-time inputs.
- **Decay claim:** A weekly display unit is not evidence of weekly stored steps. Keep the continuous approximation without an unsupported error guarantee unless a controlled test or conditional proof establishes it.
- **Exclusions:** A creator absent in 1836 can still affect a surviving victim. Preserve those events separately from output eligibility, and allow demands unresolved at the start-date horizon.
- **Verification scope:** Structural parsing and mutation tests address delivery, but cannot verify historical territorial judgments or hand-authored predicates. Those remain documentary/review inputs; give them enough evidence to audit. A generated table and golden file can still share the same model error.
- **Hook rationale:** The after-lobby hook is appropriate, but V2:197 still overstates what vanilla proves. Its comments establish lobby/player timing, not exclusive game-rule availability during the earlier hook. If the two RULE records are equal, that is an observation, not a failed probe.
- **Approval boundary:** V2:138,212 still say to commit artifacts automatically. Eric's supplied hard rule requires explicit approval before committing. This review did not authorize or perform a commit.

## 4. Verdict

**REVISE** — v2 fixes the broad architecture, but its scaling and bounded-timeline contracts remain inconsistent and its new measurement/verification gates can pass without establishing the formula they are meant to validate.

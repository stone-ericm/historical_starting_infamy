# Historical Starting Infamy — spec review R3

## 0. Disclosure

No memory summary was injected. I did not read any memory file or use context remembered from another session. I used the supplied v3 spec, the round-2 findings, the current conversation and relevant local vanilla scripts/documentation. The EoR observations cited by the spec remain unverified references; I did not read EoR notes.

The developer instruction identifies this agent as Codex based on GPT-6. The exact model identifier and reasoning-effort footer are not visible through the permitted review interface.

Repository HEAD is **0c9b379**, confirmed by git log; the initial tracked worktree was clean. I wrote only this deliverable. No game was launched, no actual save or tooltip transcript was inspected, and no network, herdr, other panes, agents or git mutations were used. Numerical examples below are **synthetic calculations**, checked with Python Decimal, not engine measurements.

**V3** means docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md at the supplied HEAD. Vanilla paths are relative to /Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/. This is the final requested review round; the remaining choices are separated from defects for the owner's decision.

## 1. Round-2 disposition table

| Finding | Status | V3 section/line and assessment |
|---|---|---|
| N1 — double scaling / amount contract | **RESOLVED** | §7, V3:153–159. A_r is a nominal charge computed once per goal/rule, and the timeline applies no further scaling. Refunds use the nominal amount independently of country saturation. H2's victim basis is now an explicit assumption (§3, :57; §10, :239), not something the oracles have measured. |
| N2 — zero clamp during decay | **RESOLVED** | §7, V3:161; tests :171. Initialization, pre-event zero clamp, post-event [0,1000] clamp and final bounded decay are explicit. The negative-infamy-debt defect is gone. |
| N3 — same-day ordering | **BOUNDED** | Acceptable. §7, V3:161; §10, :238. Accrual before reduction before refund, then goal_id, is deterministic and expressly a counterfactual convention. It is not engine chronology, and no longer claims to be. |
| N4 — insufficient ordering experiment | **RESOLVED** | §3, V3:55; §6, :141; §9, :217. Nonzero general modifier, allowed explicit-clamp cases, a binding-floor case and refusal of materially ambiguous fits address the original counterexample. With precise synthetic inputs these cases identify the principal H1 order class. P3 concerns the still-undefined observation/equivalence contract, not a claim that these fixture types can never discriminate. |
| N5 — missing oracle-A inputs / ROOT | **RESOLVED** | §6, V3:134–136; §7, :151; §9, :217. DIAG supplies the actual 1836 predicates and bonuses, materializes SIV in state scope under the monthly country ROOT, and logs root identity. The old country_infamy_value diagnostic was removed, so its incomplete-target-state coverage issue is not retained. The monthly method is scriptable; tick-0 fixture inputs remain a separate issue (P2). |
| N6 — mixed snapshots / zero stabilization | **RESOLVED** | §6, V3:131,141,145; §9, :217. Samples are self-contained, oracle B is bound to its capture-time snapshot, reconstruction takes one aligned monthly snapshot, and zero transitions are specified. P2 identifies a missing way to populate some of the newly required tick-0 inputs. |
| N7 — holder/creator and rebellion | **BOUNDED** | Acceptable. §5, V3:94–105; §10, :234–235. Holder = creator is an explicit scope restriction, target/stakeholder are distinct, and loyal/rebellious flags encode the full predicates including enemy status. A ledger requiring third-party-created goals would need a scope change, not silent substitution. |
| N8 — slice coverage / raw predicates | **BOUNDED** | Acceptable. §5, V3:108–119; §7, :151,169. Whole slices only, disjointness within each goal, duplicate-slice refusal, raw truths with vanilla precedence and denominator floors are explicit. Refusing a partial historical demand narrows coverage; it does not make the declared merged-state calculation incoherent. |
| N9 — pending/excluded actors/events | **BOUNDED** | Not yet acceptable as a complete contract. §5, V3:95,100–105,121; §7, :155–169. Pending/later resolutions, retained absent-actor events and final-only thresholds address the major event-loss paths. Minimum remaining changes: give absent holders an unrecognized-generation fallback (P1) and choose one exact horizon boundary (P4). |
| N10 — unsupported decay bound/cadence | **RESOLVED** | §10, V3:236. Continuous base decay is a declared model, no engine cadence or numerical error bound is claimed. COUNTRY also records the decay modifier (:135); ordinary monthly observations are no longer sold as a cadence measurement. |
| N11 — manifest/self-reference/freshness | **RESOLVED** | §7, V3:165–167; §9, :216; tests :171. Named evidence excludes the manifest itself, entries are rehashed, generator sources and vanilla/rule inputs are bound, and changed-file/unchanged-manifest failure is tested. Define the generator inventory as source files in implementation, as discussed below. |
| N12 — unsupported clamp fixture | **RESOLVED** | §5, V3:93; §6, :141. Regime Change is an allowed ledger goal with actual severity 0.1 and explicit 3/10 bounds (common/war_goal_types/20_regime_change.txt:42–44). No legacy investment-rights picker/article equivalence is required. Concrete legal targets still have to be found during probe development, as the spec states. |
| N13 — tolerance/empty tables/branches | **BOUNDED** | Acceptable. §7, V3:163; §9, :218–225. Positive-value checks, storage-based tolerance below half the minimum emitted amount, boundary mutations and valid empty tables fix the demonstrated false greens. Three unbooted dispatch branches are explicitly an accepted residual. Static flag validation does not execute them, but this is now disclosed rather than represented as measured coverage. |

No round-2 blocker survives as a defect in the written replay recurrence.

## 2. New findings

### P1. MAJOR — §§5–7: absent holders have no defined unrecognized-generation modifier

**Claim:** An actor without a holder_tag_1836 is still computed so its victim reductions are retained; it uses general_mult_source = none (V3:95,105,121). Component calculation still uses “unrec_mult of the holder” for a recognized holder against an unrecognized/decentralized owner (V3:151).

**Evidence:** COUNTRY measurements are obtained for holder TAGs, fixture holders and BOL (V3:135). An actor explicitly without a 1836 TAG cannot supply that measured value. The fallback at :95,:105 and §10 :232 specifies only the **general** generation modifier. No ledger field or fallback supplies country_infamy_generation_against_unrecognized_mult for that actor.

The distinction matters in vanilla: common/script_values/00_infamy_values.txt:262–277 applies root.modifier:country_infamy_generation_against_unrecognized_mult when both type conditions hold. It is not the general modifier.

Synthetic case: an absent recognized holder enforces a goal against an unrecognized surviving target. With a neutral pre-discount state value of 20, unrec_mult = 0 produces charge 20 and H2 victim reduction −10; unrec_mult = −0.1 produces 18 and −9. Both choices are numerically meaningful; the written inputs do not select one. Although the holder's own balance is not emitted, its surviving victim's balance can change.

**Proposed fix:** Define every absent-actor numeric fallback explicitly. The minimum change is “actors without a 1836 TAG use general_mult = 0 and unrec_mult = 0,” listed as an approximation in §10 and derivation output. Alternatively supply sourced per-actor overrides. Refuse missing modifier data for present actors, and test an absent recognized holder whose surviving unrecognized victim already has positive infamy. Choosing the fallback value is an owner judgment; leaving the required value undefined is a defect.

### P2. MAJOR — §§6,9: oracle B's tick-0 operand source is still missing

**Claim:** Oracle B uses tick-0 sample records from the same fixture capture (V3:141,217). DIAG, the record containing holder-relative formula predicates and SIV, is emitted only in country-rooted monthly samples (V3:136).

**Evidence:** Tick-0 hooks are rootless (:129). Their STATE fields contain owner standing, population/GDP and base (:134); COUNTRY contains country modifiers (:135). Neither contains tick-0 holder-relative homeland/language, claim/unification, adjacency, interest or a root-dependent SIV/raw country total. Fixtures B and D require those factors, and the regime-change raw input is a sum of holder-relative values over the target's states (common/war_goal_types/20_regime_change.txt:46–51; common/script_values/00_infamy_values.txt:287–295).

Entering c:TAG or state scope inside a rootless startup chain does not by itself supply the country ROOT that state_infamy_value reads. Monthly DIAG can do that, but its later values are expressly forbidden as replacements for the tick-0 fixture inputs.

A full tooltip can supply applied factors or an engine-computed raw subtotal. That is a legitimate alternative; the spec currently records breakdown text without defining it as a typed operand source. I am not claiming that the game makes a tick-0 fixture impossible. I am identifying an unfilled edge between the recorded data and the proposed oracle.

**Proposed fix:** Choose and specify one of these routes before implementing oracle B:

- Capture country-rooted diagnostic operands at the fixture's tick 0, with a real ROOT assertion; or
- Define a diagnostic fixture input containing the raw scripted infamy/subtotals and applied factors extracted from that exact tooltip, with formatting/precision metadata. In that route oracle B tests the subsequent goal-processing order; do not count replaying a transcribed subtotal as independent validation of the state formula. Monthly oracle A provides that separate check.

Cover every target state needed for a fixture country total. Also either include fixture-only holders in the monthly guard or require the chosen fixture holder to be a ledger holder: :129 guards to ledger holders plus BOL, while :135 separately promises fixture-holder records. Do not silently import historical flags, February DIAG or April modifiers into a January fixture.

### P3. MAJOR — §§3,6,9: “one fitting order class” needs an observation and equivalence definition

**Claim:** Every candidate placement is registered, adjacent multiplications are one order, and two fitting classes refuse generation (V3:55,141,217).

**Evidence — the new fixtures can work with precise operands:** I enumerated all 24 permutations of clamp C, general factor G, rule factor R and floor F for synthetic fixture inputs. Severity was already applied to the following raw values, G = 0.95 and R = 0.5:

| Fixture | Input before C/G/R/F | Clamp | H1 nominal result |
|---|---:|---|---:|
| A | 40 | none | 19 |
| B | 10 | none | 4.75 |
| C below minimum | 2 | [3,10] | 1.425 |
| C above maximum | 20 | [3,10] | 4.75 |
| D | 1.5 | none | 1 |

With exact totals, only C→G→R→F and C→R→G→F fit, which are the intended adjacent-multiplication equivalence class. Thus the original inert-modifier counterexample is addressed.

**Evidence — the actual observations are formatted:** Vanilla presents goal totals with one decimal (localization/english/interfaces_l_english.yml:6740–6742), country-state entries with one decimal (diplomacy_l_english.yml:2430), population/GDP shares as percentages with two decimals (:2414–2415), and severity with two decimals (:2433). A nominal 1.425 is displayed as 1.4; their difference is 0.025. The 0.005 tolerance in V3:217 applies to oracle A, not a defined formatting-aware comparison for B. An exact comparison to transcribed text would reject correct arithmetic; an arbitrary loose epsilon could admit a different order.

Using one-decimal totals in the same enumeration also admits C→R→F→G. Its D result is 0.95, displayed as 1.0, whereas H1's result is 1, also displayed as 1.0. The full ordered breakdown may distinguish them; the gate must specify how those labels/lines constrain a candidate rather than silently relying on totals alone. This example does not prove that complete transcripts are insufficient.

**Evidence — class/domain and candidate coverage:** “Differ on any supported ledger input” (:55) does not say whether it means the current loaded goals across five rules or the entire allowed input domain. Adjacent multiplication is also not the only functional equivalence: with the supported regime clamp [3,10] and floor 1, C(F(x)) = F(C(x)) = C(x); with no clamp, C is identity. C→F→G→R and F→C→G→R are numerically equivalent on that domain even though swapping them is not adjacent multiplication.

Finally, the registry description varies C/G/R/F while fixing severity before them. The spec says the files do not establish the engine order. If severity-before-clamp is a separate fixed premise, the captures must establish it rather than treating registry uniqueness as proof of a stage absent from the registry.

**Proposed fix:** Specify:

1. Typed operands and a fit predicate that reproduces the relevant UI formatting/rounding, or compares against higher-precision engine values. Encode the informative ordered labels/lines as evidence too.
2. The equivalence domain. A practical choice is all current supported ledger goals across all five rules, plus diagnostic fixtures; retain alternative algorithms only when they give the same nominal A_r values there, not merely the same final rounded country balances. A universal domain instead needs specified parameter bounds and a genuine equivalence method, not a few sampled test numbers.
3. A numerical-function equivalence rule broader than sorting adjacent multiplications, with structural evidence handled separately.
4. Zero fitting classes as a measurement/model failure; two materially different fitting classes as ambiguity requiring another discriminating observation.
5. Either severity in the candidate registry or an explicit separately verified severity-before-clamp assertion.

The existing refusal principle is correct. The defect is that its decisive terms are not yet an implementable, precision-aware contract. Do not promise that fixture *types* guarantee uniqueness before their actual operands and observed precision are known.

### P4. MINOR — §§5,7: the exact 1836-01-01 resolution boundary is contradictory

**Claim:** resolution_date may be after 1835-12-31, “then it has no effect on the 1836 balance” (V3:102). Event filtering instead omits only dates **after 1836-01-01** (:159).

**Evidence:** A resolution on 1836-01-01 is excluded by the field definition but retained by the event rule. The recurrence processes the retained event at its read-off horizon (:161). These conventions can differ by a complete refund, not just one day of decay.

Synthetic example: accrue 10 on 1835-12-31, then fully refund it on 1836-01-01. Excluding the refund leaves approximately **9.98631** before output rounding; including it leaves **0**.

**Proposed fix:** Define whether the horizon includes resolutions dated 1836-01-01 or means the beginning of that day before its events, and make :102,:159 and the tests agree. Add exact-boundary tests for December 31, January 1 and January 2. The choice of date convention belongs to the owner; the conflicting definitions do not.

## 3. Owner decisions: choices, not defects

The following are legitimate choices if the owner accepts their stated effect on the documentary claim. They are not reasons to reopen resolved arithmetic findings.

- **Historical scope and identity.** Holder = creator, excluding third-party-created goals, excluding liberate_subject/reduce_autonomy, and refusing partial slices are explicit restrictions. They may omit real acts; a complete ledger must show what is omitted. Whether that coverage is sufficient for the intended mod is an owner judgment.
- **Snapshot and state boundaries.** Summing whole 1836 slices into one hypothetical historical state before caps/baseline is coherent. It intentionally differs from pricing those slices as separate states. The component boundary and historical predicates are documentary judgments, not facts validated by oracle A.
- **Decay and initial balance.** Starting at zero on 1816.1.1, using continuous 5/365.25 decay, ignoring modifiers and using a canonical daily order are well-defined approximations. No engine-cadence accuracy bound is now claimed.
- **Primary-demand surcharge and historical timing.** Omitting the half-base surcharge and replacing claim/enforcement chronology with one claim and one resolution can materially change results. It is now disclosed. Owner acceptance of that reconstruction is distinct from a programming defect.
- **H2.** The signs/constants are supported by defines :1172–1175, but the exact victim-reduction basis remains unmeasured. Accepting −0.5×A_r is an explicit modeling hypothesis; the current SIV/tooltip oracles do not verify enforcement deltas. A controlled enforcement experiment is an optional way to replace the assumption with evidence.
- **Three unbooted dispatch branches.** The residual is clear at V3:225. Static flag validation and the common code shape lower the risk but do not execute those branches. Accepting that coverage tradeoff is reasonable if it remains disclosed.
- **Sampling and emission.** The 2% policy may refuse an otherwise ordinary evolving economy; it no longer claims proof of convergence. The 0.05 cutoff and two-decimal emission intentionally discard small balances. Keep filtering/rounding consistent with the explicit algorithm at :163.
- **Manifest implementation.** The new content-verification contract fixes the prior defect. Treat “every file in tools/hsi/” (:165) as an explicit inventory of generator source/configuration files, excluding generated bytecode/caches; :216 already calls them generator sources. Bind the probe sources used for a measurement in its provenance if source-level reproducibility is wanted. These are implementation details, not evidence that an existing manifest has failed.

The recurrence itself is now correct for the declared model: apply bounded decay before each finished delta, clamp the country afterward, and decay to the horizon. Accrual precedes same-day subtractions; positive accruals commute with each other, and reductions/refunds are nonpositive, so the goal-id tie break does not reintroduce CSV-order dependence. The exact January 1 inclusion rule still needs P4's correction.

The monthly DIAG method is supported by the scripts. on_monthly_pulse_country has country ROOT (common/on_actions/00_code_on_actions.txt:474–475). From that chain, enter the actual state scope and evaluate:

    set_variable = {
        name = hsi_probe_siv
        value = state_infamy_value
    }

Script values are valid numeric inputs and use available scopes (common/script_values/script_values.md:1–18); vanilla explicitly uses state-scope variables (common/scripted_effects/00_spanish_flu_effects.txt:1–7). The actual formula uses root for aggressor predicates and saves temporary state/region scopes (00_infamy_values.txt:114–198). Its unification helper is an ordinary country-scoped scripted trigger (common/scripted_triggers/00_diplomacy_triggers.txt:219–227), not an effect requiring a diplomatic play. DIAG's booleans can be materialized with if/else using those same triggers, and the numeric SIV logged immediately from its state variable. Preserve the country ROOT while changing current scope; log/assert its actual identity rather than printing an expected tag as if it proved ROOT. This is a supported composition, not a boot-tested probe.

I found no proven load/fire defect in §8's additive rootless dispatch, global guard, Standard fallback or scalar country-scope changes. Vanilla demonstrates additive registration (_on_actions.md:115–128), rootless rule checks/global writes (00_code_on_actions.txt:10–19,89–92), scalar change_infamy (bol - bolivia.txt:39), and the absence of a Standard flag (00_game_rules.txt:97–117). The storage precision and country-record parsing still need the retained real save specified by acceptance; neither is established by this review.

## 4. Verdict

**REVISE** — the replay architecture is now sound, but absent-actor modifier inputs, the tick-0 fixture data path, precision-aware ordering validation and the horizon boundary need concrete definitions before the claimed verification can be trusted.

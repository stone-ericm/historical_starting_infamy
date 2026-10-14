# Historical Starting Infamy — spec v4 addendum (2026-10-14): the simplified calibration

**Status:** owner ruling, Eric, 2026-10-14 (verbatim): "this sounds overcomplicated. let's just pick some defensible
infamy numbers based on roughly what vic3's current infamy formulas would have assigned to the acts at the given times
and given the conditions at the time of the act." This addendum supersedes the parts of spec v3.1 it names; everything
else in v3.1 stands (the ledger, its refusals, the timeline, delivery, Bolivia, the non-goals).

## What the two boots established (research/measurement/2026-10-14-run-*/)

- The state formula replica (`tools/hsi/formula.py`, `00_infamy_values.txt`) reproduces the engine: 1,754 diagnostic
  records across three monthly samples under fourteen different holders, all within 0.005 (oracle A, boot 2; the
  addendum's Mascara subtotal 17.735 is a transcription figure, the exact one from the stated operands is 17.753).
- A stage the spec lacked: **country ranks scale infamy on both sides** (`common/country_ranks/00_country_ranks.txt`,
  `infamy_aggressor_scaling` / `infamy_target_scaling`): great power +0.20 / +0.20, major +0.10 / +0.10, minor 0 / 0,
  insignificant −0.10 / −0.10, unrecognized major +0.50 / −0.30, unrecognized regional +0.40 / −0.40, unrecognized
  power +0.30 / −0.50, decentralized 0 / 0. Seen in every tooltip ("+20 % from France being a Great Power",
  "−40 % from Mascara being a Unrecognized Regional Power").
- The stage order, from the eleven captures: state values → × severity → clamp → × (1 + general modifier) →
  × (1 + aggressor scaling + target scaling) → × rule. The general modifier and the rank block are separate
  multiplications (Mascara: 17.735 × 0.95 × 0.80 × 0.5 = 6.74, shown 6.7; one additive block would show 6.6). The
  floor of 1 is placed last by the define's own comment; no capture exercised it. H1's registry is retired.
- The UI truncates to one decimal. Script-value arithmetic is fixed point at five decimals, so uncapped shares arrive
  quantized to 0.1.
- GDP shares move 5 to 40 percent between the first monthly samples (markets settling) and a ledger slice (Ladakh's
  part of Kashmir) ceased to exist in late March 1836; the 2 % stabilization rule can never pass early and is retired.
- `has_game_rule` is readable in `on_game_started`; each country's monthly pulse fires on its own day of the month;
  `debug.log` rotates every 512 KB; inside `debug_log` only `[GetGlobalVariable('x').GetValue|n]` prints values.

## The calibration (replaces v3.1 §3 H1, §6 "Oracle fixtures" and "Snapshot selection", §7 "Measurement manifest",
## §9 steps 1–2 and the tolerance rule)

1. **Snapshot.** The after-lobby day-one sample (`start_b`) supplies every reconstruction input: slice population and
   GDP shares (uncapped, as the engine computes them), global denominators, each country's general and unrecognized
   modifiers, and each country's rank. It is the state the game is in when the mod's own hook fires. The monthly
   samples are the formula check only (oracle A must reproduce every diagnostic record present) and a documented
   drift observation; a monthly sample that is short because a slice ceased to exist is still used for the records it
   has.
2. **Per goal.** raw = Σ component state values (v3.1 §7, unchanged); × severity; clamp where the goal defines one;
   × (1 + general modifier); × (1 + aggressor scaling of the holder's rank + target scaling of the target's rank);
   × rule multiplier; floor 1. Ranks: the measured 1836 rank of `holder_tag_1836` and of `victim_tag_1836` (the play's
   target); an actor without a 1836 tag uses a declared fallback by type (recognized → minor power, unrecognized →
   unrecognized power, decentralized → decentralized power), recorded in the derivation.
3. **Timeline and emission.** As v3.1 §7, except the output: a country is emitted when its finished balance is at
   least 0.5, as a whole number (half up). The README says these are defensible estimates, not a simulation.
4. **Binding.** The generated effect's header hashes the ledger, the generator sources, the vanilla inputs (now
   including the rank file) and the engine logs it read; no manifest, no immutability rule beyond "regenerate from a
   named boot directory". Fixtures stay as evidence (`research/measurement/2026-10-14-run-20261014-142803-66370/`,
   the captures) and as tests (`tools/tests/test_formula_goal.py`), not as a gate.
5. **Acceptance.** v3.1 §9 steps 3–7 stand, with the whole-number tables; the tolerance question is moot.

## Approximations added to v3.1 §10

- Day-one 1836 shares, modifiers and ranks stand in for the conditions at the time of each act; the rank at the time
  of the act is the single largest known gap (Egypt in 1831 was stronger than its 1836 rank reads) and is left to a
  later ledger override column if wanted.
- Shares are the engine's quantized values; a merged multi-slice component sums quantized slice shares.

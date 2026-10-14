# Attempt 1 (run 20261014-142803-66370), 2026-10-14 14:28–14:58 EDT — probe v0.0.1, FAILED measurement, VALID captures

**Outcome.** The probe loaded and every hook fired, but every STATE, COUNTRY and DIAG number logged 0 (1,344
`NULL_STATE` script errors): the `[SCOPE.sState('…').MakeScope…]` and `[SCOPE.sCountry('…')…]` data functions inside
`debug_log` resolved to nothing, and the `$HOOK$` parameter inside the quoted string came out as `HSIstart_a$;`.
The `[GetGlobalVariable('…').GetValue|n]` path printed real values (GLOBAL records). Probe v0.0.2 routes every value
through global variables and uses literal hook names. This directory is kept as the record of the attempt; no
manifest is written for it and the generator must never be pointed at it.

**Engine observations (new, from this boot and Eric's tooltips).**
- `on_game_started`: `has_game_rule` IS readable (start_a logged `flag=very_low`). Between the two start hooks
  global GDP moved from 358,969,839.10 to 359,401,559.50 (population unchanged at 1,022,466,736).
- `on_monthly_pulse_country` fires on a country-specific day of the month: NET 2nd, PAN 5th, PER 7th, BOL 10/11th,
  MAD 13/14th, EGY and SIA 15/16th, BIC 22/23rd, DAI and SPA 23/24th, FRA 26/27th, HAI and RUS 27/28th, GBR 30th
  (January 30, February 29, March 31). Three firings per country before April 1.
- `debug.log` rotates every 512 KB: this session spans debug.3.log (launch), debug.2.log (start hooks, January),
  debug.1.log (February, March) and debug.log (March 31). error.log rotated five times from the probe's own errors.
- Country ranks scale infamy on both sides (`common/country_ranks/00_country_ranks.txt`: `infamy_aggressor_scaling`,
  `infamy_target_scaling`): great power +0.20/+0.20, major +0.10/+0.10, minor 0/0, insignificant −0.10/−0.10,
  unrecognized major +0.50/−0.30, unrecognized regional +0.40/−0.40, unrecognized power +0.30/−0.50. The tooltips
  show "+20% from France being a Great Power", "−40% from Mascara being a Unrecognized Regional Power",
  "−10% from Lucca being a Insignificant Power". The spec's formula (00_infamy_values.txt only) lacked this stage.
- Order and arithmetic consistent with every capture: state values summed → × severity → clamp → × (1 + general
  modifier −0.05) → × (1 + aggressor rank scaling + target rank scaling) → × rule 0.5. The general modifier and the
  rank factor are separate multiplications (Mascara 17.735 × 0.95 × 0.80 × 0.5 = 6.74 → shown 6.7; the additive
  alternative 0.75 gives 6.65 → would show 6.6).
- The UI TRUNCATES to one decimal (Oran state 17.46 → "17.4"; Lucca 1.5675 → "1.5"; Austria 6.65 → "6.6").
- France's interest in North Africa reads "Engaged" (tier 2, +10 %) although France owns three states there.

**Captures (tick 0, France, Very Low), all in this directory as .heic originals and .jpg copies.**
| file | what | key lines |
|---|---|---|
| context-tick0-paused | map, January 1 1836, paused, the error popup | context |
| fixture-A-mascara-protectorate | Make Protectorate, Mascara | +35.5 from Mascaran States (18.0 Algiers + 17.4 Oran); ×0.50 severity; −5 %; +20 % France GP; −40 % Mascara unrec. regional; −50 % rule; total 6.7 |
| fixture-A-state1-algiers | nested Algiers | +5.0 base; +4.6 pop 1.27M (0.12 %); +3.9 GDP 380K (0.10 %); +6.7 Incorporated Homeland; −2.0 Borders France by land; +1.8 Engaged interest; −2.0 against unrecognized; = 18.0 |
| fixture-A-state2-oran | nested Oran | +5.0; +2.6 pop 735K (0.07 %); +2.2 GDP 219K (0.06 %); +9.8 Incorporated Capital; −1.9 borders; +1.7 Engaged; −1.9 unrec; = 17.4 |
| fixture-B-state-algiers-map-tooltip | "State Infamy" map tooltip, Algiers | the Algiers chain above, then −5 %, +20 %, −40 %, −50 %; "6.8 for France to take Algiers" |
| fixture-B-state-oran-map-tooltip | same, Oran | 6.6 |
| fixture-Cmin-lucca-regime-change | Regime Change, Lucca | +11.6 Luccan States; ×0.10; Minimum of 3; −5 %; +20 %; −10 % Lucca insignificant; −50 %; total 1.5 |
| fixture-Cmin-parma-regime-change | Regime Change, Parma (+ nested Parma: 5.0 + 1.7 + 1.3 + 8.0 capital = 16.0) | 16.0; ×0.10; Minimum of 3; …; total 1.5 |
| fixture-Cmin-modena-regime-change | Regime Change, Modena (nested 5.0 + 2.3 + 2.1 + 9.4 = 18.8) | 18.8; ×0.10; Minimum of 3; …; total 1.5 |
| fixture-Cmax-austria-regime-change | Regime Change, Austria | +345.2 Austrian States (15 entries, top 54.5 Österreich); ×0.10; Maximum of 10; −5 %; +20 % France GP; +20 % Austria GP; −50 %; total 6.6 |
| fixture-Cmax-prussia-regime-change | Regime Change, Prussia | +364.6 Prussian States (13 entries); ×0.10; Maximum of 10; −5 %; +20 %; +20 %; −50 %; total 6.6 |

B's draft-panel capture (Conquer State) was not taken; the two map tooltips show the complete per-state chain
including the factor line and the goal-level modifiers, which is what B was for. D (floor) was not offered/attempted.

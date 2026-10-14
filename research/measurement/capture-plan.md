# Oracle tooltip capture plan (Task 10, step 4 of PROCEDURE.md)

Machine-readable source: `capture-plan.json`, audited statically by `python3 research/scripts/capture_audit.py "$GAME"`.
The audit verifies only what the files fix (relations blocker incl. overlord, subject status, decentralized targets,
history truces, holder claims, release existence, ownership in the target's region as the interest proxy) and prints,
per candidate, the conditions that stay **unverified until the keyboard**: the interest tier at tick 0 (every play
carries `requires_interest_marker` by default), regime change's ideological-opinion and installable-interest-group
conditions, liberation's active secession movement, protectorate subject-rank rules. Its value estimates use
population only (GDP share = population share), interest tier 3 and France's −0.1 modifier against unrecognized
countries (Colonization); they are planning numbers, never transcription values. The audit also writes every
candidate's state slices into `research/probe/config.json`, so the probe logs tick-0 and monthly records for all of them
(Russia was dropped as a fallback because its 73 slices would not be logged in full). Review R1 (2026-10-14) found the earlier plan's B and D
targets could not be drafted at all (France sits at relations 30 with Sardinia-Piedmont and 20 with Austria, at or above
the cordial threshold that Conquer State and Liberate Country require to be strictly below; "Sicily" is Two Sicilies'
own tag, not a release), and that Tuscany would not have shown the regime-change minimum (its capital standing doubles
the state value). Every candidate below passed the audit on 2026-10-14.

Fixture holder: **France** (Empiricism gives the nonzero general generation modifier the ordering gate needs). Rule in
the lobby: **Very Low**. All captures happen on 1836.1.1 before the first unpause, as draft diplomatic plays that are
then cancelled. Nothing is typed in-game: the screenshots are the record.

## What to capture for each play

1. Diplomacy panel → the target country → **Start Diplomatic Play** → choose the war goal (for B pick the state named
   below). The draft shows the infamy the play would generate.
2. Hover that infamy value and screenshot the **full breakdown** (⇧⌘4, saved to the Desktop). Every line matters: the
   per-state entries ("x from State"), the severity line ("×0.50 from war goal severity"), any "Minimum of…" or
   "Maximum of…" line, the general modifier line, the game-rule line, and the total.
3. For A, B and D, open the **"… from N states"** list and screenshot **every constituent state's** nested tooltip
   (base value, population and GDP shares, standing, and the factor lines such as "Borders France by land", homeland,
   interest level). Mascara has two states, Morocco four: each one, not just the first. For Cmin also screenshot the
   state tooltip. These give the operands at more precision than the one-decimal state entries (review R1 finding B5).
4. Context, once per capture: the draft panel itself showing France, the target and the chosen war goal (the breakdown
   screenshot usually includes it; if not, take one more), and once per boot a screenshot of the top bar at 1836.1.1
   paused and of the lobby page with Infamy Generation = Very Low.
5. **Boundary rule:** a candidate counts only when its breakdown shows the line the table asks for. If the first
   candidate is draftable but does not show it (no "Minimum of 3" for Cmin, no "Borders France by land" for B), keep
   that screenshot and try the next candidate anyway; population order does not settle GDP, so a larger country can
   still clamp when a smaller one does not. If the game refuses the play (greyed goal, missing target, a "requires…"
   note), screenshot the refusal and move on. Record which candidate you ended up capturing, in order.
6. Cancel the draft. Do not send any play.
7. **Inventory before observing** (review R3 P1). A, B, Cmin and Cmax are each required, with their full breakdown,
   every constituent state's tooltip and the context shot. If **any one** of them is missing or shows no candidate
   with its required line, stay paused and tell Claude: the order gate needs all four, and a tick-0 observation cannot
   be recovered after unpausing. Only D may be skipped.

## Captures, in order, with the decision rule

| id | war goal | candidates (first that shows the required observation) | what the breakdown must show | audit estimate (pop-only) |
|---|---|---|---|---|
| **A** | Make protectorate | 1. **Mascara (MAS)** · 2. Morocco (MOR) · 3. Constantine (CON) | the ×0.50 severity line, the modifier and rule lines; total well above 1 | MAS raw≈38 → Very Low ≈9 |
| **B** | Conquer state | 1. **Mascara, state Algiers** · 2. Belgium, state Flanders | a state entry with **"Borders France by land"** in its tooltip; no severity line | MAS/Algiers raw≈19 → ≈9 |
| **Cmin** | Regime change | 1. **Lucca (LUC)** · 2. Parma (PAR) · 3. Modena (MOD) | **"Minimum of 3"** line; try the next candidate if it is missing (boundary rule) | LUC raw≈12 → ×0.1 ≈1.2 → clamped to 3 → Very Low ≈1.4 |
| **Cmax** | Regime change | 1. **Austria (AUS)** · 2. Prussia (PRU) | **"Maximum of 10"** line | AUS raw≈285 → ≈28 → clamped to 10 → ≈4.75 |
| **D** (optional) | Liberate country | 1. **Great Britain, release Wales** · 2. Russia, release Lithuania · 3. Prussia, release Poland | a total below 1 before the final floor, so either "1.0" or a value like "0.9" appears; capture whichever candidate the game offers, even outside the range | GBR/Wales raw≈18 → ×0.1 → Standard ≈1.7 → Very Low ≈0.86 → floor 1 |

D exists to tell floor-before-rule from floor-after-rule. Liberate Country also needs an active secession movement with
10 % support (`WAR_GOAL_LIBERATE_COUNTRY_MIN_POPULAR_SUPPORT`; history seeds Irish and Polish movements, no Welsh or
Lithuanian one), which cannot be checked from the files, and Conquer State
cannot reach the 1–2 range for France (per-state floor 1, no claims). So D is best-effort: if no candidate is offered,
skip it and say so. The ordering gate then decides from the measured ledger whether the floor's position changes any
charge; if it does and D is missing, generation refuses with the goals named, and a five-minute tooltip-only boot of the
probe supplies the capture later (its evidence is kept beside this boot's, never merged).

Regime change carries no relations blocker (`00_diplomatic_plays.txt` dp_regime_change), so Austria's 20 does not
block it; like every play it needs an interest in the target's region (play-level default). By ownership France has
involvement in Southern Europe (Corsica, with Lucca, Parma, Modena and Austria's Italian states) and in Western Europe
(Prussia's Rhineland and North Rhine lie there); Alsace is Western Europe too, so France owns nothing in Central Europe,
and the actual tick-0 tier is one of the runtime conditions only the draft panel settles. Regime change is also gated in code on the target ruler's ideological opinion of France and on an
installable interest group, which only the draft panel shows: that is why Cmin has three candidates. Make protectorate
carries no relations blocker but needs the interest and the subject-rank rules; France owns states in North Africa
(Algiers, Oran, Bône), so Mascara, Morocco and Constantine qualify by ownership.

What Claude transcribes afterwards per capture (into `oracle-tooltips.md`): capture id, holder, target, rule, then
every line of the breakdown in display order with its label and number exactly as shown, including each per-state line,
the severity line, any clamp line, the modifier and rule lines, and the total; plus the state-level tooltip lines.

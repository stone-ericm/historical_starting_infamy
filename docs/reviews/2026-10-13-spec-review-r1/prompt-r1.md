# Historical Starting Infamy — design spec review, round 1 (tag HSI-R1)

You are reviewing a DESIGN SPEC for a Victoria 3 (vanilla 1.14.5) mod before any code exists. Assume the spec contains defects: wrong engine facts, misread script semantics, arithmetic that does not match the game's formula, hooks that fire at the wrong time, verification that cannot fail. Find them and say precisely what is wrong. Do not evaluate whether the idea is worthwhile; evaluate whether the design will work as written and whether its verification would catch it if it did not.

## Hard rules
- Do NOT read `~/.codex/memories/` or any memory file, and do not rely on remembered context from other sessions. If a memory summary was injected into your context, disclose it in section 0 of the deliverable and do not use it.
- Read-only review. The only file you may create or modify is the deliverable named below. Do not edit the spec, the repo, or any game file.
- Do not run `herdr` commands, do not touch other terminal panes, do not start other agents, no network access, no git mutations.
- Allowed commands: cat, head, tail, sed -n, grep, rg, ls, find, wc, diff, shasum, python3 for read-only computation (no file writes except the deliverable), and git log/show/diff/status inside the mod repo.
- One command per tool call, from the first call onward.

## Inputs (frozen for this round)
- Spec: `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` (repo HEAD 202905f).
- Vanilla 1.14.5 scripts, read-only ground truth: `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`
  Relevant: `common/defines/00_defines.txt` (NDiplomacy infamy block, about lines 995–1175), `common/script_values/00_infamy_values.txt`, `common/script_values/00_diplomacy_values.txt` (interest tier values near line 1068), `common/war_goal_types/*.txt`, `common/on_actions/00_code_on_actions.txt` and the rest of `common/on_actions/`, `common/game_rules/00_game_rules.txt`, `common/history/countries/bol - bolivia.txt`, `common/ai_strategies/00_default_strategy.txt`, `common/scripted_effects/`, `events/` (usage patterns for `debug_log`, `change_infamy`, `has_game_rule`, global variables), `common/treaty_articles/` (`change_infamy = { ... }` block usage), `localization/english/` (any key explaining infamy severity).

## Questions to attack (answer each with evidence as file:line or quoted script)
1. Hook timing. The spec hooks `on_game_started_after_lobby` so that the game rule is final and the values exist on 1836.1.1 before the first unpause. Is that right? Does that hook fire once per campaign, on a new game only? Can a mod add to it through its own on_action file without overriding vanilla's effect block, and what is the vanilla pattern for that? Does anything in vanilla show game-rule-dependent logic in that hook?
2. `infamy_severity`. The spec infers it is a multiplier applied to the war goal's computed `infamy` value, then clamped by `infamy_min`/`infamy_max`. Find evidence for or against (loc keys, tooltips, docs, other uses). If it is unknowable from files, say so and propose the cheapest in-game test.
3. Formula replication. Compare spec §7 step by step with `00_infamy_values.txt`: order of operations, which factors are mutually exclusive (else_if chains), interest tier branches, the unrecognized-target multiplier conditions, the floor, the soft-cap arithmetic. Is anything the game applies missing from §7, or applied in §7 that the game does not apply?
4. Decay. The spec assumes linear 5.0 per year, no floor, and ignores decay modifiers. Is vanilla decay linear per day or per month? Is there anything in defines or script that would change base decay for the countries and years in question? Are the refund constants and the points at which they apply correct (back down −0.75, peace −0.5, target reduction −0.5)?
5. Script validity of the shipped effect (§8): is `change_infamy = { value = <n> multiply = global_var:hsi_rule_mult }` accepted by `change_infamy`, and is `global_var:` valid inside a script value in a country scope? Are `set_global_variable` / `has_global_variable` usable as an idempotence guard in an on_action effect that has no root scope? Are `has_game_rule` triggers valid with no root scope?
6. Probe design (§6): can numeric script values (`state_population`, `gdp`, `state_infamy_base`, a country modifier value) be printed through `debug_log` data functions, and what is the exact syntax? What is the correct weekly pulse on_action name and scope in 1.14.5? Any hazards with `debug_log` at game start?
7. Ledger schema (§5): which historical situations cannot be expressed (states that changed hands mid-window, goals against a subject's states where the overlord is the target, an aggressor that is a 1836 subject, partial-state conquests)? Which columns are missing to compute the formula exactly as the game does?
8. Verification (§9): can each check fail in the direction it is meant to catch? What false greens remain? Is reading `infamy=` from a plaintext tick-0 save reliable (format, rounding, where it lives)?
9. Anything else that would make the mod fail to load, fail to fire, or produce wrong numbers.

## Deliverable
Write `/Users/eric/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy/.codex-review/spec-review-r1/codex-findings-r1.md` with these sections:
0. Disclosure: any injected memory or context; the model and reasoning effort shown in your footer.
1. Findings, numbered, each with: severity (BLOCKER / MAJOR / MINOR), spec section, the claim, evidence (file:line or quoted script), proposed fix.
2. Answers to questions 1–9 not already covered by a finding.
3. What you would design differently, if anything, in at most 10 lines.
4. Verdict: APPROVE / REVISE / REJECT with a one-sentence reason.

When the file is complete, run `shasum -a 256` on it and print, as your final on-screen message, the line `HSI-R1-<first 8 hex of the digest>` on its own line, then exactly `DONE` on the next line. (Template: `HSI-R1-xxxxxxxx`.)

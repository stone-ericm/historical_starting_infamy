# Acceptance boot (run 20261107-123722-87747), 2026-11-07 ~12:37 EDT — v0.2.0 on 1.15.0, Standard rule, release folder enabled in place

**Observed.**
- `acceptance-egypt-11.png` (Eric's screenshot): Egypt's infamy tooltip reads **"Egyptian Infamy: Reputable (11.0)"**,
  decay −0.120/week (base −5/year, +25 % Egypt, +25 % Influence). The table gives 11. Exact.
- Punjab: reported by Eric as checked ("done" after the instruction to check Egypt 11 and Punjab 2); no screenshot.
- `error.log` of this boot against the 1.15 probe boot's (probe lines excluded, numbers normalized): **0 distinct new
  messages**; no line mentions HSI.
- One campaign; the playset was restored and verified byte for byte by the boot script (run receipt). The EoR driver
  held its boot queue for the duration.

**Not done** (as for v0.1.0, waived 2026-10-14 for v1): no save, so `hsi.savecheck`, every-other-country-at-0, Bolivia
50, the guard once, reload and late-enable did not run; Very Low not booted.

**Verdict.** Standard smoke check passed on 1.15: the mod loads, applies the Standard table at the start (Egypt exactly
11.0) and adds no new script error.

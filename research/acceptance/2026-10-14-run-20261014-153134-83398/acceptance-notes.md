# Acceptance boot (run 20261014-153134-83398), 2026-10-14 15:31–15:34 EDT — Standard rule, shipped mod enabled in place

**Observed (screenshots, .heic originals + .jpg copies).**
- `acceptance-egypt-notorious`: Egypt's Diplomacy tab on January 1, 1836, paused, shows Infamy **Notorious** (the 50–100
  band). Vanilla Egypt starts at 0 (Reputable). The table gives 54; the band is consistent with it. The numeric tooltip was
  not opened.
- `acceptance-punjab-11`: Khalsa Raj's infamy tooltip reads **"Sikh Infamy: Reputable (11.0)"**, decay −0.120/week
  (base −5/year, +25 % Khalsa Raj, +25 % Influence). The table gives 11. Exact.
- `error.log` + `error.1.log` of this boot, compared with boot 2's (probe lines excluded): **0 distinct new messages**.
  The in-game counter (1,510) is vanilla's own startup noise, present in every boot.
- The playset was restored and verified by the boot script (run receipt).

**Not done.** No save was made, so `hsi.savecheck` (structural read of the plaintext save: every other country at 0,
Bolivia 50, the `hsi_applied` guard once) and the lifecycle checks did not run. They can be run on any later Standard
boot that saves while paused as `hsi_accept_std_1836_01_01`.

**Verdict.** Standard smoke check passed: the mod loads, applies the Standard table at the start (Egypt in the
Notorious band, Punjab exactly 11.0) and adds no distinct script error against the probe boot's log. Not established
here: the exact 54, every other country at 0, Bolivia at 50, the guard once, a reload, enabling on an existing save,
the Very Low rule. (Reworded after the final review, F1.) Owner ruling 2026-10-14: the save-based checks are waived for v1; this smoke check is the acceptance record.

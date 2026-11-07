# 1.15 measurement boot, 2026-11-07 (run 20261107-121915-79721)

Game 1.15.0 (`engine.txt`). Probe regenerated for 1.15 (commit "Probe: regenerate for a 1.15 measurement boot"; one
fixture slice moved, STATE_KAUNAS -> STATE_LITHUANIA). Boot by Eric with `research/measurement/boot_probe.sh`, France,
`observe`, speed 5 past the third monthly pulse; the EoR driver held the Mac's boot queue for the duration.

**Two campaigns in one boot.** A Standard-rule game was started first (start hooks 12:21:17 / 12:21:36), then a
Very Low one, the procedure's (12:22:33 / 12:23:17). The receipt check on the raw logs refuses the duplicate
(`duplicate record ('start_a', 0, 'GLOBAL', '-')`). `research/scripts/split_sessions.py` cuts the concatenated raw
logs at each start_a into `session-1/` and `session-2/` (cut lines and raw-log hashes in each `SESSION.md`); the raw
logs here are unchanged. **`session-2/` is the measurement.** `session-1/` reached no monthly sample.

**Pre-quit checkpoint.** The live `debug.log` ended mid-line at exactly 256 KiB, inside the Netherlands' third
monthly sample; the final logs after quitting carry the rest (8 more probe lines). On the final logs, session-2's
receipt is INCOMPLETE only for STATE_KASHMIR/LAD in sample 3: Ladakh is present in samples 1 and 2 (state and country
records) and gone in sample 3, i.e. it ceased to exist during March 1836, the case the v4 addendum allows.

**Oracle A on 1.15.** 1,752 DIAG records over three monthly samples, 0 mismatches with the 1.15 formula variant.
With the 1.14.5 variant the generator refuses (e.g. BIC/STATE_ADANA/EGY: 10.2375 generated vs 4.6125 engine), so the
1.15 state base (each share floored at 1, no flat 5) is engine-measured, not only read from the files.

**Day-one noise.** The two campaigns' after-lobby samples differ slightly (world GDP 363,263,028.21 vs
363,616,532.42, +0.10 %); population is identical. Priced from either start the five tables are identical; Egypt's
Standard balance is 10.933 (session 1) vs 11.069 (session 2), both 11.

**Result (session-2):** Very Low none; Low EGY 3; Standard EGY 11, PAN 2; High 19 / 4; Very High 27 / 7. The v0.2.0
draft priced from the 1.14.5 boot's inputs had 4 / 12 / 20 / 28 for Egypt: one lower at every rule now.

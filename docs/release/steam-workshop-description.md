# Steam Workshop listing (paste into the launcher's Upload mod dialog)

**Title:** Historical Starting Infamy

**Tags:** Historical, Balance

**Description:**

In vanilla every country starts 1836 with 0 infamy, except Bolivia, which gets 50 for taking Peru. This mod gives the rest of the world the infamy the game's own rules would have charged for what each country did between 1816 and 1835, decayed at the normal 5 per year down to 1 January 1836.

The result is that the world forgets fast. Almost everything before 1830 has decayed to nothing by 1836. What survives:

- Egypt: 54. The 1831 invasion of Syria (Adana, Aleppo, Syria, Lebanon, Palestine, priced as an unrecognized regional power attacking a great power).
- Punjab (Khalsa Raj): 11. Peshawar and Ladakh, 1834.

Under the Infamy Generation game rule: Very Low 16 / 1, Low 35 / 6, Standard 54 / 11, High 72 / 16, Very High 91 / 21 (France also gets 1 at Very High). Bolivia keeps its vanilla 50.

How the numbers were made. Twenty acts (Greek and Belgian independence and their backers, the French in Algiers, the Russo-Persian and Russo-Turkish wars, the First Anglo-Burmese War, Siam and Vietnam in Cambodia, Persia at Herat, Haiti in Santo Domingo, Egypt in Sudan and Syria, the Sikhs at Peshawar and Ladakh, and others) were each mapped to the war goal they correspond to and priced with the 1.14.5 infamy formula, using the game's own day-one 1836 population and GDP shares, modifiers and country ranks. The formula was checked against the engine with a probe mod that logged 1,754 state values under fourteen countries; the replica reproduces all of them. Each charge is dated at the start of its war, refunded or reduced the way the game does it, decayed, and rounded to a whole number. Acts the rules cannot express (partial cessions, humiliations, colonization) are left out and listed.

What it does technically: two script files, nothing overwritten. It registers on on_game_started_after_lobby, applies the table once per new campaign, guarded by a global variable, and respects the Infamy Generation rule (Standard when none is set). It does nothing on an existing save.

Victoria 3 1.14.5, vanilla. Should coexist with any mod that does not itself change starting infamy. Not tested in multiplayer.

Source, ledger and measurement logs: https://github.com/stone-ericm/historical_starting_infamy

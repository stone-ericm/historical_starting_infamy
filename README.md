# Historical Starting Infamy

A Victoria 3 (1.14.5) mod, on the Steam Workshop as [item 3819895927](https://steamcommunity.com/sharedfiles/filedetails/?id=3819895927). It assigns estimated starting infamy from a ledger of selected 1816–1835 acts (twenty acts, thirty-seven war goals; the excluded and unrepresentable acts are listed in `research/`), priced with the game's own 1.14.5 formula and replayed as one decaying balance per country, read off on 1 January 1836. Countries with no surviving ledger balance stay at zero. Vanilla gives Bolivia 50 for the conquest of Peru; that stays as it is.

## Starting infamy by game rule

<!-- hsi:table:start -->
| Country | Very Low | Low | Standard | High | Very High |
|---|---:|---:|---:|---:|---:|
| EGY | 16 | 35 | 54 | 72 | 91 |
| FRA | 0 | 0 | 0 | 0 | 1 |
| PAN | 1 | 6 | 11 | 16 | 21 |
<!-- hsi:table:end -->

The values are applied by the after-lobby new-campaign hook, guarded by a global flag so a reload cannot apply them twice, and scaled by the Infamy Generation game rule. Measured so far: a Standard-rule start shows Egypt in the Notorious band and Punjab at 11.0, with no new script errors. Not measured for this release (waived by the author): the Very Low start, a reload of a saved game, and enabling the mod on an existing save, which the guard is designed to leave unchanged.

## How the numbers were derived

Each act is mapped by a documented judgment to the vanilla war goal it corresponds to and priced with the 1.14.5 formula. The state formula was checked against the engine: a probe mod logged the engine's own state values under fourteen holders for three months, and the replica reproduces all 1,754 diagnostic records within 0.005. Eleven tooltip captures support the severity, clamp and rank stages and their order; the final floor of 1 is taken from the define and was not captured. Each charge is dated at the start of the war or crisis in which the demand was made, with one modelled resolution (refund fractions from the vanilla defines; the victim's reduction uses the creator's charge, an assumption), and decays at 5 per year to 1836. Results are whole numbers; balances below one half are dropped. The ledger, its sources, the measurement logs, the component and stage derivation and the timeline replay are in `research/`.

This is a defensible estimate, not a simulation. In particular: the game's own day-one 1836 population and GDP shares, modifiers and country ranks stand in for their historical values at the time of each act (a surviving target the probe did not log, Ladakh, uses a declared fallback rank, stated in the derivation); split regions are priced as one state made of whole 1836 slices; the aggressor is always the goal's creator; standing, claims, adjacency and interest are documented historical judgments; decay runs at the base rate without modifiers; each goal has one claim and one resolution, without the primary-demand surcharge; same-day events follow a fixed order; the victim's reduction uses the creator's charge; actors that no longer exist in 1836 use declared fallback modifiers and ranks; the 1824 Assam component also covers Cachar, annexed separately in 1832. Acts the rules cannot express are listed in `research/not_representable.md`.

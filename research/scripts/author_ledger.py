"""Writes research/acts.csv, goals.csv, goal_states.csv from the judgment tables below (spec §5).
Language sharing and aggressor-homeland flags are computed from vanilla culture language fields and state homelands;
everything else is a recorded historical judgment. Re-run after editing the tables; never edit the CSVs by hand.
Usage: python3 research/scripts/author_ledger.py <game_dir>"""
import csv, re, sys
from pathlib import Path
V = Path(sys.argv[1]); OUT = Path(__file__).resolve().parents[1]

def blocks(text, pat):
    for m in re.finditer(pat, text):
        i = m.end(); d = 1; j = i
        while d and j < len(text):
            d += (text[j] == "{") - (text[j] == "}"); j += 1
        yield m.group(1), text[i:j - 1]
cult_txt = "".join(p.read_text(encoding="utf-8-sig") for p in (V / "common/cultures").glob("*.txt"))
TRAITS = {}
for name, blk in blocks(cult_txt, r"(?m)^\s*([a-z_]+)\s*=\s*\{"):
    m = re.search(r"\blanguage\s*=\s*(language_[a-z_]+)", blk)   # cultures carry one `language = language_x` field
    if m: TRAITS[name] = {m.group(1)}
states_txt = (V / "common/history/states/00_states.txt").read_text(encoding="utf-8-sig")
HOMELANDS = {n: re.findall(r"add_homeland\s*=\s*cu:([a-z_]+)", b) for n, b in blocks(states_txt, r"s:(STATE_[A-Z0-9_]+)\s*=\s*\{")}
cdef_txt = "".join(p.read_text(encoding="utf-8-sig") for p in (V / "common/country_definitions").glob("*.txt"))
CULTURES = {}
for tag, blk in blocks(cdef_txt, r"(?m)^([A-Z][A-Z0-9]{2})\s*=\s*\{"):
    m = re.search(r"cultures\s*=\s*\{([^}]*)\}", blk); CULTURES[tag] = m.group(1).split() if m else []
def holder_langs(tag): return set().union(*(TRAITS.get(c, set()) for c in CULTURES[tag]))
def flags(holder, state):
    homes = HOMELANDS[state]; hl = holder_langs(holder)
    ah = any(c in CULTURES[holder] for c in homes)
    sl = (not ah) and any(TRAITS.get(c, set()) & hl for c in homes)
    return int(ah), int(sl)

# ---------------- acts: (act_id, title, start, end, source, notes)
ACTS = [
 ("egy_syria_1831", "Egyptian conquest of Ottoman Syria", "1831-11-01", "1833-05-14", "kutahya", "Ibrahim Pasha's army entered Palestine in late October 1831 and besieged Acre from November; the Convention of Kutahya (May 1833) left Syria, Palestine and Adana to Egypt."),
 ("egy_sudan_1820", "Egyptian conquest of the Sudan", "1820-10-01", "1821-08-31", "turco_egyptian_sudan", "Ismail Pasha's expedition left in October 1820; Dongola submitted by November 1820, Sennar fell in June 1821, Kordofan after the battle of Bara in August 1821."),
 ("bol_peru_1835", "Bolivian intervention in Peru", "1835-06-15", "1836-10-28", "peru_bolivian_confederation", "Santa Cruz entered Peru in June 1835; the Confederation was proclaimed on 28 October 1836. Computed, never emitted: vanilla sets Bolivia to 50."),
 ("rus_persia_1826", "Russo-Persian War", "1826-07-28", "1828-02-22", "turkmenchay", "Persia attacked in July 1826; Russia added the territorial demands and took the Erivan and Nakhchivan khanates at Turkmenchay."),
 ("rus_ottoman_1828", "Russo-Turkish War", "1828-04-26", "1829-09-14", "adrianople", "Russia declared war in April 1828; Adrianople gave Russia the Danube delta. The protectorate over Moldavia and Wallachia is not a Vic3 subject transfer (they remain Ottoman subjects in 1836) and is not modelled."),
 ("bic_burma_1824", "First Anglo-Burmese War", "1824-03-05", "1826-02-24", "yandabo", "Fought by the East India Company (BIC); Yandabo ceded Arakan, Tenasserim and Burmese Assam."),
 ("greece_backers_1827", "Great-power backing of Greek independence", "1827-07-06", "1830-02-03", "greek_independence", "Treaty of London (6 July 1827) to the London Protocol (3 February 1830); one liberate_country goal per backer."),
 ("fra_algiers_1830", "French conquest of the Regency of Algiers", "1830-06-14", "1832-03-27", "algiers_1830", "Landing at Sidi Ferruch 14 June 1830; Algiers 5 July 1830, Oran 4 January 1831, Bone 27 March 1832. The Regency has no 1836 tag."),
 ("belgium_backers_1830", "Great-power backing of Belgian independence", "1830-12-20", "", "belgian_revolution", "London Protocol of 20 December 1830 recognised Belgian independence; the Netherlands accepted only in 1839, so the goal is pending on 1836-01-01."),
 ("net_belgium_1831", "Ten Days' Campaign", "1831-08-02", "1831-08-12", "ten_days_campaign", "Dutch attempt to retake Belgium, abandoned under French intervention."),
 ("pan_peshawar_1834", "Sikh annexation of Peshawar", "1834-05-01", "1834-05-06", "peshawar_1834", "Hari Singh Nalwa took Peshawar from the Barakzai sardars; formal annexation 6 May 1834."),
 ("pan_ladakh_1834", "Dogra invasion of Ladakh", "1834-08-01", "", "ladakh_1834", "Zorawar Singh's campaign (August 1834 to October 1835) under Ranjit Singh's vassal Gulab Singh; Ladakh is still independent in vanilla 1836, so the goal is pending."),
 ("dai_cambodia_1833", "Vietnamese takeover of Cambodia", "1833-11-23", "1834-12-31", "tay_thanh", "Siamese invasion repelled by April 1834; Minh Mang placed Cambodia under direct rule as Tay Thanh in late 1834. Cambodia is a Vietnamese vassal in vanilla 1836."),
 ("sia_cambodia_1833", "Siamese invasion of Cambodia", "1833-11-23", "1834-04-30", "siam_vietnam_1833", "Bodindecha's invasion failed; Siamese forces withdrew by April 1834."),
 ("sia_vientiane_1827", "Siamese destruction of Vientiane", "1827-01-15", "1828-10-31", "lao_rebellion", "Anouvong's advance in January 1827; Vientiane taken in 1827 and razed in 1828; the kingdom was annexed."),
 ("sia_kedah_1821", "Siamese invasion of Kedah", "1821-11-12", "1821-11-18", "kedah_1821", "The governor of Ligor invaded on 12 November 1821 and took Kedah fort on the 18th."),
 ("hai_santo_domingo_1822", "Haitian occupation of Santo Domingo", "1822-01-15", "1822-02-09", "hispaniola_1822", "Boyer's army entered Santo Domingo on 9 February 1822."),
 ("spa_mexico_1829", "Barradas expedition", "1829-07-27", "1829-09-11", "barradas", "Spanish landing at Tampico 27 July 1829; capitulation 11 September 1829."),
 ("per_herat_1833", "Persian siege of Herat", "1833-07-01", "1833-11-30", "herat_1833", "Abbas Mirza's campaign from summer 1833; the siege was lifted in November 1833 after his death with only nominal suzerainty acknowledged."),
 ("mad_radama_1817", "Merina conquests under Radama I", "1817-06-01", "1824-12-31", "radama_i", "East coast submitted in 1817; the west was reduced by 1824."),
]
# ---------------- goals: (goal_id, act, wargoal, holder, tag, htype, target, stakeholder, victim_tag, claim, resolution, res_date, loyal, rebel, notes)
G = []
def goal(gid, act, wg, holder, htype, target, victim, claim, res, resd, notes, stakeholder=""):
    G.append((gid, act, wg, holder, holder, htype, target, stakeholder, victim, claim, res, resd, "0", "0", "measured_1836", notes))
for sk in ("ALEPPO", "SYRIA", "LEBANON", "PALESTINE", "ADANA"):
    goal(f"egy_{sk.lower()}", "egy_syria_1831", "conquer_state", "EGY", "unrecognized", "Ottoman Empire", "TUR", "1831-11-01", "enforced", "1833-05-14", "Egypt was an Ottoman subject attacking its overlord; the overlord-side subject discounts do not apply to the subject's goals.")
goal("egy_dongola", "egy_sudan_1820", "conquer_state", "EGY", "unrecognized", "Shaiqiya and Mamluk Dongola", "", "1820-10-01", "enforced", "1820-11-30", "Decentralized owner; no 1836 tag.")
goal("egy_sennar", "egy_sudan_1820", "conquer_state", "EGY", "unrecognized", "Funj Sultanate of Sennar", "", "1820-10-01", "enforced", "1821-06-13", "Sennar was the Funj capital; no 1836 tag.")
goal("egy_kordofan", "egy_sudan_1820", "conquer_state", "EGY", "unrecognized", "Kordofan (Darfur dependency)", "", "1820-10-01", "enforced", "1821-08-31", "No 1836 tag.")
goal("bol_north_peru", "bol_peru_1835", "make_protectorate", "BOL", "recognized", "Peru (northern states)", "NPU", "1835-06-15", "enforced", "1836-10-28", "Enforcement after the horizon: no reduction on the victim before 1836. Never emitted (vanilla 50).")
goal("bol_south_peru", "bol_peru_1835", "make_protectorate", "BOL", "recognized", "Peru (southern states)", "SPU", "1835-06-15", "enforced", "1836-10-28", "As above.")
for sk in ("ARMENIA", "AZERBAIJAN"):
    goal(f"rus_{sk.lower()}", "rus_persia_1826", "conquer_state", "RUS", "recognized", "Qajar Persia", "PER", "1826-07-28", "enforced", "1828-02-22", "Russia was the defender who added the territorial goals; Persia is unrecognized, so Russia's measured discount applies.")
goal("rus_dobrudja", "rus_ottoman_1828", "conquer_state", "RUS", "recognized", "Ottoman Empire", "TUR", "1828-04-26", "enforced", "1829-09-14", "The Russian slice of Dobrudja is the Danube delta.")
for sk in ("ARAKAN", "TENASSERIM", "ASSAM"):
    goal(f"bic_{sk.lower()}", "bic_burma_1824", "conquer_state", "BIC", "recognized", "Kingdom of Burma", "BUR", "1824-03-05", "enforced", "1826-02-24", "BIC is a chartered company in vanilla; the formula's unrecognized gate treats any non-unrecognized, non-decentralized root as recognized.")
for h in ("GBR", "FRA", "RUS"):
    goal(f"{h.lower()}_greece", "greece_backers_1827", "liberate_country", h, "recognized", "Ottoman Empire", "TUR", "1827-07-06", "enforced", "1830-02-03", "Backer goal at 10% of the released states (GRE's 1836 states).")
goal("fra_algiers", "fra_algiers_1830", "conquer_state", "FRA", "recognized", "Regency of Algiers", "", "1830-06-14", "enforced", "1830-07-05", "Algiers was the Regency's capital.")
goal("fra_oran", "fra_algiers_1830", "conquer_state", "FRA", "recognized", "Regency of Algiers", "", "1830-06-14", "enforced", "1831-01-04", "")
goal("fra_constantine", "fra_algiers_1830", "conquer_state", "FRA", "recognized", "Regency of Algiers", "", "1830-06-14", "enforced", "1832-03-27", "The French slice of Constantine is Bone.")
for h in ("FRA", "GBR"):
    goal(f"{h.lower()}_belgium", "belgium_backers_1830", "liberate_country", h, "recognized", "Netherlands", "NET", "1830-12-20", "pending", "", "Pending on 1836-01-01 (Dutch acceptance 1839).")
for sk in ("FLANDERS", "WALLONIA", "GELRE"):
    goal(f"net_{sk.lower()}", "net_belgium_1831", "return_state", "NET", "recognized", "Belgium", "BEL", "1831-08-02", "dropped_backdown", "1831-08-12", "Dutch claims on the seceded provinces; dropped under French intervention.")
goal("pan_peshawar", "pan_peshawar_1834", "conquer_state", "PAN", "unrecognized", "Barakzai sardars of Peshawar", "KAB", "1834-05-01", "enforced", "1834-05-06", "Peshawar lies in the PAN slice of STATE_PASHTUNISTAN.")
goal("pan_ladakh", "pan_ladakh_1834", "make_tributary", "PAN", "unrecognized", "Ladakh", "LAD", "1834-08-01", "pending", "", "Gulab Singh acted as Ranjit Singh's vassal: holder = creator = PAN by the v1 restriction. Pending: LAD is independent in vanilla 1836.")
goal("dai_cambodia", "dai_cambodia_1833", "make_protectorate", "DAI", "unrecognized", "Cambodia", "CAM", "1833-11-23", "enforced", "1834-12-31", "Vietnam defended against Siam and then imposed direct rule; vanilla has CAM as a DAI vassal. Cambodia's earlier dual tributary status is not treated as a loyal-subject discount.")
goal("sia_cambodia", "sia_cambodia_1833", "make_protectorate", "SIA", "unrecognized", "Cambodia", "CAM", "1833-11-23", "dropped_peace", "1834-04-30", "Failed; half refunded on withdrawal.")
goal("sia_vientiane", "sia_vientiane_1827", "conquer_state", "SIA", "unrecognized", "Kingdom of Vientiane", "", "1827-01-15", "enforced", "1828-10-31", "The SIA slice of STATE_LAOS; Vientiane was the kingdom's capital.")
goal("sia_kedah", "sia_kedah_1821", "conquer_state", "SIA", "unrecognized", "Sultanate of Kedah", "", "1821-11-12", "enforced", "1821-11-18", "Whole-slice approximation: the SIA slice of STATE_MALAYA stands for Kedah.")
goal("hai_santo_domingo", "hai_santo_domingo_1822", "conquer_state", "HAI", "recognized", "Republic of Spanish Haiti", "", "1822-01-15", "enforced", "1822-02-09", "Santo Domingo was the capital of the short-lived republic.")
goal("spa_rio_grande", "spa_mexico_1829", "return_state", "SPA", "recognized", "Mexico", "MEX", "1829-07-27", "dropped_peace", "1829-09-11", "Spain had not recognised Mexican independence: claim = 1, return_state. Tampico lies in STATE_RIO_GRANDE.")
goal("per_herat", "per_herat_1833", "make_tributary", "PER", "unrecognized", "Herat", "HER", "1833-07-01", "dropped_peace", "1833-11-30", "Nominal suzerainty acknowledged but not enforced; treated as dropped.")
goal("mad_south", "mad_radama_1817", "conquer_state", "MAD", "unrecognized", "Betsimisaraka and Sakalava chiefdoms", "", "1817-06-01", "enforced", "1824-12-31", "Decentralized owners; the MAD slice is the whole state.")
# ---------------- components: (goal_id, comp, state, slices, owner_type, standing, claim, unif, adjacent, interest, justification)
C = [
 ("egy_aleppo", "c1", "STATE_ALEPPO", "EGY", "recognized", "homeland", 0, 0, 0, 3, "Ottoman core province; Turkish homeland under a Turkish primary culture gives the 1.5 standing. Egypt not land-adjacent at claim time."),
 ("egy_syria", "c1", "STATE_SYRIA", "EGY", "recognized", "incorporated", 0, 0, 0, 3, "Ottoman province, Arab homeland only."),
 ("egy_lebanon", "c1", "STATE_LEBANON", "EGY", "recognized", "incorporated", 0, 0, 0, 3, "Ottoman province."),
 ("egy_palestine", "c1", "STATE_PALESTINE", "EGY", "recognized", "incorporated", 0, 0, 1, 3, "Ottoman province; adjacent to Egyptian Sinai."),
 ("egy_adana", "c1", "STATE_ADANA", "EGY", "recognized", "homeland", 0, 0, 0, 3, "EGY slice only (whole-slice rule); Turkish homeland."),
 ("egy_dongola", "c1", "STATE_DONGOLA", "EGY", "decentralized", "unincorporated", 0, 0, 1, 5, "Frontier under Shaiqiya chiefs; adjacent to Upper Egypt; Nile Basin is Egypt's home region."),
 ("egy_sennar", "c1", "STATE_BLUE_NILE", "EGY", "unrecognized", "capital", 0, 0, 0, 5, "Funj capital Sennar; Nile Basin home region."),
 ("egy_kordofan", "c1", "STATE_KORDOFAN", "EGY", "unrecognized", "incorporated", 0, 0, 0, 5, "Darfur's province, not its capital."),
 ("bol_north_peru", "c1", "STATE_LIMA", "NPU", "recognized", "capital", 0, 0, 0, 5, "Peru's capital; Andes is Bolivia's home region."),
 ("bol_north_peru", "c2", "STATE_CAJAMARCA", "NPU", "recognized", "incorporated", 0, 0, 0, 5, ""),
 ("bol_north_peru", "c3", "STATE_PASTAZA", "NPU", "recognized", "unincorporated", 0, 0, 0, 5, "Amazonian frontier; NPU slice only."),
 ("bol_south_peru", "c1", "STATE_ICA", "SPU", "recognized", "incorporated", 0, 0, 0, 5, ""),
 ("bol_south_peru", "c2", "STATE_AREQUIPA", "SPU", "recognized", "incorporated", 0, 0, 1, 5, "Adjacent to Bolivia."),
 ("bol_south_peru", "c3", "STATE_TARAPACA", "SPU", "recognized", "incorporated", 0, 0, 1, 5, "Adjacent to Bolivia's Litoral."),
 ("rus_armenia", "c1", "STATE_ARMENIA", "RUS", "unrecognized", "incorporated", 0, 0, 1, 3, "Erivan khanate, a Persian province; adjacent to Russian Georgia."),
 ("rus_azerbaijan", "c1", "STATE_AZERBAIJAN", "RUS", "unrecognized", "incorporated", 0, 0, 1, 3, "Nakhchivan khanate; adjacent to Russian Karabakh (Gulistan 1813)."),
 ("rus_dobrudja", "c1", "STATE_DOBRUDJA", "RUS", "recognized", "homeland", 0, 0, 1, 3, "Ottoman incorporated province with a Turkish homeland; adjacent to Bessarabia."),
 ("bic_arakan", "c1", "STATE_ARAKAN", "BIC", "unrecognized", "incorporated", 0, 0, 1, 3, "Burmese province since 1784; adjacent to Chittagong."),
 ("bic_tenasserim", "c1", "STATE_TENASSERIM", "BIC", "unrecognized", "incorporated", 0, 0, 0, 3, "Burmese province; no Company land border."),
 ("bic_assam", "c1", "STATE_ASSAM", "BIC", "unrecognized", "unincorporated", 0, 0, 1, 5, "APPROXIMATION (owner choice 2026-10-14): the 1836 BIC Assam slice also contains Cachar, annexed separately in 1832 and excluded from the ledger; the 1824 demand is priced on the whole slice. Burmese occupation of Ahom Assam since 1817, not an integrated province; North India is the Company's home region."),
]
for h in ("gbr", "fra", "rus"):
    for i, sk in enumerate(("STATE_ATTICA", "STATE_PELOPONNESE", "STATE_WEST_AEGEAN_ISLANDS"), 1):
        C.append((f"{h}_greece", f"c{i}", sk, "GRE", "recognized", "incorporated", 0, 0, 0, 3, "Released state of Greece; Ottoman incorporated province, Greek homeland."))
C += [
 ("fra_algiers", "c1", "STATE_ALGIERS", "FRA", "unrecognized", "capital", 0, 0, 0, 3, "Capital of the Regency."),
 ("fra_oran", "c1", "STATE_ORAN", "FRA", "unrecognized", "incorporated", 0, 0, 0, 3, "Beylik of Oran."),
 ("fra_constantine", "c1", "STATE_CONSTANTINE", "FRA", "unrecognized", "incorporated", 0, 0, 0, 3, "Beylik of Constantine; the French slice is Bone."),
]
for h, adj in (("fra", 1), ("gbr", 0)):
    C += [
     (f"{h}_belgium", "c1", "STATE_FLANDERS", "BEL", "recognized", "incorporated", 0, 0, adj, 5, "Released state; Dutch incorporated province, Flemish homeland. Western Europe is the backer's home region."),
     (f"{h}_belgium", "c2", "STATE_WALLONIA", "BEL", "recognized", "incorporated", 0, 0, adj, 5, "Released state; BEL slice only (Luxembourg's slice stays)."),
     (f"{h}_belgium", "c3", "STATE_GELRE", "BEL", "recognized", "homeland", 0, 0, 0, 5, "Released state (Limburg); Dutch homeland under the Dutch owner gives 1.5."),
    ]
C += [
 ("net_flanders", "c1", "STATE_FLANDERS", "BEL", "recognized", "capital", 1, 0, 1, 5, "Belgium's capital state; Dutch claim."),
 ("net_wallonia", "c1", "STATE_WALLONIA", "BEL", "recognized", "incorporated", 1, 0, 1, 5, "BEL slice only; Dutch claim."),
 ("net_gelre", "c1", "STATE_GELRE", "BEL", "recognized", "incorporated", 1, 0, 1, 5, "BEL slice (Limburg); Dutch claim; Dutch homeland gives the aggressor-homeland reduction."),
 ("pan_peshawar", "c1", "STATE_PASHTUNISTAN", "PAN", "unrecognized", "incorporated", 0, 0, 1, 3, "Barakzai sardars' domain; adjacent to the Punjab; Greater Persia is not Punjab's home region."),
 ("pan_ladakh", "c1", "STATE_KASHMIR", "LAD", "unrecognized", "capital", 0, 0, 1, 3, "Ladakh's capital state; adjacent across the Punjab hills."),
 ("dai_cambodia", "c1", "STATE_CAMBODIA", "CAM", "unrecognized", "capital", 0, 0, 1, 5, "Cambodia's capital state; Indochina is Vietnam's home region."),
 ("sia_cambodia", "c1", "STATE_CAMBODIA", "CAM", "unrecognized", "capital", 0, 0, 1, 5, "As above for Siam."),
 ("sia_vientiane", "c1", "STATE_LAOS", "SIA", "unrecognized", "capital", 0, 0, 1, 5, "Vientiane, the kingdom's capital; the SIA slice."),
 ("sia_kedah", "c1", "STATE_MALAYA", "SIA", "unrecognized", "capital", 0, 0, 1, 5, "Kedah's capital; whole SIA slice stands for the sultanate."),
 ("hai_santo_domingo", "c1", "STATE_SANTO_DOMINGO", "HAI", "recognized", "capital", 0, 0, 1, 5, "Capital of Spanish Haiti; Central America is Haiti's home region."),
 ("spa_rio_grande", "c1", "STATE_RIO_GRANDE", "MEX", "recognized", "incorporated", 1, 0, 0, 3, "Mexican province; Spanish claim from non-recognition."),
 ("per_herat", "c1", "STATE_HERAT", "HER", "unrecognized", "capital", 0, 0, 1, 5, "Herat's capital; Greater Persia is Persia's home region."),
 ("per_herat", "c2", "STATE_CENTRAL_HIGHLANDS", "HER", "unrecognized", "unincorporated", 0, 0, 0, 5, "HER slice only; hinterland."),
 ("mad_south", "c1", "STATE_SOUTH_MADAGASCAR", "MAD", "decentralized", "unincorporated", 0, 0, 1, 5, "Chiefdoms; East Africa is Merina's home region."),
]
HOLDER = {g[0]: g[3] for g in G}
with open(OUT / "acts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["act_id", "title", "start_date", "end_date", "source", "notes"]); w.writerows(ACTS)
with open(OUT / "goals.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["goal_id", "act_id", "wargoal", "holder", "holder_tag_1836", "holder_type", "target", "stakeholder", "victim_tag_1836", "claim_date", "resolution", "resolution_date", "loyal_subject", "rebellious_subject", "general_mult_source", "notes"]); w.writerows(G)
with open(OUT / "goal_states.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["goal_id", "component_id", "state_key", "slices_1836", "owner_type", "standing", "aggressor_homeland", "shared_language", "claim", "scripted_unification", "adjacent", "interest_tier", "justification"])
    for gid, comp, sk, slices, otype, standing, claim, unif, adj, tier, just in C:
        ah, sl = flags(HOLDER[gid], sk)
        w.writerow([gid, comp, sk, slices, otype, standing, ah, sl, claim, unif, adj, tier, just + f" [computed from vanilla: aggressor_homeland={ah}, shared_language={sl}]"])
print(f"acts {len(ACTS)}, goals {len(G)}, components {len(C)}")
for gid, comp, sk, *_ in C:
    ah, sl = flags(HOLDER[gid], sk)
    if ah or sl: print(f"  {gid}/{sk}: aggressor_homeland={ah} shared_language={sl}")

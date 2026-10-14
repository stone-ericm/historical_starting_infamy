"""Research helper for the ledger: prints the vanilla 1836 facts behind each mapping judgment.
Usage: python3 research/scripts/vanilla_lookup.py <game_dir> HOLDER:STATE_KEY[,STATE_KEY...] ...   or   owners:TAG   or   find:KEYWORD"""
import re, sys
from pathlib import Path
V = Path(sys.argv[1])
def blocks(text, pat):
    for m in re.finditer(pat, text):
        i = m.end(); d = 1; j = i
        while d and j < len(text):
            d += (text[j] == "{") - (text[j] == "}"); j += 1
        yield m.group(1), text[i:j-1]
states_txt = (V/"common/history/states/00_states.txt").read_text(encoding="utf-8-sig")
STATES = {}
for name, blk in blocks(states_txt, r"s:(STATE_[A-Z0-9_]+)\s*=\s*\{"):
    owners = []
    for _, cs in blocks(blk, r"(create_state)\s*=\s*\{"):
        tag = re.search(r"country\s*=\s*c:([A-Z0-9]+)", cs).group(1)
        stype = re.search(r"state_type\s*=\s*(\w+)", cs)
        owners.append((tag, stype.group(1) if stype else "incorporated"))
    STATES[name] = {"owners": owners,
                    "homelands": re.findall(r"add_homeland\s*=\s*cu:([a-z_]+)", blk),
                    "claims": re.findall(r"add_claim\s*=\s*c:([A-Z0-9]+)", blk)}
cult_txt = "".join(p.read_text(encoding="utf-8-sig") for p in (V/"common/cultures").glob("*.txt"))
CULT = {}
for name, blk in blocks(cult_txt, r"(?m)^([a-z_]+)\s*=\s*\{"):
    # 1.14.5 cultures carry one `language = language_x` field, not a traits block (CLAUDE.md gotcha; review R1 finding L7)
    lang = re.search(r"(?m)^\s*language\s*=\s*([a-z_]+)", blk)
    CULT[name] = {lang.group(1)} if lang else set()
cdef_txt = "".join(p.read_text(encoding="utf-8-sig") for p in (V/"common/country_definitions").glob("*.txt"))
CDEF = {}
for tag, blk in blocks(cdef_txt, r"(?m)^([A-Z][A-Z0-9]{2})\s*=\s*\{"):
    cu = re.search(r"cultures\s*=\s*\{([^}]*)\}", blk); cap = re.search(r"capital\s*=\s*(STATE_[A-Z0-9_]+)", blk)
    ctype = re.search(r"country_type\s*=\s*(\w+)", blk)
    CDEF[tag] = {"cultures": cu.group(1).split() if cu else [], "capital": cap.group(1) if cap else None, "type": ctype.group(1) if ctype else "?"}
REGION = {}
for p in (V/"common/strategic_regions").glob("*.txt"):
    for name, blk in blocks(p.read_text(encoding="utf-8-sig"), r"(?m)^(region_[a-z_]+)\s*=\s*\{"):
        for s in re.findall(r"(STATE_[A-Z0-9_]+)", blk): REGION[s] = name
subj_txt = (V/"common/history/diplomacy/00_subject_relationships.txt").read_text(encoding="utf-8-sig")
SUBJ = {}
for overlord, blk in blocks(subj_txt, r"c:([A-Z0-9]+)\s*\?=\s*\{"):
    for m in re.finditer(r"country\s*=\s*c:([A-Z0-9]+)\s*type\s*=\s*(\w+)", blk): SUBJ[m.group(1)] = (overlord, m.group(2))
def langs(cultures): return set().union(*(CULT.get(c, set()) for c in cultures))
for arg in sys.argv[2:]:
    if arg.startswith("find:"):
        kw = arg[5:]; print(f"## find {kw}:", [s for s in STATES if kw in s]); continue
    if arg.startswith("owners:"):
        tag = arg[7:]; print(f"## states with a {tag} slice:", [s for s, d in STATES.items() if any(o == tag for o, _ in d["owners"])]); 
        print(f"   {tag}: type={CDEF.get(tag,{}).get('type')} capital={CDEF.get(tag,{}).get('capital')} subject_of={SUBJ.get(tag)} cultures={CDEF.get(tag,{}).get('cultures')}"); continue
    holder, keys = arg.split(":"); hl = langs(CDEF[holder]["cultures"]); hreg = REGION.get(CDEF[holder]["capital"])
    print(f"## holder {holder} type={CDEF[holder]['type']} cultures={CDEF[holder]['cultures']} langs={sorted(hl)} capital_region={hreg}")
    for k in keys.split(","):
        d = STATES.get(k)
        if not d: print(f"   {k}: NOT FOUND"); continue
        hl_shared = [c for c in d["homelands"] if CULT.get(c, set()) & hl]
        print(f"   {k}: owners={d['owners']} region={REGION.get(k)} same_region_as_holder_capital={REGION.get(k)==hreg} homelands={d['homelands']} shared_language_via={hl_shared} aggressor_homeland={any(c in CDEF[holder]['cultures'] for c in d['homelands'])} claims1836={d['claims']}")

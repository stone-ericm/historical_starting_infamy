# tools/tests/fixtures/make_probe_log.py
"""Deterministic synthetic probe output matching the fixture ledger. Used by test_measurement and the
Task 11 golden test. Numbers are invented but internally consistent with hsi.formula."""
from pathlib import Path

SLICES = [("STATE_ALEPPO", "EGY", 0), ("STATE_SYRIA", "EGY", 0), ("STATE_ATTICA", "GRE", 0),
          ("STATE_PELOPONNESE", "GRE", 0), ("STATE_HEDJAZ", "HDJ", 1)]
COUNTRIES = {"EGY": (1, -0.05, -0.1, 0.0, 0.0), "GBR": (0, -0.05, -0.3, 0.1, 0.0),
             "BOL": (0, 0.0, 0.0, 0.0, 50.0), "FRA": (0, -0.05, -0.3, 0.0, 0.0), "TUR": (0, 0.0, 0.0, 0.0, 0.0)}
RANKS = {"EGY": 3, "GBR": 7, "BOL": 5, "FRA": 7, "TUR": 6}   # unrecognized major, great, minor, great, major (the ledger's victim)
HOLDERS = ["EGY", "GBR"]

def shares(i, sample, zero_gdp_at_start=False):
    pop = 1.90 + 0.10 * i + 0.002 * sample
    gdp = 0.0 if (sample == 0 and zero_gdp_at_start) else 1.10 + 0.05 * i + 0.001 * sample
    return pop, gdp

def lines(months=3, zero_gdp_at_start=False):
    out = []
    def state_lines(hook, sample, datestr):
        out.append(f"HSI;{hook};{sample};{datestr};GLOBAL;-;pop=1,022,805,087;gdp=2,000,000,000.00")
        for i, (sk, owner, otype) in enumerate(SLICES):
            pop, gdp = shares(i, sample, zero_gdp_at_start)
            out.append(f"HSI;{hook};{sample};{datestr};STATE;{sk}/{owner};owner_type={otype};pop=500,000;gdp=300,000.00;"
                       f"pop_share_uncapped={pop:.4f};gdp_share_uncapped={gdp:.4f};incorporated=1;capital=0;owner_homeland=1;base={(5+pop+gdp)*1.5:.4f}")
        for tag, (ctype, gen, unrec, decay, inf) in COUNTRIES.items():
            out.append(f"HSI;{hook};{sample};{datestr};COUNTRY;{tag};country_type={ctype};rank={RANKS[tag]};gen_mult={gen:.4f};unrec_mult={unrec:.4f};decay_mult={decay:.4f};infamy={inf:.4f}")
    for hook in ("start_a", "start_b"):
        state_lines(hook, 0, "lobby")
        out.append(f"HSI;{hook};0;lobby;RULE;-;flag=very_low")
    for m in range(1, months + 1):
        datestr = ["February 1, 1836", "March 1, 1836", "April 1, 1836"][m - 1]
        state_lines("monthly", m, datestr)
        for holder in HOLDERS:
            for i, (sk, owner, otype) in enumerate(SLICES):
                pop, gdp = shares(i, m, zero_gdp_at_start)
                siv = (5 + pop + gdp) * 1.5 * (0.85 if holder == "EGY" else 1.0) * (0.9 if holder == "EGY" else 1.0)
                if holder == "GBR" and otype != 0:
                    siv *= 1.0 + COUNTRIES["GBR"][2]      # recognized holder vs unrecognized owner: x(1 + unrec_mult)
                out.append(f"HSI;monthly;{m};{datestr};DIAG;{holder}/{sk}/{owner};root_tag={holder};aggressor_homeland=0;homeland_bonus=0;"
                           f"shared_language={1 if holder == 'EGY' else 0};language_bonus=0;claim=0;scripted_unification=0;"
                           f"adjacent={1 if holder == 'EGY' else 0};interest_bucket=3;root_type={1 if holder == 'EGY' else 0};owner_type={otype};"
                           f"unrec_mult={COUNTRIES[holder][2]:.4f};pop_share_uncapped={pop:.4f};gdp_share_uncapped={gdp:.4f};incorporated=1;capital=0;owner_homeland=1;base={(5+pop+gdp)*1.5:.4f};siv={max(siv, 1.0):.4f}")
    return out

def write(path: Path, **kw):
    body = "\n".join(f"[12:00:00][jomini_script_system.cpp:123]: {l}" for l in lines(**kw)) + "\n"
    path.write_text(body, encoding="utf-8")
    return path

def write_rotated(directory: Path, parts: int = 3, **kw):
    """The same log split across debug.<parts-1>.log ... debug.1.log, debug.log (oldest has the highest index)."""
    ls = [f"[12:00:00][jomini_script_system.cpp:123]: {l}" for l in lines(**kw)]
    n = len(ls); step = (n + parts - 1) // parts
    chunks = [ls[i:i + step] for i in range(0, n, step)]
    names = [f"debug.{parts - 1 - i}.log" if i < parts - 1 else "debug.log" for i in range(len(chunks))]
    for name, chunk in zip(names, chunks):
        (directory / name).write_text("\n".join(chunk) + "\n", encoding="utf-8")
    return [directory / n for n in names]

if __name__ == "__main__":
    import sys
    write(Path(sys.argv[1]))

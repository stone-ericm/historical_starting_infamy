# tools/hsi/measurement.py
"""Probe output: HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v... (spec §6). Snapshot selection with the
2 % stabilization policy and the measurement manifest (spec §6, §7)."""
from dataclasses import dataclass
import hashlib
import math
import re
import sys
from pathlib import Path

KINDS = {"GLOBAL", "STATE", "COUNTRY", "DIAG", "RULE"}
MANIFEST = "manifest.sha256"
SAVES_DIR = "saves"   # gitignored; never listed in the manifest

class MeasurementError(Exception):
    pass

class ManifestError(Exception):
    pass

@dataclass(frozen=True)
class Record:
    hook: str
    sample: int
    date: str
    kind: str
    key: str
    fields: dict

_NUM_CLEAN = str.maketrans({",": "", " ": "", "−": "-", " ": ""})

def parse_number(s: str) -> float:
    t = s.translate(_NUM_CLEAN)
    try:
        x = float(t)
    except ValueError:
        raise MeasurementError(f"not a number: {s!r}")
    if not math.isfinite(x):
        raise MeasurementError(f"non-finite number: {s!r}")
    return x

def rotation_index(path: Path) -> int:
    """debug.log -> 0 (newest), debug.1.log -> 1, debug.2.log -> 2 ... (older). The engine rotates every 512 KB
    (observed 2026-10-14: one probe session spanned debug.2.log, debug.1.log and debug.log)."""
    m = re.fullmatch(r"(.+?)\.(\d+)\.log", Path(path).name)
    return int(m.group(2)) if m else 0

def extract(debug_log) -> list:
    """HSI payloads from one log file, or from several rotated files read oldest first (highest index first)."""
    paths = [Path(debug_log)] if isinstance(debug_log, (str, Path)) else [Path(p) for p in debug_log]
    paths = sorted(paths, key=lambda p: -rotation_index(p))
    out = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                i = line.find("HSI;")
                if i >= 0:
                    out.append(line[i:].rstrip("\r\n"))
    return out

def session_logs(directory: Path, stem: str = "debug") -> list:
    """Every <stem>*.log in a measurement directory, oldest rotation first."""
    paths = [p for p in Path(directory).iterdir() if re.fullmatch(rf"{stem}(\.\d+)?\.log", p.name)]
    return sorted(paths, key=lambda p: -rotation_index(p))

def parse_lines(lines) -> list:
    recs = []
    for n, line in enumerate(lines, start=1):
        parts = line.split(";")
        if len(parts) < 6 or parts[0] != "HSI":
            raise MeasurementError(f"line {n}: malformed record {line!r}")
        _, hook, sample, date, kind, key = parts[:6]
        if kind not in KINDS:
            raise MeasurementError(f"line {n}: unknown kind {kind!r}")
        try:
            sample_i = int(sample)
        except ValueError:
            raise MeasurementError(f"line {n}: sample must be an integer, got {sample!r}")
        fields = {}
        for kv in parts[6:]:
            if "=" not in kv:
                raise MeasurementError(f"line {n}: field without '=': {kv!r}")
            k, v = kv.split("=", 1)
            if k in fields:
                raise MeasurementError(f"line {n}: duplicate field {k}")
            fields[k] = v
        recs.append(Record(hook, sample_i, date, kind, key, fields))
    return recs

def group_samples(records) -> dict:
    groups: dict = {}
    seen = set()
    for r in records:
        ident = (r.hook, r.sample, r.kind, r.key)
        if ident in seen:
            raise MeasurementError(f"duplicate record {ident}")
        seen.add(ident)
        groups.setdefault((r.hook, r.sample), []).append(r)
    return groups

@dataclass
class Snapshot:
    hook: str
    sample: int
    date: str
    global_pop: float
    global_gdp: float
    slices: dict
    countries: dict
    diag: dict
    rule: str | None

    def slice(self, state_key: str, owner: str) -> dict:
        try:
            return self.slices[(state_key, owner)]
        except KeyError:
            raise MeasurementError(f"slice {state_key}/{owner} not in sample {self.hook}/{self.sample}")

    def country(self, tag: str) -> dict:
        try:
            return self.countries[tag]
        except KeyError:
            raise MeasurementError(f"country {tag} not in sample {self.hook}/{self.sample}")

def _numeric(fields: dict, skip=()) -> dict:
    return {k: parse_number(v) for k, v in fields.items() if k not in skip}

def build_snapshot(records) -> Snapshot:
    globals_ = [r for r in records if r.kind == "GLOBAL"]
    if len(globals_) != 1:
        raise MeasurementError(f"sample needs exactly one GLOBAL record, has {len(globals_)}")
    g = globals_[0]
    slices, countries, diag, rule = {}, {}, {}, None
    for r in records:
        if r.kind == "STATE":
            sk, owner = r.key.split("/")
            slices[(sk, owner)] = _numeric(r.fields)
        elif r.kind == "COUNTRY":
            countries[r.key] = _numeric(r.fields)
        elif r.kind == "DIAG":
            holder, sk, owner = r.key.split("/")
            d = _numeric(r.fields, skip=("root_tag",))
            d["root_tag"] = r.fields.get("root_tag", "")
            if d["root_tag"] != holder:
                raise MeasurementError(f"DIAG {r.key}: root_tag {d['root_tag']!r} is not the holder")
            diag[(holder, sk, owner)] = d
        elif r.kind == "RULE":
            rule = r.fields.get("flag")
    return Snapshot(g.hook, g.sample, g.date, parse_number(g.fields["pop"]), parse_number(g.fields["gdp"]),
                    slices, countries, diag, rule)

SCHEMA = {   # every field a record of each kind must carry (probe_gen renders exactly these)
    "GLOBAL": ("pop", "gdp"),
    "STATE": ("owner_type", "pop", "gdp", "pop_share_uncapped", "gdp_share_uncapped", "incorporated", "capital", "owner_homeland", "base"),
    "COUNTRY": ("country_type", "rank", "gen_mult", "unrec_mult", "decay_mult", "infamy"),
    "DIAG": ("root_tag", "aggressor_homeland", "homeland_bonus", "shared_language", "language_bonus", "claim", "scripted_unification",
             "adjacent", "interest_bucket", "root_type", "owner_type", "unrec_mult", "pop_share_uncapped", "gdp_share_uncapped",
             "incorporated", "capital", "owner_homeland", "base", "siv"),
    "RULE": ("flag",),
}
CODES = {"aggressor_homeland": (0, 1), "homeland_bonus": (0, 1), "shared_language": (0, 1), "language_bonus": (0, 1), "claim": (0, 1),
         "scripted_unification": (0, 1), "adjacent": (0, 1), "interest_bucket": (1, 2, 3, 5), "root_type": (0, 1, 2), "owner_type": (0, 1, 2),
         "country_type": (0, 1, 2), "incorporated": (0, 1), "capital": (0, 1), "owner_homeland": (0, 1),
         "rank": (0, 1, 2, 3, 4, 5, 6, 7)}   # 7 great, 6 major, 5 minor, 4 insignificant, 3 unrec major, 2 unrec regional, 1 unrec, 0 decentralized
RULE_FLAGS = ("very_low", "low", "standard", "high", "very_high")
SAMPLER_KINDS = ("GLOBAL", "STATE", "COUNTRY", "RULE")
_MONTHS = {m: i for i, m in enumerate(("January", "February", "March", "April", "May", "June", "July", "August",
                                       "September", "October", "November", "December"), start=1)}

def parse_game_date(s: str):
    """'April 1, 1836' -> datetime.date; the engine's GetString form. Raises MeasurementError otherwise."""
    import datetime
    m = re.fullmatch(r"\s*([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})\s*", s)
    if not m or m.group(1) not in _MONTHS:
        raise MeasurementError(f"unparseable game date {s!r}")
    try:
        return datetime.date(int(m.group(3)), _MONTHS[m.group(1)], int(m.group(2)))
    except ValueError as e:
        raise MeasurementError(f"invalid calendar date {s!r}: {e}")

def check_record_schema(r, label: str) -> list:
    problems = []
    for f in SCHEMA[r.kind]:
        if f not in r.fields:
            problems.append(f"{label}: {r.kind} {r.key} lacks {f}")
    for f in r.fields:
        if f not in SCHEMA[r.kind]:
            problems.append(f"{label}: {r.kind} {r.key} has an unexpected field {f}")
    if r.kind == "RULE":
        if r.fields.get("flag") not in RULE_FLAGS:
            problems.append(f"{label}: RULE flag {r.fields.get('flag')!r} is not a known rule")
        return problems
    for f, v in r.fields.items():
        if f == "root_tag":
            continue
        try:
            x = parse_number(v)
        except MeasurementError as e:
            problems.append(f"{label}: {r.kind} {r.key} {f}: {e}"); continue
        if f in CODES and x not in CODES[f]:
            problems.append(f"{label}: {r.kind} {r.key} {f}={v} is not one of {CODES[f]}")
    return problems

def expected_receipt(ledger_slices, holder_tags, config: dict, victim_tags=()) -> dict:
    """What one complete probe boot must have logged, derived from the ledger and the probe config
    exactly as probe_gen.render derives the probe (review R1 finding B4)."""
    from .participants import probe_slices, probe_tags, diag_pairs
    class _Led:   # the participants helpers read these three things from a Ledger
        def __init__(self, s, h, v): self._s, self._h, self._v = s, h, v
        def all_slices(self): return set(self._s)
        def holder_tags(self): return set(self._h)
        @property
        def goals(self): return {i: type("G", (), {"victim_tag_1836": v})() for i, v in enumerate(self._v)}
    led = _Led(ledger_slices, holder_tags, victim_tags or ())
    diag = {(h, sk, owner) for h, pairs in diag_pairs(led, config).items() for sk, owner in pairs}
    required = set(probe_tags(_Led(ledger_slices, holder_tags, ()), config))     # holders, fixture holder, targets, BOL, sampler
    tags = set(probe_tags(led, config))
    # a victim's record only supplies its rank; a victim the boot did not log gets the declared fallback, labelled
    # "fallback-unmeasured" in the derivation (final review F5), so its absence is reported, not refused
    return {"months": int(config["months"]), "slices": set(probe_slices(led, config)), "tags": required,
            "optional_tags": tags - required, "diag": diag, "rule": config.get("rule")}

def missing_optional(records, expected: dict) -> list:
    """Optional (victim-only) COUNTRY records absent from the day-one sample."""
    groups = group_samples(records)
    have = {r.key for r in groups.get(("start_b", 0), []) if r.kind == "COUNTRY"}
    return sorted(expected.get("optional_tags", set()) - have)

def check_receipt(records, expected: dict, require_monthly: bool = True) -> list:
    """Both start hooks (and, when required, every configured monthly sample) must be complete, and the sampler's
    records of one sample must share one firing date. Returns the list of problems (empty when complete).
    With require_monthly=False the monthly samples are checked only if present (the day-one snapshot is the
    reconstruction input; the monthly samples feed the formula check, ruling 2026-10-14)."""
    problems = []
    groups = group_samples(records)
    monthly = [("monthly", m) for m in range(1, expected["months"] + 1)]
    want = [("start_a", 0), ("start_b", 0)] + monthly
    for hook, sample in sorted(set(groups) - set(want)):
        problems.append(f"unexpected group {hook} sample {sample}: outside the configured receipt ({expected['months']} monthly samples)")
    if not require_monthly:
        want = [("start_a", 0), ("start_b", 0)] + [k for k in monthly if k in groups]
    sampler_dates = {}
    for hook, sample in want:
        label = f"{hook} sample {sample}" if hook == "monthly" else hook
        rs = groups.get((hook, sample))
        if not rs:
            problems.append(f"{label}: missing entirely" + (f" (monthly sample {sample})" if hook == "monthly" else ""))
            continue
        kinds = {}
        for r in rs:
            kinds.setdefault(r.kind, []).append(r)
        if len(kinds.get("GLOBAL", [])) != 1:
            problems.append(f"{label}: needs exactly one GLOBAL record, has {len(kinds.get('GLOBAL', []))}")
        if hook != "monthly" and len(kinds.get("RULE", [])) != 1:
            problems.append(f"{label}: needs exactly one RULE record, has {len(kinds.get('RULE', []))}")
        strict = require_monthly or hook != "monthly"      # a short monthly sample still feeds the formula check
        have_slices = {tuple(r.key.split("/")) for r in kinds.get("STATE", [])}
        for sk, owner in sorted(expected["slices"] - have_slices):
            if strict: problems.append(f"{label}: missing STATE {sk}/{owner}")
        for key in sorted(have_slices - expected["slices"]):
            problems.append(f"{label}: unexpected STATE {'/'.join(key)} (not in the ledger or the capture plan)")
        have_tags = {r.key for r in kinds.get("COUNTRY", [])}
        for t in sorted(expected["tags"] - have_tags):
            if strict: problems.append(f"{label}: missing COUNTRY {t}")
        for t in sorted(have_tags - expected["tags"] - expected.get("optional_tags", set())):
            problems.append(f"{label}: unexpected COUNTRY {t}")
        for kind in ({"RULE"} if hook == "monthly" else {"DIAG"}):   # RULE is a start-hook record, DIAG a monthly one
            if kind in kinds:
                problems.append(f"{label}: {kind} records do not belong in this sample")
        for r in rs:
            problems += check_record_schema(r, label)
        dates = {r.date for r in rs if r.kind in SAMPLER_KINDS}
        if len(dates) != 1:
            problems.append(f"{label}: sampler records carry {len(dates)} dates {sorted(dates)}; one firing date expected")
        if hook == "start_b" and expected.get("rule"):
            flags = [r.fields.get("flag") for r in kinds.get("RULE", [])]
            if flags and flags != [expected["rule"]]:
                problems.append(f"{label}: RULE flag {flags[0]!r} but the lobby was set to {expected['rule']!r} (start_a is an observation; start_b must match)")
        if hook == "monthly":
            if len(dates) == 1:
                try:
                    sampler_dates[sample] = parse_game_date(next(iter(dates)))
                except MeasurementError as e:
                    problems.append(f"{label}: {e}")
            have_diag = {tuple(r.key.split("/")) for r in kinds.get("DIAG", [])}
            for h, sk, owner in sorted(expected["diag"] - have_diag):
                if strict: problems.append(f"{label}: missing DIAG {h}/{sk}/{owner}")
            for key in sorted(have_diag - expected["diag"]):
                problems.append(f"{label}: unexpected DIAG {'/'.join(key)}")
            # one root fires once per sample: all its DIAG records share one date, within a month of the sampler's
            per_root: dict = {}
            for r in kinds.get("DIAG", []):
                per_root.setdefault(r.key.split("/")[0], set()).add(r.date)
            for root, ds in sorted(per_root.items()):
                if len(ds) != 1:
                    problems.append(f"{label}: DIAG root {root} carries {len(ds)} dates {sorted(ds)}; one firing expected")
                    continue
                try:
                    d = parse_game_date(next(iter(ds)))
                except MeasurementError as e:
                    problems.append(f"{label}: DIAG root {root}: {e}"); continue
                if sample in sampler_dates and abs((d - sampler_dates[sample]).days) > 31:
                    problems.append(f"{label}: DIAG root {root} fired on {d} but the sampler on {sampler_dates[sample]}; not the same month")
        try:
            build_snapshot(rs)
        except (MeasurementError, KeyError, ValueError) as e:
            problems.append(f"{label}: cannot build the sample: {e!r}")
    ordered = [sampler_dates[k] for k in sorted(sampler_dates)]
    if any(b <= a for a, b in zip(ordered, ordered[1:])):
        problems.append(f"monthly sampler dates are not strictly increasing: {sampler_dates}")
    return problems

def start_snapshot(records) -> Snapshot:
    """The after-lobby day-one sample (start_b): the reconstruction's shares, denominators, modifiers and ranks."""
    groups = group_samples(records)
    if ("start_b", 0) not in groups:
        raise MeasurementError("no start_b sample: the after-lobby hook did not log")
    return build_snapshot(groups[("start_b", 0)])

def monthly_snapshots(records) -> list:
    groups = group_samples(records)
    return [build_snapshot(groups[k]) for k in sorted(k for k in groups if k[0] == "monthly")]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(directory: Path, names) -> Path:
    directory = Path(directory)
    names = sorted(names)
    if MANIFEST in names:
        raise ManifestError("the manifest never lists itself")
    body = "".join(f"{sha256_file(directory / n)}  {n}\n" for n in names)
    out = directory / MANIFEST
    out.write_text(body, encoding="utf-8")
    return out

def verify_manifest(directory: Path) -> list:
    directory = Path(directory)
    mp = directory / MANIFEST
    if not mp.exists():
        raise ManifestError(f"{mp} missing")
    listed = {}
    for line in mp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        listed[name] = digest
    present = {p.name for p in directory.iterdir() if p.is_file() and p.name != MANIFEST}
    problems = [f"unexpected file {n}" for n in sorted(present - set(listed))]
    for name, digest in listed.items():
        p = directory / name
        if not p.exists():
            problems.append(f"missing file {name}")
        elif sha256_file(p) != digest:
            problems.append(f"digest mismatch {name}")
    if problems:
        raise ManifestError("\n".join(problems))
    return sorted(listed)

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract"); ex.add_argument("--debug-log", required=True, nargs="+", help="debug.log and its rotated siblings, any order"); ex.add_argument("--out", required=True)
    ck = sub.add_parser("check", help="receipt check against the ledger and probe config; run on the live logs before quitting")
    ck.add_argument("--debug-log", required=True, nargs="+"); ck.add_argument("--research", required=True); ck.add_argument("--probe-config", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        import json
        from .ledger import load_ledger
        led = load_ledger(Path(a.research))
        config = json.loads(Path(a.probe_config).read_text(encoding="utf-8"))
        try:
            recs = parse_lines(extract(a.debug_log))
            problems = check_receipt(recs, expected_receipt(led.all_slices(), led.holder_tags(), config, led.victim_tags()))
        except MeasurementError as e:
            problems = [str(e)]
        for p in problems:
            print(p, file=sys.stderr)
        print("receipt: " + ("COMPLETE" if not problems else f"INCOMPLETE ({len(problems)} problem(s))"))
        return 0 if not problems else 1
    if a.cmd == "extract":
        payloads = extract(a.debug_log)
        recs = parse_lines(payloads)
        groups = group_samples(recs)
        Path(a.out).write_text("\n".join(payloads) + "\n", encoding="utf-8")
        for (hook, sample), rs in sorted(groups.items()):
            kinds = {}
            for r in rs:
                kinds[r.kind] = kinds.get(r.kind, 0) + 1
            print(f"{hook} sample {sample} date {rs[0].date}: {kinds}")
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())

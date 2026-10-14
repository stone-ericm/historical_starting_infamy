# tools/hsi/savecheck.py
"""Structural reader for plaintext 1.14 saves and the acceptance comparison (spec section 9 steps 3-6; hardened
after the final review F2). What it checks: the whole file is lexically balanced (quoted strings are opaque); the
protected blocks (meta_data, variables, country_manager.database) are read with the same quote-aware reader; every
country definition appears once; every parsed infamy is a finite number; the guard flag appears exactly once; Bolivia's
record is present at vanilla's 50; every emitted country is at its table value within a tolerance that cannot hide a
wrong whole number; every other country is at 0. It does not parse every game subsystem."""
from dataclasses import dataclass
import json
import math
import re
import sys
from pathlib import Path
from . import constants as K

class SaveParseError(Exception):
    pass

def _scan(text: str, start: int):
    """Yield (index, char) for structural characters only: braces outside quoted strings."""
    i, n = start, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = text.find('"', i + 1)
            if j < 0:
                raise SaveParseError(f"unterminated string at offset {i}")
            i = j + 1
            continue
        if c in "{}":
            yield i, c
        i += 1

def check_balanced(text: str) -> None:
    depth = 0
    for i, c in _scan(text, 0):
        depth += 1 if c == "{" else -1
        if depth < 0:
            raise SaveParseError(f"closing brace before opening at offset {i}")
    if depth != 0:
        raise SaveParseError(f"unbalanced file: depth {depth} at end")

def block_at(text: str, idx: int) -> str:
    i = text.index("{", idx)
    depth = 0
    for k, c in _scan(text, i):
        depth += 1 if c == "{" else -1
        if depth == 0:
            return text[i:k + 1]
    raise SaveParseError(f"unbalanced block starting at offset {idx}")

def top_block(text: str, key: str) -> str:
    m = re.search(r"(?m)^" + re.escape(key) + r"=\{", text)
    if not m:
        raise SaveParseError(f"top-level block {key!r} not found")
    return block_at(text, m.start())

def children(block: str) -> list:
    """Direct `name={...}` children of a balanced block (quote-aware depth)."""
    inner = block[1:-1]
    out = []
    pos = 0
    depth = 0
    structural = {i: c for i, c in _scan(inner, 0)}
    for m in re.finditer(r"([A-Za-z0-9_]+)=\{", inner):
        if m.end() - 1 not in structural:
            continue
        depth = sum(1 if c == "{" else -1 for i, c in structural.items() if i < m.start())
        if depth != 0 or m.start() < pos:
            continue
        child = block_at(inner, m.start())
        out.append((m.group(1), child))
        pos = m.start() + len(child)
    return out

def depth1_scalars(block: str) -> dict:
    """name=value pairs at depth 1 only; nested blocks are skipped; a repeated name is an error."""
    inner = block[1:-1]
    out, depth, i, line_start = {}, 0, 0, 0
    structural = {i: c for i, c in _scan(inner, 0)}
    while i < len(inner):
        c = inner[i]
        if i in structural:
            depth += 1 if c == "{" else -1
        elif c == "\n":
            if depth == 0:
                m = re.match(r"\s*([A-Za-z0-9_]+)=([^{}\s]+)\s*$", inner[line_start:i])
                if m:
                    if m.group(1) in out:
                        raise SaveParseError(f"duplicate scalar {m.group(1)} inside one record")
                    out[m.group(1)] = m.group(2).strip('"')
            line_start = i + 1
        i += 1
    return out

@dataclass
class SaveInfo:
    game_date: str
    rule_flags: set
    countries: dict
    global_flag_counts: dict

def _finite(s: str, what: str) -> float:
    try:
        x = float(s)
    except ValueError:
        raise SaveParseError(f"{what}: not a number: {s!r}")
    if not math.isfinite(x):
        raise SaveParseError(f"{what}: non-finite value {s!r}")
    return x

def parse_save(path: Path) -> SaveInfo:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    check_balanced(text)
    meta = top_block(text, "meta_data")
    scal = depth1_scalars(meta)
    if "game_date" not in scal:
        raise SaveParseError("meta_data.game_date missing")
    rules = ""
    for name, blk in children(meta):
        if name == "game_rules":
            for n2, b2 in children(blk):
                if n2 == "settings":
                    rules = b2
    flags = set(re.findall(r"[A-Za-z0-9_]+", rules[1:-1])) if rules else set()
    countries = {}
    db = [b for n, b in children(top_block(text, "country_manager")) if n == "database"]
    if len(db) != 1:
        raise SaveParseError(f"country_manager.database: expected one block, found {len(db)}")
    for _id, rec in children(db[0]):
        s = depth1_scalars(rec)
        if "definition" in s:
            tag = s["definition"]
            if tag in countries:
                raise SaveParseError(f"country {tag} defined twice")
            countries[tag] = _finite(s.get("infamy", "0"), f"{tag}.infamy")
    counts: dict = {}
    for f in re.findall(r"\bflag=([A-Za-z0-9_]+)", top_block(text, "variables")):
        counts[f] = counts.get(f, 0) + 1
    return SaveInfo(scal["game_date"], flags, countries, counts)

MAX_TOLERANCE = 0.5   # whole-number tables: anything larger could hide a wrong whole number

def check_save(info: SaveInfo, tables: dict, rule_key: str, tolerance: float) -> list:
    problems = []
    if not (math.isfinite(tolerance) and 0.0 <= tolerance < MAX_TOLERANCE):
        return [f"tolerance {tolerance!r} is not a finite value in [0, {MAX_TOLERANCE})"]
    if info.game_date != "1836.1.1":
        problems.append(f"game date is {info.game_date}, expected 1836.1.1")
    expected_flag = K.RULE_FLAGS.get(rule_key)
    infamy_flags = {f for f in info.rule_flags if f.startswith("infamy_generation_")}
    if expected_flag is None and infamy_flags:
        problems.append(f"rule mismatch: save has {sorted(infamy_flags)} but table is standard")
    if expected_flag is not None and infamy_flags != {expected_flag}:
        problems.append(f"rule mismatch: save has {sorted(infamy_flags)}, expected {expected_flag}")
    n = info.global_flag_counts.get("hsi_applied", 0)
    if n != 1:
        problems.append("global variable hsi_applied is absent" if n == 0 else f"global variable hsi_applied appears {n} times (applied more than once)")
    table = tables[rule_key]
    for tag, want in sorted(table.items()):
        if not (isinstance(want, (int, float)) and math.isfinite(want) and want > 0):
            problems.append(f"table entry {tag}={want!r} is not a positive finite number"); continue
        if tag not in info.countries:
            problems.append(f"expected positive record for {tag} is missing")
            continue
        got = info.countries[tag]
        if got <= 0.0:
            problems.append(f"{tag}: expected positive {want}, save has {got} (not positive)")
        elif abs(got - want) > tolerance:
            problems.append(f"{tag}: save has {got}, table says {want} (tolerance {tolerance})")
    if "BOL" not in info.countries:
        problems.append("BOL record missing (vanilla's 50 cannot be confirmed)")
    for tag, got in sorted(info.countries.items()):
        if tag == "BOL":
            if abs(got - 50.0) > tolerance:
                problems.append(f"BOL: expected vanilla 50, save has {got}")
        elif tag not in table and got != 0.0:
            problems.append(f"{tag}: unexpected infamy {got}, not in the {rule_key} table")
    return problems

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True); ap.add_argument("--tables", required=True)
    ap.add_argument("--rule", required=True, choices=sorted(K.RULE_MULT)); ap.add_argument("--tolerance", type=float, default=0.005)
    a = ap.parse_args(argv)
    try:
        info = parse_save(Path(a.save))
    except SaveParseError as e:
        print(f"PARSE ERROR: {e}", file=sys.stderr); return 2
    problems = check_save(info, json.loads(Path(a.tables).read_text()), a.rule, a.tolerance)
    for p in problems:
        print(p, file=sys.stderr)
    print("savecheck: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    return 0 if not problems else 1

if __name__ == "__main__":
    raise SystemExit(main())

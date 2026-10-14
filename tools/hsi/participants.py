# tools/hsi/participants.py
"""What one probe boot observes, derived from the ledger and the probe config in exactly one place, so the
renderer (probe_gen) and the receipt (measurement.expected_receipt) can never disagree."""

def fixture_slices(config: dict) -> list:
    return sorted({(sk, owner) for sk, owner in config.get("fixture_slices", [])})

def probe_slices(led, config: dict) -> list:
    """STATE records: every ledger slice and every capture-plan target slice."""
    return sorted(set(led.all_slices()) | set(fixture_slices(config)))

def probe_tags(led, config: dict) -> list:
    """COUNTRY records: ledger holders and victims (their 1836 ranks scale every charge), the fixture holder, the
    owners of the fixture slices (the captures' targets), BOL and the sampler."""
    tags = set(led.holder_tags()) | {config["fixture_holder"], "BOL", config["sampler_tag"]}
    tags |= {g.victim_tag_1836 for g in led.goals.values() if g.victim_tag_1836}
    tags |= {owner for _, owner in fixture_slices(config)}
    return sorted(tags)

def guard_tags(led, config: dict) -> list:
    """Countries whose monthly pulse runs the probe: every ledger holder, the fixture holder, BOL, the sampler."""
    return sorted(set(led.holder_tags()) | {config["fixture_holder"], "BOL", config["sampler_tag"]})

def diag_pairs(led, config: dict) -> dict:
    """holder -> sorted slices it evaluates: ledger holders over ledger slices; the fixture holder also over the
    fixture slices."""
    holders = set(led.holder_tags()); fh = config["fixture_holder"]
    out = {}
    for h in sorted(holders | {fh}):
        s = (set(led.all_slices()) if h in holders else set()) | (set(fixture_slices(config)) if h == fh else set())
        if s:
            out[h] = sorted(s)
    return out

#!/usr/bin/env python3
import json
from pathlib import Path

# Tier hierarchy from weakest to strongest (lowest tier first)
TIERS_ORDERED = ["LC", "ZU", "PU", "NU", "UU", "OU", "Uber"]

# Original tier groupings
ACTUAL_TIER_GROUPS = [
    "LC",
    ["NFE", "ZU"],
    "PU",
    "NU",
    ["RU", "UU"],
    "OU",
]

INPUT_PATH = Path("data/learnsets.json")
OUTPUT_DIR = Path("data/learnsets_by_tier")

# Define banned moves per tier (lowercase, no spaces)
BANNED_MOVES_BY_TIER = {
    "Uber": {"doubleteam", "minimize", "fly", "dig", "fissure", "guillotine", "horndrill"},
    "OU": set(),
    "UU": {"bind", "clamp", "confuseray", "firespin", "supersonic", "wrap"},
    "NU": set(),
    "PU": set(),
    "ZU": set(),
    "LC": {"dragonrage", "firespin", "sonicboom", "wrap", 
           "doubleteam", "minimize", "fly", "dig", "fissure", "guillotine", "horndrill"},
}

# -------------------------
# Tier normalization logic
# -------------------------

def build_tier_normalizer(groups):
    """
    Build a mapping from raw tier -> normalized tier.
    """
    mapping = {}
    for entry in groups:
        if isinstance(entry, list):
            canonical = entry[-1]
            for tier in entry:
                mapping[tier] = canonical
        else:
            mapping[entry] = entry
    return mapping

TIER_NORMALIZER = build_tier_normalizer(ACTUAL_TIER_GROUPS)

def normalize_tier(tier):
    return TIER_NORMALIZER.get(tier, tier)

# -------------------------
# Ban inheritance logic
# -------------------------

def get_cumulative_bans():
    """
    Compute cumulative banned moves per tier.
    LC does NOT inherit bans from higher tiers.
    """
    cumulative = {}

    for tier in TIERS_ORDERED:
        if tier == "LC":
            cumulative[tier] = set(BANNED_MOVES_BY_TIER.get("LC", set()))
            continue

        tier_idx = TIERS_ORDERED.index(tier)
        higher_tiers = TIERS_ORDERED[tier_idx:]
        bans = set()
        for ht in higher_tiers:
            bans |= BANNED_MOVES_BY_TIER.get(ht, set())
        cumulative[tier] = bans

    return cumulative

CUMULATIVE_BANS = get_cumulative_bans()

# -------------------------
# Core helpers
# -------------------------

def load_learnsets(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def tier_index(tier):
    try:
        return TIERS_ORDERED.index(tier)
    except ValueError:
        return None

def filter_moves(learned_moves, banned_moves_set):
    return [
        move for move in learned_moves
        if move["move_name"].replace(" ", "").lower() not in banned_moves_set
    ]

def filter_pokemon_for_tier(all_learnsets, tier):
    tier_idx = tier_index(tier)
    if tier_idx is None:
        print(f"Warning: Unknown tier '{tier}'")
        return {}

    allowed_tiers = set(TIERS_ORDERED[:tier_idx + 1])
    banned_moves = CUMULATIVE_BANS.get(tier, set())

    filtered = {}

    for pid, data in all_learnsets.items():
        raw_tier = data.get("tier")
        if not raw_tier:
            continue

        normalized = normalize_tier(raw_tier)
        if normalized not in allowed_tiers:
            continue

        filtered_learned = filter_moves(data.get("learned", []), banned_moves)
        filtered[pid] = {
            **data,
            "tier": normalized,
            "learned": filtered_learned,
        }

    return filtered

# -------------------------
# Main
# -------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_learnsets = load_learnsets(INPUT_PATH)

    for tier in TIERS_ORDERED:
        filtered = filter_pokemon_for_tier(all_learnsets, tier)

        out_path = OUTPUT_DIR / f"learnsets_{tier.lower()}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(filtered, f, indent=2)

        print(f"Wrote {len(filtered)} Pokémon learnsets for tier {tier} to {out_path}")

if __name__ == "__main__":
    main()

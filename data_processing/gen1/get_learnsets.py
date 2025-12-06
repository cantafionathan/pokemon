#!/usr/bin/env python3
import json
import csv
import requests
from pathlib import Path

FORTELLE_URLS = [
    "https://raw.githubusercontent.com/Fortelle/pokemon-learnsets/master/dist/redgreen.json",
    "https://raw.githubusercontent.com/Fortelle/pokemon-learnsets/master/dist/yellow.json",
]

POKEDEX_PATH = Path("data/gen1/pokedex.csv")
MOVELIST_PATH = Path("data/gen1/movelist.csv")
OUTPUT_PATH = Path("data/gen1/learnsets.json")


# ----------------------------------------------------
# Load pokedex + movelist
# ----------------------------------------------------

def load_pokedex():
    pokedex = {}
    with open(POKEDEX_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pokedex[int(row["id"])] = row["name"]
    return pokedex


def load_movelist():
    moves = {}
    with open(MOVELIST_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            moves[int(row["id"])] = row["name"]
    return moves


# ----------------------------------------------------
# Load Fortelle learnsets (source of truth)
# ----------------------------------------------------

def load_fortelle_learnsets():
    print("Fetching Fortelle learnsets...")

    all_entries = []

    for url in FORTELLE_URLS:
        data = requests.get(url).json()
        all_entries.extend(data)

    # prefer Red/Green entries over Yellow
    by_id = {}
    for entry in all_entries:
        pid = int(entry["pokemon"])
        if pid not in by_id:
            by_id[pid] = entry

    return by_id


# ----------------------------------------------------
# Parse Fortelle evolution inheritance
# ----------------------------------------------------

def build_final_learnsets(pokedex, movelist, fortelle_by_id):
    print("Building final learnsets…")

    output = {}

    for pid, name in pokedex.items():

        if pid not in fortelle_by_id:
            print(f"Warning: {name} has no Fortelle entry")
            output[pid] = {"name": name, "learned": []}
            continue

        entry = fortelle_by_id[pid]

        natural_moves = []
        inherited_moves = []

        for m in entry["moves"]:
            mid = int(m["move"])

            # inherited move from lower evolution?
            if "pokemon" in m and int(m["pokemon"]) != pid:
                inherited_moves.append({
                    "move": mid,
                    "method": "evolution",   # rewrite to evolution
                    "level": None
                })
            else:
                natural_moves.append({
                    "move": mid,
                    "method": m["method"],
                    "level": m.get("level")
                })

        # Deduplicate: if natural learn exists, drop inherited versions
        natural_ids = {m["move"] for m in natural_moves}
        inherited_filtered = [
            m for m in inherited_moves
            if m["move"] not in natural_ids
        ]

        combined = natural_moves + inherited_filtered

        # Final dedupe by (move, method, level)
        seen = set()
        final = []
        for m in combined:
            key = (m["move"], m["method"], m["level"])
            if key not in seen:
                seen.add(key)
                final.append(m)

        # format + attach move names
        formatted = []
        for m in final:
            mid = m["move"]
            formatted.append({
                "move_id": mid,
                "move_name": movelist.get(mid, f"Move{mid}"),
                "method": m["method"],
                "level": m["level"]
            })

        # sort: levelup first, by level
        formatted.sort(key=lambda x: (
            0 if x["method"] == "levelup" else 1,
            x["level"] if x["level"] is not None else 999
        ))

        output[pid] = {
            "name": name,
            "learned": formatted
        }

    return output


# ----------------------------------------------------
# Main
# ----------------------------------------------------

def main():
    pokedex = load_pokedex()
    movelist = load_movelist()
    fortelle = load_fortelle_learnsets()

    learnsets = build_final_learnsets(pokedex, movelist, fortelle)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(learnsets, f, indent=2)

    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

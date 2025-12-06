# data_processing/gen1/get_pokedex.py

import re
import csv
import requests

BASE_URL = "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/pokedex.ts"
GEN1_URL = "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen1/pokedex.ts"


def fetch(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text


def parse_base_pokedex(text):
    """Extract num, name, types from the main pokedex.ts"""
    entries = {}

    # Regex for entries like:
    # bulbasaur: {
    #     num: 1,
    #     name: "Bulbasaur",
    #     types: ["Grass", "Poison"],
    pattern = re.compile(
        r'(\w+)\s*:\s*\{[^}]*?num:\s*(\d+),[^}]*?name:\s*"([^"]+)"[^}]*?types:\s*\[\s*"(\w+)"\s*(?:,\s*"(\w+)")?',
        re.DOTALL
    )

    for match in pattern.finditer(text):
        key, num, name, t1, t2 = match.groups()
        entries[key] = {
            "id": int(num),
            "name": name,
            "type1": t1.lower(),
            "type2": t2.lower() if t2 else "",
        }

    return entries


def parse_gen1_overrides(text):
    """Extract baseStats overrides from mods/gen1/pokedex.ts"""
    stats = {}

    # Example:
    # bulbasaur: {
    #     inherit: true,
    #     baseStats: { hp: 45, atk: 49, def: 49, spa: 65, spd: 65, spe: 45 },
    # },

    pattern = re.compile(
        r'(\w+)\s*:\s*\{[^}]*?baseStats:\s*\{\s*hp:\s*(\d+),\s*atk:\s*(\d+),\s*def:\s*(\d+),\s*spa:\s*(\d+),\s*spd:\s*(\d+),\s*spe:\s*(\d+)',
        re.DOTALL
    )

    for match in pattern.finditer(text):
        key, hp, atk, deff, spa, spd, spe = match.groups()
        stats[key] = {
            "HP": int(hp),
            "ATK": int(atk),
            "DEF": int(deff),
            "SPC": int(spa),   # Gen 1 Special is combined
            "SPE": int(spe),
        }

    return stats


def save_csv(all_entries, path="data/gen1/pokedex.csv"):
    fields = ["id", "name", "type1", "type2", "HP", "ATK", "DEF", "SPC", "SPE"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for e in sorted(all_entries, key=lambda x: x["id"]):
            writer.writerow(e)

    print("Wrote", len(all_entries), "entries to", path)


def main():
    base_text = fetch(BASE_URL)
    gen1_text = fetch(GEN1_URL)

    base = parse_base_pokedex(base_text)
    overrides = parse_gen1_overrides(gen1_text)

    rows = []

    for key, base_entry in base.items():
        if key not in overrides:
            continue  # only include Gen 1 Pokémon

        # Skip MissingNo
        if base_entry["id"] == 0 or base_entry["name"].lower() == "missingno":
            continue

        stats = overrides[key]

        row = {
            **base_entry,
            **stats
        }
        rows.append(row)

    save_csv(rows)


if __name__ == "__main__":
    main()

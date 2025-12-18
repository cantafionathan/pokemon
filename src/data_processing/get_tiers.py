import re
import json
import requests

BASE_URL = "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/pokedex.ts"
FORMATS_URL = "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen1/formats-data.ts"

def normalize_name(name: str) -> str:
    """
    Normalize Pokémon names for downstream use.
    - Remove apostrophes (ASCII and Unicode)
    """
    return (
        name
        .replace("\\u2019", "")  # right single quotation mark
        .replace("'", "")       # ASCII apostrophe, just in case
    )


def fetch(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text

def parse_base_pokedex(text):
    """Extract num, name from the main pokedex.ts"""
    entries = {}

    pattern = re.compile(
        r'(\w+)\s*:\s*\{[^}]*?num:\s*(\d+),[^}]*?name:\s*"([^"]+)"',
        re.DOTALL
    )

    for match in pattern.finditer(text):
        key, num, name = match.groups()
        entries[key] = {
            "id": int(num),
            "name": name,
        }

    return entries

def parse_formats(text):
    """Extract tier info from formats-data.ts"""
    tiers = {}

    pattern = re.compile(
        r'(\w+)\s*:\s*\{\s*tier:\s*"([^"]+)"',
        re.DOTALL
    )

    for match in pattern.finditer(text):
        key, tier = match.groups()
        tiers[key] = tier

    return tiers

def save_json(entries, path="data/pokemon_tiers.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(entries)} entries to {path}")

def main():
    base_text = fetch(BASE_URL)
    formats_text = fetch(FORMATS_URL)

    base = parse_base_pokedex(base_text)
    tiers = parse_formats(formats_text)

    rows = []

    for key, tier in tiers.items():
        # Skip if missing in base pokedex or if MissingNo or id=0
        if key not in base:
            continue
        if base[key]["id"] == 0 or base[key]["name"].lower() == "missingno":
            continue

        rows.append({
            "id": base[key]["id"],
            "name": normalize_name(base[key]["name"]),
            "tier": tier
        })

    rows.sort(key=lambda x: x["id"])

    save_json(rows)

if __name__ == "__main__":
    main()

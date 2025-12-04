# data_processing/gen1/get_pokedex.py
import json
import requests
from pathlib import Path
from data_processing.common.paths import data_dir

# Fixes for PokeAPI names → preferred names
RENAME_MAP = {
    "Mr Mime": "Mr. Mime",
    "Nidoran M": "Nidoran-M",
    "Nidoran F": "Nidoran-F",
    "Farfetchd": "Farfetch'd",
}

def normalize_name(raw: str) -> str:
    # PokeAPI names often use hyphens; normalize capitalization and common exceptions
    name = raw.replace("-", " ").title()
    return RENAME_MAP.get(name, name)

def fetch_gen_pokedex(gen: int = 1):
    """
    Fetch the Pokédex for the given generation.
    For Gen1, the Kanto Pokédex has id=2 on PokeAPI.
    Returns a dict mapping dex number (str) -> canonical name.
    """
    if gen == 1:
        url = "https://pokeapi.co/api/v2/pokedex/2/"
    else:
        # Generic fallback: use generation endpoint to collect species and sort
        # (this will return species not necessarily dex-ordered)
        url = f"https://pokeapi.co/api/v2/generation/{gen}/"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    pokedex = {}

    if gen == 1:
        entries = data["pokemon_entries"]
        for entry in entries:
            dex_num = entry["entry_number"]
            raw = entry["pokemon_species"]["name"]
            pokedex[str(dex_num)] = normalize_name(raw)
    else:
        # For other gens, produce a simple index: 1..N
        species = [s["name"] for s in data.get("pokemon_species", [])]
        for i, s in enumerate(species, start=1):
            pokedex[str(i)] = normalize_name(s)

    return pokedex

def main(gen:int=1, out_path: str=None):
    out_dir = data_dir(gen)
    out_dir.mkdir(parents=True, exist_ok=True)

    if out_path is None:
        out_path = out_dir / "pokedex.json"
    else:
        out_path = Path(out_path)

    pokedex = fetch_gen_pokedex(gen)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pokedex, f, indent=2, ensure_ascii=False)

    print(f"Saved Gen {gen} Pokédex to {out_path}")
    return out_path

if __name__ == "__main__":
    main(gen=1)

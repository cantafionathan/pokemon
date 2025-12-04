import os
import json
import requests


# Fixes for PokeAPI names → your preferred names
RENAME_MAP = {
    "Mr Mime": "Mr. Mime",
    "Nidoran M": "Nidoran-M",
    "Nidoran F": "Nidoran-F",
    "Farfetchd": "Farfetch'd",
}


def normalize_name(name: str) -> str:
    """
    Convert PokeAPI species names to your preferred format using RENAME_MAP.
    Handles capitalization & spacing weirdness from PokeAPI.
    """
    # Capitalize words (pokeapi gives lower-case)
    name = name.replace("-", " ").title().replace(" ", " ")

    # Apply custom renames if matched
    return RENAME_MAP.get(name, name)


def fetch_gen1_pokedex():
    """
    Fetch the Gen 1 Pokédex (1–151) using the Kanto Pokédex endpoint.
    Returns {"1": "Bulbasaur", ..., "151": "Mew"}.
    """

    url = "https://pokeapi.co/api/v2/pokedex/2/"
    resp = requests.get(url)
    resp.raise_for_status()

    data = resp.json()
    entries = data["pokemon_entries"]

    pokedex = {}

    for entry in entries:
        dex_num = entry["entry_number"]
        raw = entry["pokemon_species"]["name"]  # e.g. "mr-mime", "nidoran-m"
        cleaned = normalize_name(raw)

        pokedex[str(dex_num)] = cleaned

    return pokedex


def main(out_path=None):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(root_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    if out_path is None:
        out_path = os.path.join(data_dir, "gen1_pokedex.json")

    pokedex = fetch_gen1_pokedex()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pokedex, f, indent=2, ensure_ascii=False)

    print(f"Saved Gen 1 Pokédex to {out_path}")


if __name__ == "__main__":
    main()

# scrape_moves.py

import requests
import json
from pathlib import Path
from tqdm import tqdm

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MOVE_VOCAB_PATH = DATA_DIR / "move_vocab.json"
VALID_MOVES_PATH = DATA_DIR / "valid_moves.json"

POKEAPI_BASE = "https://pokeapi.co/api/v2"

OU_BANNED_MOVES = {
    "Fissure",
    "Horn Drill",
    "Guillotine",
    "Double Team",
    "Minimize",
    "Dig",
    "Fly",
}

def get_gen1_moves():
    """Return a list of all moves introduced in Generation 1."""
    gen1 = requests.get(f"{POKEAPI_BASE}/generation/1/").json()
    moves = [m["name"].replace("-", " ").title() for m in gen1["moves"]]
    return sorted(moves)


def get_gen1_pokemon():
    """Return a list of all Pokémon introduced in Generation 1."""
    gen1 = requests.get(f"{POKEAPI_BASE}/generation/1/").json()
    pokemons = [p["name"].replace("-", " ").title() for p in gen1["pokemon_species"]]
    return sorted(pokemons)


def get_valid_moves_for_pokemon(name, gen1_move_vocab):
    """Return all moves a Pokémon can learn *in Generation 1*."""
    url_name = name.lower().replace(" ", "-").replace("♀", "-f").replace("♂", "-m")
    resp = requests.get(f"{POKEAPI_BASE}/pokemon/{url_name}")
    if resp.status_code != 200:
        return []

    data = resp.json()
    valid = []

    for m in data["moves"]:
        move_name = m["move"]["name"].replace("-", " ").title()

        # Skip moves not introduced in Gen1
        if move_name not in gen1_move_vocab:
            continue

        # Check if learned in Gen1 version groups
        for detail in m["version_group_details"]:
            vg = detail["version_group"]["name"]
            if vg in ("red-blue", "yellow"):
                valid.append(move_name)
                break

    return sorted(set(m for m in valid if m not in OU_BANNED_MOVES))


def main():
    print("Fetching Generation 1 move vocabulary...")
    move_vocab = get_gen1_moves()
    MOVE_VOCAB_PATH.write_text(json.dumps(move_vocab, indent=2))
    print(f"Saved {len(move_vocab)} moves to {MOVE_VOCAB_PATH}")

    print("Fetching Generation 1 Pokémon...")
    pokemons = get_gen1_pokemon()

    print(f"Found {len(pokemons)} Pokémon")

    print("Collecting valid moves for each Pokémon...")
    valid_moves = {}
    for name in tqdm(pokemons):
        valid_moves[name] = get_valid_moves_for_pokemon(name, set(move_vocab))

    # Rename specific Pokémon keys for presentation
    rename_map = {
        "Mr Mime": "Mr. Mime",
        "Nidoran M": "Nidoran-M",
        "Nidoran F": "Nidoran-F",
    }

    for old_name, new_name in rename_map.items():
        if old_name in valid_moves:
            valid_moves[new_name] = valid_moves.pop(old_name)

    VALID_MOVES_PATH.write_text(json.dumps(valid_moves, indent=2))
    print(f"Saved valid moves for {len(valid_moves)} Pokémon to {VALID_MOVES_PATH}")



if __name__ == "__main__":
    main()

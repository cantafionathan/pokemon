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

FORMATS = {
    "ubers": {
        "banned_pokemon": set(),  # none banned in Ubers
        "banned_moves": {
            "Fissure",
            "Horn Drill",
            "Guillotine",
            "Double Team",
            "Minimize",
            "Dig",
            "Fly",
            "Bide",
        },  
    },
    "ou": {
        "banned_pokemon": {
            "Mewtwo",
            "Mew",
        },
        "banned_moves": {
            "Fissure",
            "Horn Drill",
            "Guillotine",
            "Double Team",
            "Minimize",
            "Dig",
            "Fly",
            "Bide",
        },
    },
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

    return sorted(set(valid))

def get_evolution_chain(name):
    """Return a list of Pokémon names in its evolution chain, in order."""
    # Convert name to API species slug
    species_name = name.lower().replace(" ", "-").replace("♀", "-f").replace("♂", "-m")
    species = requests.get(f"{POKEAPI_BASE}/pokemon-species/{species_name}").json()
    
    chain_url = species["evolution_chain"]["url"]
    chain = requests.get(chain_url).json()["chain"]

    evo_list = []

    def traverse(node):
        evo_list.append(node["species"]["name"].replace("-", " ").title())
        for e in node["evolves_to"]:
            traverse(e)

    traverse(chain)
    return evo_list


def main():
    print("Fetching Generation 1 move vocabulary...")
    base_move_vocab = get_gen1_moves()

    print("Fetching Generation 1 Pokémon...")
    base_pokemons = get_gen1_pokemon()

    print(f"Found {len(base_pokemons)} Pokémon")

    # Cache evolution chains once (same for all formats)
    print("Building evolution chain cache...")
    evo_cache = {name: get_evolution_chain(name) for name in base_pokemons}

    #
    # ───────────────────────────────────────────────────────────────
    #   PROCESS EACH FORMAT SEPARATELY
    # ───────────────────────────────────────────────────────────────
    #
    for fmt, rules in FORMATS.items():
        fmt_dir = DATA_DIR / fmt
        fmt_dir.mkdir(parents=True, exist_ok=True)

        banned_moves = rules["banned_moves"]
        banned_pokemon = rules["banned_pokemon"]

        print(f"\n=== Processing format: {fmt.upper()} ===")

        # Apply move filter
        move_vocab = sorted([m for m in base_move_vocab if m not in banned_moves])

        # Save move vocab
        (fmt_dir / "move_vocab.json").write_text(json.dumps(move_vocab, indent=2))

        # Apply Pokémon filter
        pokemons = [p for p in base_pokemons if p not in banned_pokemon]

        print("Collecting valid moves for each Pokémon...")
        valid_moves = {}
        for name in tqdm(pokemons):
            moves = get_valid_moves_for_pokemon(name, set(move_vocab))
            valid_moves[name] = sorted(set(moves) - banned_moves)

        print("Applying evolution-based inheritance...")
        for chain in evo_cache.values():
            # Skip chains containing banned mons
            chain = [m for m in chain if m in valid_moves]
            inherited = set()
            for mon in chain:
                current = set(valid_moves.get(mon, []))
                valid_moves[mon] = sorted(current | inherited)
                inherited |= current

        # Name consistency fixes
        rename_map = {
            "Mr Mime": "Mr. Mime",
            "Nidoran M": "Nidoran-M",
            "Nidoran F": "Nidoran-F",
            "Farfetchd": "Farfetch'd",
        }

        for old, new in rename_map.items():
            if old in valid_moves:
                valid_moves[new] = valid_moves.pop(old)

        # Save final valid_moves.json
        (fmt_dir / "valid_moves.json").write_text(
            json.dumps(valid_moves, indent=2)
        )

        print(f"Saved {len(valid_moves)} Pokémon to {fmt_dir}/valid_moves.json")

    print("\nAll formats processed!")




if __name__ == "__main__":
    main()

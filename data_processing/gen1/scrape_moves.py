# data_processing/gen1/scrape_moves.py
"""
Scrape generation move vocabulary and valid per-mon moves (Gen-specific),
and write format-specific files to data/gen{gen}/{ou,ubers}/...
"""

import csv
import json
import requests
from pathlib import Path
from tqdm import tqdm
from data_processing.common.paths import data_dir

POKEAPI = "https://pokeapi.co/api/v2"

# Format rules (names mapped to output subfolders)
FORMATS = {
    "ou": {
        "banned_pokemon": {"Mewtwo", "Mew"},
        "banned_moves": {
            "Fissure", "Horn Drill", "Guillotine",
            "Double Team", "Minimize", "Bide",
        },
    },
    "ubers": {
        "banned_pokemon": set(),
        "banned_moves": {
            "Fissure", "Horn Drill", "Guillotine",
            "Double Team", "Minimize", "Bide",
        },
    },
}

def fetch_gen_moves(gen: int = 1):
    gen_url = f"{POKEAPI}/generation/{gen}/"
    resp = requests.get(gen_url)
    resp.raise_for_status()
    moves = [m["name"].replace("-", " ").title() for m in resp.json().get("moves", [])]
    return sorted(moves)

def fetch_gen_pokemon_list(gen: int = 1):
    gen_url = f"{POKEAPI}/generation/{gen}/"
    resp = requests.get(gen_url)
    resp.raise_for_status()
    mons = [p["name"].replace("-", " ").title() for p in resp.json().get("pokemon_species", [])]
    return sorted(mons)

def fetch_valid_moves_for_pokemon(name: str, gen_moves_set, gen:int=1):
    """
    Return moves that this pokemon can learn in the given generation
    by inspecting the /pokemon/<name> endpoint and filtering version groups.
    """
    slug = name.lower().replace(" ", "-").replace("♀", "-f").replace("♂", "-m")
    url = f"{POKEAPI}/pokemon/{slug}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []

    data = resp.json()
    valid = []
    for m in data.get("moves", []):
        mv = m["move"]["name"].replace("-", " ").title()
        if mv not in gen_moves_set:
            continue
        # check version groups for Gen1 games
        for detail in m.get("version_group_details", []):
            vg = detail["version_group"]["name"]
            if vg in ("red-blue", "yellow"):
                valid.append(mv)
                break
    return sorted(set(valid))

def build_evo_cache(pokemons):
    """
    Get evolution chains for each species and return a dict species -> chain list.
    If any species fetch fails, we ignore and continue.
    """
    evo_cache = {}
    for name in tqdm(pokemons, desc="evo cache"):
        slug = name.lower().replace(" ", "-").replace("♀", "-f").replace("♂", "-m")
        try:
            resp = requests.get(f"{POKEAPI}/pokemon-species/{slug}")
            resp.raise_for_status()
            species = resp.json()
            chain_url = species["evolution_chain"]["url"]
            chain_data = requests.get(chain_url).json()["chain"]
            chain = []
            def traverse(node):
                chain.append(node["species"]["name"].replace("-", " ").title())
                for e in node.get("evolves_to", []):
                    traverse(e)
            traverse(chain_data)
            evo_cache[name] = chain
        except Exception:
            # skip on any errors (network, missing data)
            continue
    return evo_cache

def main(gen:int=1):
    base_dir = data_dir(gen)
    base_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching generation {gen} move vocabulary and Pokémon list...")
    gen_moves = fetch_gen_moves(gen)
    gen_moves_set = set(gen_moves)
    mons = fetch_gen_pokemon_list(gen)

    # Precompute evo cache to perform inheritance (so pre-evolutions learn shared moves)
    print("Building evolution chain cache (this may take a while)...")
    evo_cache = build_evo_cache(mons)

    # For each target format, filter and save format-specific JSONs
    for fmt_name, rules in FORMATS.items():
        fmt_dir = base_dir / fmt_name
        fmt_dir.mkdir(parents=True, exist_ok=True)

        banned_moves = rules["banned_moves"]
        banned_pokemon = rules["banned_pokemon"]

        # filtered move vocab
        move_vocab = sorted([m for m in gen_moves if m not in banned_moves])
        (fmt_dir / "move_vocab.json").write_text(json.dumps(move_vocab, indent=2))
        print(f"Saved move_vocab to {fmt_dir / 'move_vocab.json'}")

        # valid moves per mon (filtered)
        valid_moves = {}
        for mon in tqdm(mons, desc=f"valid moves ({fmt_name})"):
            if mon in banned_pokemon:
                continue
            moves = fetch_valid_moves_for_pokemon(mon, set(move_vocab), gen=gen)
            valid_moves[mon] = sorted(set(moves) - banned_moves)

        # evolution-based inheritance
        for chain in evo_cache.values():
            # filter to mons we have in valid_moves
            available_chain = [m for m in chain if m in valid_moves]
            inherited = set()
            for mon in available_chain:
                current = set(valid_moves.get(mon, []))
                valid_moves[mon] = sorted(current | inherited)
                inherited |= current

        # name normalization map
        rename_map = {
            "Mr Mime": "Mr. Mime",
            "Nidoran M": "Nidoran-M",
            "Nidoran F": "Nidoran-F",
            "Farfetchd": "Farfetch'd",
        }
        for old, new in rename_map.items():
            if old in valid_moves:
                valid_moves[new] = valid_moves.pop(old)

        (fmt_dir / "valid_moves.json").write_text(json.dumps(valid_moves, indent=2))
        print(f"Saved valid_moves to {fmt_dir / 'valid_moves.json'} (count={len(valid_moves)})")

    print("All formats processed.")
    return base_dir

if __name__ == "__main__":
    main(gen=1)

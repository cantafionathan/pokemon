import csv
import json
from pathlib import Path
from io import StringIO
from data_processing.get_unrestricted_learnsets import MOVE_LIST as MOVELIST_CSV

def normalize_name(name: str) -> str:
    """
    Normalize Pokémon move / species names to canonical forms.

    Add new rules to NORMALIZATION_MAP as needed.
    """
    NORMALIZATION_MAP = {
        "Vice Grip": "Vise Grip",
        "Hi Jump Kick": "High Jump Kick",
    }

    return NORMALIZATION_MAP.get(name, name)


def parse_movelist(csv_text):
    movelist = {}
    f = StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    for row in reader:
        move_id = int(row["id"])
        move_name = row["move"]
        movelist[move_id] = normalize_name(move_name)
    return movelist

MOVELIST = parse_movelist(MOVELIST_CSV)

POKEDEX_PATH = Path("data/pokemon_tiers.json")

def load_pokedex_from_tiers(path=POKEDEX_PATH):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Build dict: id -> name
    pokedex = {entry["id"]: entry["name"] for entry in data}
    return pokedex

POKEDEX = load_pokedex_from_tiers()

def build_team_summary(pokemon_ids, moves_ids_per_pokemon):
    """
    Builds a compact, single-line-per-Pokémon summary of the team.

    Format example:
    P1: [Move1, Move2, Move3, Move4]
    P2: [Move1, Move2, Move3, Move4]

    Args:
        pokemon_ids: List of Pokémon IDs (ints)
        moves_ids_per_pokemon: List of list of move IDs per Pokémon

    Returns:
        str: The compact formatted team summary
    """
    lines = []
    for idx, (pid, moves_ids) in enumerate(zip(pokemon_ids, moves_ids_per_pokemon), start=1):
        name = POKEDEX.get(pid, f"Pokemon{pid}")
        move_names = [MOVELIST.get(mid, f"Move{mid}") for mid in moves_ids]
        moves_str = ", ".join(move_names)
        lines.append(f"{name}: [{moves_str}]")
    return "\n".join(lines)

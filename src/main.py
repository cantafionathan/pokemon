from poke_env_engine.battle_simulator import battle_once, build_team_text
from config import get_format
import json
import random
from pathlib import Path


# ACTUAL CODE BEGINS HERE
######################################################################
######################################################################

######################################################################
######################################################################

def sample_random_team(learnsets_path: Path):
    with open(learnsets_path, encoding="utf-8") as f:
        learnsets = json.load(f)

    # Filter Pokémon that have at least 4 learned moves
    valid_pokemon = [
        pid for pid, pdata in learnsets.items()
        if len(pdata.get("learned", [])) >= 4
    ]
    if len(valid_pokemon) < 6:
        raise ValueError("Not enough Pokémon with 4+ moves to build a full team")

    chosen_pokemon = random.sample(valid_pokemon, 6)

    pokemon_ids = []
    moves_ids_per_pokemon = []

    for pid in chosen_pokemon:
        pdata = learnsets[pid]
        pokemon_ids.append(int(pid))  # convert string ID to int

        learned_moves = pdata.get("learned", [])

        # Randomly pick 4 unique moves (each is a dict with move_id, move_name)
        chosen_moves = random.sample(learned_moves, 4)

        moves_ids = [move["move_id"] for move in chosen_moves]
        moves_ids_per_pokemon.append(moves_ids)

    return (pokemon_ids, moves_ids_per_pokemon)


def main():
    tier = "OU"  # "Uber", "OU", "UU", "NU", "PU", "ZU", "LC"
    learnsets_file = Path(f"data/learnsets_by_tier/learnsets_{tier.lower()}.json")

    team1 = sample_random_team(learnsets_file)
    team2 = sample_random_team(learnsets_file)

    format = get_format(tier)  # Assuming your format strings follow this pattern
    print(f"{format}, ({tier})")

    result = battle_once(team1, team2, format)

    print(f"Battle result: Player {result} won")

if __name__ == "__main__":
    main()

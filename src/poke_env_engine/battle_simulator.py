import asyncio
import uuid
import json
import logging
import gc
from pathlib import Path
import csv
from io import StringIO

from data_processing.get_unrestricted_learnsets import MOVE_LIST as MOVELIST_CSV

from poke_env.player import SimpleHeuristicsPlayer as PLAYER_CLASS
from poke_env.ps_client.server_configuration import LocalhostServerConfiguration


POKEDEX_PATH = Path("data/pokemon_tiers.json")

def load_pokedex_from_tiers(path=POKEDEX_PATH):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Build dict: id -> name
    pokedex = {entry["id"]: entry["name"] for entry in data}
    return pokedex

POKEDEX = load_pokedex_from_tiers()

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


# ============================================================
# Helpers
# ============================================================

def build_team_text(pokemon_ids, moves_ids_per_pokemon):
    """Builds the team text with Ability: None and moves in correct format.

    Args:
        pokemon_ids: List of Pokémon IDs (ints)
        moves_ids_per_pokemon: List of list of move IDs per Pokémon

    Returns:
        str: The formatted team text
    """
    lines = []
    for pid, moves_ids in zip(pokemon_ids, moves_ids_per_pokemon):
        name = POKEDEX.get(pid, f"Pokemon{pid}")
        lines.append(name)
        lines.append("Ability: None")
        for mid in moves_ids:
            move_name = MOVELIST.get(mid, f"Move{mid}")
            lines.append(f"- {move_name}")
        lines.append("")  # blank line between Pokémon

    return "\n".join(lines)


async def battle_async(team1: str, team2: str, format: str) -> int:
    player1 = PLAYER_CLASS(
        battle_format=format,
        server_configuration=LocalhostServerConfiguration,
        team=team1,
        max_concurrent_battles=1,
    )
    player2 = PLAYER_CLASS(
        battle_format=format,
        server_configuration=LocalhostServerConfiguration,
        team=team2,
        max_concurrent_battles=1,
    )


    player1.logger.setLevel(logging.ERROR)
    player2.logger.setLevel(logging.ERROR)

    player1._username = f"p_{uuid.uuid4().hex[:6]}"
    player2._username = f"o_{uuid.uuid4().hex[:6]}"

    try:
        await asyncio.wait_for(player1.battle_against(player2, n_battles=1), timeout=60)
        winner = 1 if player1.n_won_battles > 0 else 2
    except asyncio.TimeoutError:
        logging.error("Battle timed out")
        winner = 0
    except Exception as e:
        logging.error(f"Unexpected error during battle: {e}")
        winner = 0
    finally:
        await player1.ps_client.stop_listening()
        await player2.ps_client.stop_listening()
        await asyncio.sleep(0.1)
        gc.collect()

    return winner



def battle_once(team1: tuple[list[int], list[list[int]]], 
                team2: tuple[list[int], list[list[int]]], 
                format: str) -> int:
    """Run one battle synchronously, returning 1/2/0 for player1 win/player2 win/draw."""
    team1_str = build_team_text(*team1)
    team2_str = build_team_text(*team2)
    return asyncio.run(battle_async(team1_str, team2_str, format))


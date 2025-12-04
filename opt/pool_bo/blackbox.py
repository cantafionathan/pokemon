# bo/objective.py
import torch
import logging
from battle_engine.battle_simulator import evaluate_team
from .encoding import decode_team_pokemon_only, random_legal_moves, format_team, parse_showdown_team

# ============================================================
# Black-box BO wrapper
# ============================================================

logger = logging.getLogger("bo.objective")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

def black_box_eval(x: torch.Tensor, n_battles_per_opponent: int = 1, n_moveset_samples: int = 5) -> float:
    """
    Decode embedding → team species
    Try n_moveset_samples random moveset assignments
    Evaluate each team and return the best score
    """

    pokemon_list = decode_team_pokemon_only(x)

    best_score = -1.0
    best_team_str = None

    for _ in range(n_moveset_samples):
        pokemon_moves = {
            p: random_legal_moves(p) for p in pokemon_list
        }

        team_str = format_team(pokemon_moves)

        score = evaluate_team(team_str, n_battles_per_opponent)

        if score > best_score:
            best_score = score
            best_team_str = team_str



    return best_score, best_team_str


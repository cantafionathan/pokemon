# bo/objective.py
import torch
from simulator.battle_simulator import evaluate_team
from .encoding import decode_team_from_embedding as decode

# ============================================================
# Black-box BO wrapper
# ============================================================

def black_box_eval(x: torch.Tensor, n_battles_per_opponent: int = 10) -> float:
    """
    Decode embedding → team string → real battle winrate.
    """
    team_dict = decode(x) # with random initialization gets stuck
    team_str = team_dict["team"]
    return evaluate_team(team_str, n_battles_per_opponent)

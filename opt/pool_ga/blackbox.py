from .encoding import load_flattened_pool, team_string_from_indices
from simulator.battle_simulator import evaluate_team
import typing as t

flattened = load_flattened_pool()

def black_box_eval(
    indices: t.List[int],
    n_battles_per_opponent: int = 1,
) -> t.Tuple[float, str]:
    """
    Given a GA individual (list of indices), construct the team string and
    evaluate it using the black-box evaluator.

    Returns:
        (score, team_string)
    """

    team_str = team_string_from_indices(flattened, indices)

    score = evaluate_team(team_str, n_battles_per_opponent=n_battles_per_opponent)

    return score, team_str
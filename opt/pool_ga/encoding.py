# pool_ga/encoding.py

import json
import os
from typing import List, Tuple, Dict

from config import DATA_DIR


# -----------------------------
# Load and flatten move pool
# -----------------------------

def load_flattened_pool(
    path: str = DATA_DIR() / "competitive_movesets.json"
) -> List[Tuple[str, List[str]]]:
    """
    Loads competitive movesets and returns a flattened pool:
        [(species, [moves]), ...]

    Example:
        "Bulbasaur": [ ["Sleep Powder", "Razor Leaf", ...], ... ]
    becomes:
        ("Bulbasaur", ["Sleep Powder", ...])
        ("Bulbasaur", ["Sleep Powder", ...])
        ...

    This is the global search space for the GA.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"Cannot find moveset file: {path}")

    with open(path, "r") as f:
        data = json.load(f)

    flattened = []
    for species, moveset_list in data.items():
        for moveset in moveset_list:
            flattened.append((species, moveset))

    return flattened


# -----------------------------
# Team string construction
# -----------------------------

def team_string_from_indices(
    flattened: List[Tuple[str, List[str]]],
    indices: List[int]
) -> str:
    """
    Convert GA individual (indices) → showdown team string.

    Each index refers into `flattened`.
    """

    blocks = []

    for idx in indices:
        species, moves = flattened[idx]

        move_lines = "\n".join(f"- {m}" for m in moves)

        block = (
            f"{species}\n"
            f"Ability: None\n"
            f"{move_lines}"
        )

        blocks.append(block)

    return "\n\n".join(blocks)

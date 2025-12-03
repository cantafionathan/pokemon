# opt/random/optimizer.py

import json
import os
import random
import numpy as np

from opt.ga.blackbox import black_box_eval
from config import DATA_DIR

MOVES_PATH = DATA_DIR() / "competitive_movesets.json"


class RandomSearchOptimizer:
    """
    Simple random search over Pokémon teams.
    Each 'team' is 6 builds (species + moveset) chosen randomly,
    without duplicate species.

    Returns:
        run_random_search(...) -> (best_team_indices, best_score, best_team_repr)
    """

    def __init__(
        self,
        n_samples: int = 500,
        seed: int | None = 0,
        moves_path: str | None = None,
    ):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.n_samples = int(n_samples)
        self.moves_path = moves_path or MOVES_PATH

        self._load_movesets()
        if len(self.flattened) == 0:
            raise RuntimeError(f"No builds found in {self.moves_path}")

    # ---------------------
    # Load move pool
    # ---------------------
    def _load_movesets(self):
        with open(self.moves_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        self.flattened = []
        self.species_to_indices = {}
        for species, movelists in data.items():
            for moveset in movelists:
                idx = len(self.flattened)
                self.flattened.append((species, moveset))
                self.species_to_indices.setdefault(species, []).append(idx)

        self.pool_size = len(self.flattened)

    def index_to_build(self, idx: int):
        s, m = self.flattened[idx]
        return {"species": s, "moveset": m}

    def team_indices_to_repr(self, team):
        return [self.index_to_build(i) for i in team]

    # ---------------------
    # Team generator
    # ---------------------
    def random_team(self):
        """Sample 6 unique species, and pick 1 random build for each."""
        species_list = list(self.species_to_indices.keys())
        chosen_species = random.sample(species_list, 6)

        team = []
        for sp in chosen_species:
            team.append(random.choice(self.species_to_indices[sp]))
        return team

    # ---------------------
    # Main loop
    # ---------------------
    def run_random_search(
        self,
        n_battles_per_opponent: int = 1,
        verbose: bool = True,
        history_file: str | None = None
    ):
        """
        Perform random sampling of teams.

        Returns:
            (best_team_indices, best_score, best_team_repr)
        """

        history = []

        best_score = -float("inf")
        best_team = None

        for i in range(1, self.n_samples + 1):
            team = self.random_team()
            score, _ = black_box_eval(
                indices=team,
                n_battles_per_opponent=n_battles_per_opponent,
            )

            if score > best_score:
                best_score = score
                best_team = team[:]

            ### record history after each generation
            history.append({
                "iteration": i,
                "best_wr_so_far": best_score,
            })
            if history_file is not None:
                with open(history_file, "w") as f:
                    json.dump(history, f, indent=2)

            if verbose and (i % 10 == 0 or i == 1 or i == self.n_samples):
                print(f"[Random] {i}/{self.n_samples} | best={best_score:.4f}")

        return best_team, best_score, self.team_indices_to_repr(best_team)


# -------------------------
# Self-test
# -------------------------
if __name__ == "__main__":
    rs = RandomSearchOptimizer(n_samples=20, seed=0)
    best_team, best_score, best_repr = rs.run_random_search(n_battles_per_opponent=1)
    print("\n=== BEST TEAM (Random Search) ===")
    print("Score", best_score)
    for i, b in enumerate(best_repr, 1):
        print(f"{i}. {b['species']}: {b['moveset']}")

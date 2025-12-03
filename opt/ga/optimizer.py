# opt/ga/optimizer.py

import json
import os
import random
import numpy as np

from .blackbox import black_box_eval 

from config import DATA_DIR

# adjust path if needed; this assumes project root is current working dir when running main.py
MOVES_PATH = DATA_DIR() / "competitive_movesets.json"


class GAOptimizer:
    """
    Genetic Algorithm Optimization loop for Pokémon teams where each 'gene' is a
    (species, moveset) build drawn from data/competitive_movesets.json.

    Results:
        run_ga(...) -> (best_team_indices, best_score, best_team_repr)
    """

    def __init__(
        self,
        population_size: int = 50,
        mutation_rate: float = 0.12,
        seed: int | None = 0,
        moves_path: str | None = None,
    ):
        """
        Args:
            population_size: Number of teams in the GA population.
            mutation_rate: Per-gene mutation probability.
            seed: RNG seed (None -> no seeding).
            moves_path: optional override path to competitive_movesets.json
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.population_size = int(population_size)
        self.mutation_rate = float(mutation_rate)
        self.moves_path = moves_path or MOVES_PATH

        # load + flatten the pool
        self._load_movesets()
        if len(self.flattened) == 0:
            raise RuntimeError(f"No builds found in {self.moves_path}")

    # -------------------------
    # Data loading / utilities
    # -------------------------
    def _load_movesets(self):
        with open(self.moves_path, "r", encoding="utf-8") as fh:
            pool = json.load(fh)

        # pool expected as: { "Bulbasaur": [ ["M1","M2","M3","M4"], ... ], ... }
        self.flattened: list[tuple[str, list[str]]] = []
        self.species_to_indices: dict[str, list[int]] = {}
        for species, movelists in pool.items():
            for moveset in movelists:
                idx = len(self.flattened)
                self.flattened.append((species, moveset))
                self.species_to_indices.setdefault(species, []).append(idx)

        self.pool_size = len(self.flattened)

    def index_to_build(self, idx: int) -> dict:
        """Return a dict representation for an index."""
        species, moveset = self.flattened[idx]
        return {"species": species, "moveset": moveset}

    def team_indices_to_repr(self, team: list[int]) -> list[dict]:
        return [self.index_to_build(i) for i in team]

    # -------------------------
    # GA operators
    # -------------------------
    def fix_duplicates(self, team: list[int]) -> list[int]:
        """Replace duplicates in a team by random other builds."""
        new_team = team[:]
        species_in_team = set()
        for i, member_idx in enumerate(new_team):
            species = self.flattened[member_idx][0]
            if species in species_in_team:
                # Duplicate species found, replace it
                while True:
                    new_idx = random.randrange(self.pool_size)
                    new_species = self.flattened[new_idx][0]
                    if new_species not in species_in_team:
                        new_team[i] = new_idx
                        species_in_team.add(new_species)
                        break
            else:
                species_in_team.add(species)
        return new_team

    def random_team(self) -> list[int]:
        """Construct a random team as indices into flattened pool, avoiding duplicate species."""
        # This is equivalent to sampling 6 unique species, then one build per species
        species_names = list(self.species_to_indices.keys())
        chosen_species = random.sample(species_names, 6)
        
        team = []
        for species in chosen_species:
            build_idx = random.choice(self.species_to_indices[species])
            team.append(build_idx)
            
        return team

    def crossover(self, parent_a: list[int], parent_b: list[int]) -> list[int]:
        """Uniform crossover by slot; then fix duplicates."""
        child = []
        for i in range(6):
            if random.random() < 0.5:
                child.append(parent_a[i])
            else:
                child.append(parent_b[i])
        return self.fix_duplicates(child)

    def mutate(self, team: list[int]) -> list[int]:
        """Per-gene mutation. With probability mutation_rate, mutate each gene."""
        new_team = team[:]
        for i in range(6):
            if random.random() < self.mutation_rate:
                # Mutate by swapping for a different species
                current_species = {self.flattened[idx][0] for idx in new_team}
                while True:
                    new_idx = random.randrange(self.pool_size)
                    new_species = self.flattened[new_idx][0]
                    if new_species not in current_species:
                        new_team[i] = new_idx
                        break
        return new_team


    # -------------------------
    # GA main loop
    # -------------------------
    def run_ga(
    self,
    n_generations: int = 10,
    n_battles_per_opponent: int = 1,
    elite_frac: float = 0.2,
    verbose: bool = True,
    history_file: str | None = None
    ) -> tuple[list[int], float, list[dict]]:
        """
        Runs the Genetic Algorithm.

        Returns:
            (best_team_indices, best_score, best_team_repr)
        """
        history = []

        pop = [self.random_team() for _ in range(self.population_size)]
        best_team: list[int] | None = None
        best_score = -float("inf")

        elite_k = max(1, int(round(elite_frac * self.population_size)))

        for gen in range(1, n_generations + 1):
            # evaluate population
            scores = []
            for team in pop:
                score, _ = black_box_eval(
                    indices=team,
                    n_battles_per_opponent=n_battles_per_opponent,
                )
                scores.append(score)

            scores = np.asarray(scores, dtype=float)

            # update best
            gen_best_idx = int(np.argmax(scores))
            gen_best_score = float(scores[gen_best_idx])
            if gen_best_score > best_score:
                best_score = gen_best_score
                best_team = pop[gen_best_idx][:]  # copy

            # logging
            if verbose:
                mean = float(np.mean(scores))
                std = float(np.std(scores))
                print(f"[GA] Gen {gen}/{n_generations} | best={gen_best_score:.4f} mean={mean:.4f} std={std:.4f}")

            ### record history after each generation
            history.append({
                "generation": gen,
                "best_wr_so_far": best_score,
            })
            if history_file is not None:
                with open(history_file, "w") as f:
                    json.dump(history, f, indent=2)

            # selection: keep elites and produce rest by crossover and mutation
            elite_indices = np.argsort(scores)[-elite_k:]
            elites = [pop[i] for i in elite_indices.tolist()]

            new_pop = elites[:]  # carry elites over unchanged

            # fill rest of population
            while len(new_pop) < self.population_size:
                # parent selection: tournament selection among elites (or random elites if few)
                if len(elites) >= 2:
                    parent_a, parent_b = random.sample(elites, 2)
                else:
                    parent_a = random.choice(elites)
                    parent_b = self.random_team()

                child = self.crossover(parent_a, parent_b)
                child = self.mutate(child)
                new_pop.append(child)

            pop = new_pop

        if best_team is None:
            raise RuntimeError("GA failed to find a best team (this should not happen)")

        return best_team, best_score, self.team_indices_to_repr(best_team)



# -------------------------
# Example usage 
# -------------------------
if __name__ == "__main__":
    # quick self-test of GA optimizer
    ga = GAOptimizer(population_size=2, mutation_rate=0.12, seed=None)
    try:
        best_team, best_score, best_repr = ga.run_ga(n_generations=10, n_battles_per_opponent=1)
        print("\n=== BEST TEAM ===")
        print("Score", best_score)
        for i, b in enumerate(best_repr, 1):
            print(f"{i}. {b['species']}: {b['moveset']}")
    except Exception as e:
        print("GA run failed during evaluation. Error:", e)

# opt/optimizer.py

import json
from opt.pool_bo.optimizer import POOLBOOptimizer
from opt.pool_ga.optimizer import POOLGAOptimizer
from opt.pool_rs.optimizer import POOLRandomSearchOptimizer
from opt.pool_bo.encoding import parse_showdown_team
from config import DATA_DIR, set_format, get_format


class Optimizer:
    """
    Unified wrapper for all optimization methods:
    - Bayesian Optimization on pool of good movesets (pool_bo)
    - Genetic Algorithm on pool of good movesets (pool_ga)
    - Random Search on pool of good movesets (pool_rs)

    Usage:
        opt = Optimizer(method="pool_bo", B=7500, seed=0, format="ou")
        results = opt.run()
    """

    def __init__(self, method, B, seed=0, n_battles_per_opponent=1, format="ou"):
        set_format(format)

        OPP_PATH = DATA_DIR() / "opponent_teams.json"

        with open(OPP_PATH, "r", encoding="utf-8") as f:
            OPPONENTS = json.load(f)

        self.method = method.lower()
        self.B = B
        self.seed = seed
        self.n_battles_per_opponent = n_battles_per_opponent
        self.n_opponents = len(OPPONENTS)

        

        valid = {"pool_bo", "pool_ga", "pool_rs"}
        if self.method not in valid:
            raise ValueError(f"method must be one of {valid}")

    # --------------------------------------------------------
    # Unified run()
    # --------------------------------------------------------
    def run(self):
        if self.method == "pool_bo":
            return self._run_pool_bo()
        elif self.method == "pool_ga":
            return self._run_pool_ga()
        elif self.method == "pool_rs":
            return self._run_pool_rs()

    # --------------------------------------------------------
    # BO
    # --------------------------------------------------------
    def _run_pool_bo(self):
        opt = POOLBOOptimizer()

        n_init = 5
        n_moveset_samples = 1

        n_init_battles = (
            n_init
            * self.n_battles_per_opponent
            * n_moveset_samples
            * self.n_opponents
        )

        battles_per_iter = (
            self.n_battles_per_opponent
            * n_moveset_samples
            * self.n_opponents
        )

        n_iters = max(1, (self.B - n_init_battles) // battles_per_iter)

        print("=== Pool BO Schedule ===")
        print(f"Battle Budget: {self.B}")
        print(f"Init Number of Battles: {n_init_battles}")
        print(f"Battles per BO Step: {battles_per_iter}")
        print(f"BO Iterations: {n_iters}")
        print(f"Format: gen1{get_format()}")

        best_x, best_y, best_team_str = opt.run_pool_bo(
            n_iters=n_iters,
            n_init=n_init,
            n_battles_per_opponent=self.n_battles_per_opponent,
            n_moveset_samples=n_moveset_samples,
            seed=self.seed,
        )

        parsed = parse_showdown_team(best_team_str)
        self._print_best(parsed, best_y)
        return parsed, best_y

    # --------------------------------------------------------
    # GA
    # --------------------------------------------------------
    def _run_pool_ga(self):
        opt = POOLGAOptimizer(
            population_size=50,
            mutation_rate=0.12,
            seed=self.seed,
        )

        battles_per_eval = self.n_battles_per_opponent * self.n_opponents
        n_generations = max(1, self.B // (opt.population_size * battles_per_eval))

        print("=== Pool GA Schedule ===")
        print(f"Battle Budget: {self.B}")
        print(f"Population Size: {opt.population_size}")
        print(f"Battles per Team Evaluation: {battles_per_eval}")
        print(f"GA Generations: {n_generations}")
        print(f"Format: gen1{get_format()}")

        best_team_indices, best_score, best_repr = opt.run_pool_ga(
            n_generations=n_generations,
            n_battles_per_opponent=self.n_battles_per_opponent,
            verbose=True,
        )

        self._print_best(best_repr, best_score)
        return best_repr, best_score

    # --------------------------------------------------------
    # Random Search
    # --------------------------------------------------------
    def _run_pool_rs(self):
        battles_per_eval = self.n_battles_per_opponent * self.n_opponents
        n_samples = max(1, self.B // battles_per_eval)

        print("=== Pool Random Search Schedule ===")
        print(f"Battle Budget: {self.B}")
        print(f"Battles per Team Evaluation: {battles_per_eval}")
        print(f"Random Samples: {n_samples}")
        print(f"Format: gen1{get_format()}")

        opt = POOLRandomSearchOptimizer(
            n_samples=n_samples,
            seed=self.seed,
        )

        best_team_indices, best_score, best_repr = opt.run_pool_random_search(
            n_battles_per_opponent=self.n_battles_per_opponent,
            verbose=True,
        )

        self._print_best(best_repr, best_score)
        return best_repr, best_score

    # --------------------------------------------------------
    # Helper
    # --------------------------------------------------------
    def _print_best(self, team_repr, score):
        print("\n=== BEST TEAM ===")
        print(f"Score {score:.4f}")
        for i, b in enumerate(team_repr, 1):
            print(f"{i}. {b['species']}: {b['moveset']}")

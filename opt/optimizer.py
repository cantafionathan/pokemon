# opt/optimizer.py

from simulator.battle_simulator import OPPONENTS
from opt.bo.optimizer import BOOptimizer
from opt.ga.optimizer import GAOptimizer
from opt.rs.optimizer import RandomSearchOptimizer
from opt.bo.encoding import parse_showdown_team
from config import set_format, get_format


class Optimizer:
    """
    Unified wrapper for all optimization methods:
    - Bayesian Optimization (bo)
    - Genetic Algorithm (ga)
    - Random Search (rs)

    Usage:
        opt = Optimizer(method="ga", B=7500, seed=0)
        results = opt.run()
    """

    def __init__(self, method, B, seed=0, n_battles_per_opponent=1, format="ou"):
        self.method = method.lower()
        self.B = B
        self.seed = seed
        self.n_battles_per_opponent = n_battles_per_opponent
        self.n_opponents = len(OPPONENTS)

        set_format(format)

        valid = {"bo", "ga", "rs"}
        if self.method not in valid:
            raise ValueError(f"method must be one of {valid}")

    # --------------------------------------------------------
    # Unified run()
    # --------------------------------------------------------
    def run(self):
        if self.method == "bo":
            return self._run_bo()
        elif self.method == "ga":
            return self._run_ga()
        elif self.method == "rs":
            return self._run_rs()

    # --------------------------------------------------------
    # BO
    # --------------------------------------------------------
    def _run_bo(self):
        opt = BOOptimizer()

        n_init = 5
        n_moveset_samples = 5

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

        print("=== BO Schedule ===")
        print(f"Battle Budget: {self.B}")
        print(f"Init Number of Battles: {n_init_battles}")
        print(f"Battles per BO Step: {battles_per_iter}")
        print(f"BO Iterations: {n_iters}")
        print(f"Format: gen1{get_format()}")

        best_x, best_y, best_team_str = opt.run_bo(
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
    def _run_ga(self):
        opt = GAOptimizer(
            population_size=2,
            mutation_rate=0.12,
            seed=self.seed,
        )

        battles_per_eval = self.n_battles_per_opponent * self.n_opponents
        n_generations = max(1, self.B // (opt.population_size * battles_per_eval))

        print("=== GA Schedule ===")
        print(f"Battle Budget: {self.B}")
        print(f"Population Size: {opt.population_size}")
        print(f"Battles per Team Evaluation: {battles_per_eval}")
        print(f"GA Generations: {n_generations}")
        print(f"Format: gen1{get_format()}")

        best_team_indices, best_score, best_repr = opt.run_ga(
            n_generations=n_generations,
            n_battles_per_opponent=self.n_battles_per_opponent,
            verbose=True,
        )

        self._print_best(best_repr, best_score)
        return best_repr, best_score

    # --------------------------------------------------------
    # Random Search
    # --------------------------------------------------------
    def _run_rs(self):
        battles_per_eval = self.n_battles_per_opponent * self.n_opponents
        n_samples = max(1, self.B // battles_per_eval)

        print("=== Random Search Schedule ===")
        print(f"Battle Budget: {self.B}")
        print(f"Battles per Team Evaluation: {battles_per_eval}")
        print(f"Random Samples: {n_samples}")
        print(f"Format: gen1{get_format()}")

        opt = RandomSearchOptimizer(
            n_samples=n_samples,
            seed=self.seed,
        )

        best_team_indices, best_score, best_repr = opt.run_random_search(
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

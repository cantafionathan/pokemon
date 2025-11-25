# main.py

from opt.bo.optimizer import BOOptimizer
from opt.ga.optimizer import GAOptimizer
from opt.rs.optimizer import RandomSearchOptimizer
from simulator.battle_simulator import OPPONENTS
from opt.bo.encoding import parse_showdown_team



if __name__ == "__main__":
    B = 7500 # battle budget
    n_battles_per_opponent = 1
    seed = 0
    method = "ga"  # choose from "bo", "ga", "rs"

    # -----------------------------
    # Bayesian Optimization (BO)
    # -----------------------------

    if method == "bo":
        opt = BOOptimizer()

        # hyperparameters
        n_init = 5
        n_moveset_samples = 5
        n_opponents = len(OPPONENTS)

        n_init_battles = n_init * n_battles_per_opponent * n_moveset_samples * n_opponents
        n_iters = (B - n_init_battles) // (n_battles_per_opponent * n_moveset_samples * n_opponents)

        print("=== BO Schedule ===")
        print(f"Battle Budget: {B}")
        print(f"Init Number of Battles: {n_init_battles}")
        print(f"Battles per BO Step: {n_battles_per_opponent * n_moveset_samples * n_opponents}")
        print(f"BO Iterations: {n_iters}")

        best_x, best_y, best_team_str = opt.run_bo(n_iters=n_iters, 
                                                   n_init=n_init, 
                                                   n_battles_per_opponent=n_battles_per_opponent, 
                                                   n_moveset_samples=n_moveset_samples,
                                                   seed=seed)
        
        parsed_team = parse_showdown_team(best_team_str)
        print("\n=== BEST TEAM ===")
        print(f"Score {best_y:.4f}")
        for i, b in enumerate(parsed_team, 1):
            print(f"{i}. {b['species']}: {b['moveset']}")

    # -----------------------------
    # Genetic Algorithm (GA)
    # -----------------------------

    if method == "ga":
        ga = GAOptimizer(
            population_size=50,
            mutation_rate=0.12,
            seed=seed,
        )

        # number of GA generations based on battle budget
        n_opponents = len(OPPONENTS)
        battles_per_team_eval = n_battles_per_opponent * n_opponents

        # Number of generations given total budget
        n_generations = max(1, B // (ga.population_size * battles_per_team_eval))

        print("=== GA Schedule ===")
        print(f"Battle Budget: {B}")
        print(f"Population Size: {ga.population_size}")
        print(f"Battles per Team Evaluation: {battles_per_team_eval}")
        print(f"GA Generations: {n_generations}")

        best_team_indices, best_score, best_team_repr = ga.run_ga(
            n_generations=n_generations,
            n_battles_per_opponent=n_battles_per_opponent,
            verbose=True
        )

        print("\n=== BEST TEAM ===")
        print(f"Score {best_score:.4f}")
        for i, b in enumerate(best_team_repr, 1):
            print(f"{i}. {b['species']}: {b['moveset']}")

    # -----------------------------
    # Random Search (RS)
    # -----------------------------

    if method == "rs":
        n_opponents = len(OPPONENTS)
        battles_per_team_eval = n_battles_per_opponent * n_opponents

        # Each random sample costs evaluating one team
        n_samples = max(1, B // battles_per_team_eval)

        print("=== Random Search Schedule ===")
        print(f"Battle Budget: {B}")
        print(f"Battles per Team Evaluation: {battles_per_team_eval}")
        print(f"Random Samples: {n_samples}")

        rs = RandomSearchOptimizer(
            n_samples=n_samples,
            seed=seed,
        )

        best_team_indices, best_score, best_team_repr = rs.run_random_search(
            n_battles_per_opponent=n_battles_per_opponent,
            verbose=True,
        )

        print("\n=== BEST TEAM (Random Search) ===")
        print(f"Score {best_score:.4f}")
        for i, b in enumerate(best_team_repr, 1):
            print(f"{i}. {b['species']}: {b['moveset']}")


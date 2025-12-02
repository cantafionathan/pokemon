import json
import os
import time
from datetime import datetime

from opt.bo.optimizer import BOOptimizer
from opt.ga.optimizer import GAOptimizer
from opt.rs.optimizer import RandomSearchOptimizer

from simulator.battle_simulator import OPPONENTS
from opt.bo.encoding import parse_showdown_team


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def load_history(hist_path):
    """Load history which may be a raw list OR a dict containing history."""
    with open(hist_path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "history" in data:
        return data["history"]
    raise ValueError(f"Unexpected history format in {hist_path}")


def rewrite_history_B_used(
    history_list,
    method,
    *,
    n_b,
    n_opponents,
    population_size=None,
    n_moveset_samples=None,
    n_init_battles=None
):
    """Annotate each history entry with cumulative B_used."""

    if method == "bo":
        # Cost per BO iteration (excluding initial batch)
        cost_per_eval = n_b * n_opponents * n_moveset_samples

        for i, entry in enumerate(history_list):
            entry["B_used"] = n_init_battles + (i + 1) * cost_per_eval

    elif method == "ga":
        battles_per_generation = population_size * (n_b * n_opponents)

        for g, entry in enumerate(history_list):
            entry["B_used"] = (g + 1) * battles_per_generation

    elif method == "rs":
        cost_per_team = n_b * n_opponents

        for i, entry in enumerate(history_list):
            entry["B_used"] = (i + 1) * cost_per_team

    else:
        raise ValueError(f"Unknown method {method}")


def run_experiments():
    seeds = [0, 1, 2, 3, 4]
    methods = ["bo", "rs"]
    budgets = [5000, 10000]
    n_battles_per_opponent_list = [1, 3]

    ensure_dir("results/histories")
    ensure_dir("results/experiments")

    for seed in seeds:
        for method in methods:
            for B in budgets:
                for n_b in n_battles_per_opponent_list:

                    print(f"\n=== Running {method} | seed={seed} | B={B} | nb={n_b} ===")

                    hist_path = f"results/histories/{method}_seed{seed}_B{B}_nb{n_b}.json"

                    start = time.time()

                    # -----------------------------------------------------
                    # BO
                    # -----------------------------------------------------
                    if method == "bo":
                        opt = BOOptimizer()

                        n_init = 5
                        n_moveset_samples = 5
                        n_opponents = len(OPPONENTS)

                        cost_per_eval = n_b * n_moveset_samples * n_opponents
                        n_init_battles = n_init * cost_per_eval

                        n_iters = max(1, (B - n_init_battles) // cost_per_eval)

                        best_x, best_y, best_team_str = opt.run_bo(
                            n_iters=n_iters,
                            n_init=n_init,
                            n_battles_per_opponent=n_b,
                            n_moveset_samples=n_moveset_samples,
                            seed=seed,
                            history_file=hist_path,
                        )

                        final_team = parse_showdown_team(best_team_str)
                        final_wr = best_y

                    # -----------------------------------------------------
                    # GA
                    # -----------------------------------------------------
                    elif method == "ga":
                        population_size = 50
                        ga = GAOptimizer(
                            population_size=population_size,
                            mutation_rate=0.12,
                            seed=seed,
                        )

                        n_opponents = len(OPPONENTS)
                        battles_per_team = n_b * n_opponents
                        n_generations = max(1, B // (population_size * battles_per_team))

                        best_team, best_score, best_repr = ga.run_ga(
                            n_generations=n_generations,
                            n_battles_per_opponent=n_b,
                            verbose=False,
                            history_file=hist_path,
                        )

                        final_team = best_repr
                        final_wr = best_score

                    # -----------------------------------------------------
                    # RS
                    # -----------------------------------------------------
                    elif method == "rs":
                        n_opponents = len(OPPONENTS)
                        cost_per_team = n_b * n_opponents

                        n_samples = max(1, B // cost_per_team)

                        rs = RandomSearchOptimizer(
                            n_samples=n_samples,
                            seed=seed,
                        )

                        best_team, best_score, best_repr = rs.run_random_search(
                            n_battles_per_opponent=n_b,
                            verbose=False,
                            history_file=hist_path,
                        )

                        final_team = best_repr
                        final_wr = best_score

                    else:
                        raise ValueError(f"Unknown method {method}")

                    runtime_sec = time.time() - start

                    # -----------------------------------------------------
                    # Re-load and rewrite history with B_used
                    # -----------------------------------------------------
                    history_list = load_history(hist_path)

                    rewrite_history_B_used(
                        history_list,
                        method,
                        n_b=n_b,
                        n_opponents=len(OPPONENTS),
                        population_size=population_size if method == "ga" else None,
                        n_moveset_samples=n_moveset_samples if method == "bo" else None,
                        n_init_battles=n_init_battles if method == "bo" else None,
                    )

                    # Save updated history
                    with open(hist_path, "w") as f:
                        json.dump(history_list, f, indent=2)

                    # -----------------------------------------------------
                    # Save final result summary
                    # -----------------------------------------------------
                    result = {
                        "method": method,
                        "seed": seed,
                        "budget": B,
                        "battles_per_opponent": n_b,
                        "history": history_list,
                        "final_team": final_team,
                        "final_wr": round(final_wr, 5),
                        "runtime_sec": runtime_sec,
                        "timestamp": datetime.now().isoformat(),
                    }

                    final_path = f"results/experiments/{method}_seed{seed}_B{B}_nb{n_b}.json"
                    with open(final_path, "w") as f:
                        json.dump(result, f, indent=2)

                    print(f"Saved: {final_path}")


if __name__ == "__main__":
    run_experiments()

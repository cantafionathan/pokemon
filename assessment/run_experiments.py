from opt.optimizer import Optimizer
from simulator.battle_simulator import OPPONENTS
from opt.bo.encoding import parse_showdown_team
import os
import json
import time
from datetime import datetime


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
    methods = ["bo", "ga", "rs"]  # add or remove methods here
    budgets = [5000, 10000]

    ensure_dir("results/histories")
    ensure_dir("results/experiments")

    for seed in seeds:
        for method in methods:
            for B in budgets:

                    print(f"\n=== Running {method} | seed={seed} | B={B} ===")

                    hist_path = f"results/histories/{method}_seed{seed}_B{B}.json"

                    start = time.time()

                    optimizer = Optimizer(
                        method=method,
                        B=B,
                        seed=seed,
                        n_battles_per_opponent=1,
                        format="ou",  # or "ubers", or parameterize if needed
                    )

                    best_team_repr, best_score = optimizer.run()

                    runtime_sec = time.time() - start

                    # load history (if your optimizer saves history automatically)
                    # Otherwise, you can skip or modify accordingly
                    history_list = []
                    if os.path.exists(hist_path):
                        try:
                            history_list = load_history(hist_path)
                        except Exception:
                            print(f"Warning: Could not load history from {hist_path}")

                    # Compute n_init_battles and n_moveset_samples if bo, else None
                    n_opponents = len(OPPONENTS)
                    n_init = 5  # as per Optimizer _run_bo
                    n_moveset_samples = 5  # as per Optimizer _run_bo
                    n_init_battles = (
                        n_init * n_moveset_samples * n_opponents
                        if method == "bo"
                        else None
                    )
                    population_size = 2 if method == "ga" else None  # as per your Optimizer

                    rewrite_history_B_used(
                        history_list,
                        method,
                        n_b=1,
                        n_opponents=n_opponents,
                        population_size=population_size,
                        n_moveset_samples=n_moveset_samples if method == "bo" else None,
                        n_init_battles=n_init_battles,
                    )

                    # Save updated history
                    if history_list:
                        with open(hist_path, "w") as f:
                            json.dump(history_list, f, indent=2)

                    # Save final experiment summary
                    result = {
                        "method": method,
                        "seed": seed,
                        "budget": B,
                        "history": history_list,
                        "final_team": best_team_repr,
                        "final_wr": round(best_score, 5),
                        "runtime_sec": runtime_sec,
                        "timestamp": datetime.now().isoformat(),
                    }

                    final_path = f"results/experiments/{method}_seed{seed}_B{B}.json"
                    with open(final_path, "w") as f:
                        json.dump(result, f, indent=2)

                    print(f"Saved: {final_path}")


if __name__ == "__main__":
    run_experiments()

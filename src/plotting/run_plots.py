from pathlib import Path
import matplotlib.pyplot as plt

from plotting.loader import load_logs_from_path
from plotting.plots.score_vs_generation import plot_score_vs_generation
from plotting.plots.score_vs_battles import plot_score_vs_battles
from plotting.plots.team_evolution import TeamNavigator


def main():
    # ------------------------------------------------------------------
    # CONFIG — change these paths / choices as needed
    # ------------------------------------------------------------------

    # Can be:
    #  - logs/2025-01-01/
    #  - logs/2025-01-01/SomeMethod_12-30-00.json
    #  - logs/
    LOG_PATH = Path("logs/2025-12-19/test_experiment")

    # For team evolution: pick ONE run
    TEAM_EVOLUTION_METHOD = "EloGeneticAlgorithm"  # e.g. "EloGeneticAlgorithm"
    TEAM_EVOLUTION_SEED = None    # e.g. 1234
    EVERY_K_GENERATIONS = 1

    # ------------------------------------------------------------------
    # LOAD LOGS
    # ------------------------------------------------------------------

    runs = load_logs_from_path(LOG_PATH)

    if not runs:
        raise RuntimeError(f"No logs found at {LOG_PATH}")

    print(f"Loaded {len(runs)} runs")
    for r in runs:
        print(f"  Method={r.method}, Seed={r.run_seed}, Entries={len(r.entries)}")

    # ------------------------------------------------------------------
    # PLOTS ACROSS ALL RUNS (mean ± SE)
    # ------------------------------------------------------------------

    fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex=False)

    plot_score_vs_generation(runs, ax=axes[0, 0], mode="generation_best")
    plot_score_vs_generation(runs, ax=axes[1, 0], mode="best_so_far")
    plot_score_vs_battles(runs, ax=axes[0, 1], mode="generation_best")
    plot_score_vs_battles(runs, ax=axes[1, 1], mode="best_so_far")

    plt.tight_layout()
    plt.show()




    # ------------------------------------------------------------------
    # TEAM EVOLUTION (single run, interactive navigator)
    # ------------------------------------------------------------------

    if TEAM_EVOLUTION_METHOD is not None:
        matching = [
            r for r in runs
            if r.method == TEAM_EVOLUTION_METHOD
            and (TEAM_EVOLUTION_SEED is None or r.run_seed == TEAM_EVOLUTION_SEED)
        ]

        if not matching:
            raise RuntimeError(
                f"No run found for method={TEAM_EVOLUTION_METHOD}, "
                f"seed={TEAM_EVOLUTION_SEED}"
            )

        run = matching[0]

        print("\nTEAM EVOLUTION")
        print("=" * 80)

        # Filter to generations we want to display
        filtered_entries = [
            e for e in run.best_per_generation()
            if e.generation % EVERY_K_GENERATIONS == 0
        ]

        # Print generation info (optional)
        for e in filtered_entries:
            print(f"Generation {e.generation} - Score: {e.score:.4f}")

        # Now launch interactive navigator with filtered entries
        navigator = TeamNavigator(run, filtered_entries)


if __name__ == "__main__":
    main()

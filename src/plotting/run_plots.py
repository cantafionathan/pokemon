from pathlib import Path
import matplotlib.pyplot as plt

from plotting.loader import load_logs_from_path
from plotting.plots.score_vs_generation import plot_score_vs_generation
from plotting.plots.score_vs_battles import plot_score_vs_battles
from plotting.plots.team_evolution import TeamNavigator


def run_plots(
    log_path,
    tier: str,
    team_evolution_method: str | None = None,
    team_evolution_seed: int | None = None,
    every_k_generations: int | None = None,
):
    """
    Generate plots from experiment logs.

    Parameters
    ----------
    log_path : str | Path
        Path to experiment logs directory
    tier : str
        Tier name (OU, UU, etc.) — informational for titles
    team_evolution_method : str | None
        Optimizer method to visualize (None disables team evolution)
    team_evolution_seed : int | None
        Seed to visualize (None = auto-select best seed)
    every_k_generations : int | None
        Downsample generations for team evolution (None = generations // 5)
    """

    log_path = Path(log_path)

    # ------------------------------------------------------------------
    # LOAD LOGS
    # ------------------------------------------------------------------
    runs = load_logs_from_path(log_path)

    if not runs:
        raise RuntimeError(f"No logs found at {log_path}")

    print(f"Loaded {len(runs)} runs from {log_path}")
    for r in runs:
        print(f"  Method={r.method}, Seed={r.run_seed}, Entries={len(r.entries)}")

    # ------------------------------------------------------------------
    # PLOTS ACROSS ALL RUNS
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex=False)

    plot_score_vs_generation(runs, ax=axes[0, 0], mode="generation_best")
    plot_score_vs_generation(runs, ax=axes[1, 0], mode="best_so_far")
    plot_score_vs_battles(runs, ax=axes[0, 1], mode="generation_best")
    plot_score_vs_battles(runs, ax=axes[1, 1], mode="best_so_far")

    fig.suptitle(f"{tier} — Aggregate Performance", fontsize=14)
    plt.tight_layout()
    plt.show()

    # ------------------------------------------------------------------
    # TEAM EVOLUTION (single run)
    # ------------------------------------------------------------------
    if team_evolution_method is None:
        return

    # Filter runs by method
    method_runs = [r for r in runs if r.method == team_evolution_method]

    if not method_runs:
        raise RuntimeError(
            f"No runs found for method={team_evolution_method}"
        )

    # --------------------------------------------------
    # Auto-select best seed if not provided
    # --------------------------------------------------
    if team_evolution_seed is None:
        best_run = max(
            method_runs,
            key=lambda r: r.best_per_generation()[-1].score,
        )
        team_evolution_seed = best_run.run_seed

        print(
            f"Auto-selected best seed {team_evolution_seed} "
            f"for method {team_evolution_method}"
        )

    matching = [
        r for r in method_runs
        if r.run_seed == team_evolution_seed
    ]

    if not matching:
        raise RuntimeError(
            f"No run found for method={team_evolution_method}, "
            f"seed={team_evolution_seed}"
        )

    run = matching[0]

    # --------------------------------------------------
    # Auto-select k if not provided
    # --------------------------------------------------
    max_generation = run.entries[-1].generation

    if every_k_generations is None:
        every_k_generations = max(1, max_generation // 5)

        print(
            f"Auto-selected every_k_generations={every_k_generations} "
            f"(generations={max_generation})"
        )

    filtered_entries = [
        e for e in run.best_per_generation()
        if e.generation % every_k_generations == 0
    ]

    print("\nTEAM EVOLUTION")
    print("=" * 80)
    for e in filtered_entries:
        print(f"Generation {e.generation} - Score: {e.score:.4f}")

    TeamNavigator(run, filtered_entries)


# ----------------------------------------------------------------------
# Standalone usage (keeps old behavior)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    run_plots(
        log_path="ga_vs_rs_OU",
        tier="OU",
        team_evolution_method="EloGeneticAlgorithm",
        team_evolution_seed=0,
        every_k_generations=1,
    )

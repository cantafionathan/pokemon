from pathlib import Path
import matplotlib.pyplot as plt
import json
import numpy as np
from collections import defaultdict
import warnings


from plotting.loader import load_logs_from_path
from plotting.score_vs_generation import plot_score_vs_generation
from plotting.score_vs_battles import plot_score_vs_battles
from plotting.team_evolution import TeamViewer


def run_plots(
    log,
    tier: str,
    team_evolution_method: str | None = None,
    team_evolution_seed: int | None = None,
    every_k_generations: int | None = None,
    animation: bool = False,
    interval_ms: int = 1000,
    save: bool = False,
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

    log_path = Path("logs") / log

    if not log_path.exists():
        raise RuntimeError(f"Log path does not exist: {log_path}")

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
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), sharex=False)
    # if for some reason plotting number of battle stoo, change to 
    # fig, axes = plt.subplots(1, 2, figsize=(14, 8), sharex=False)
    # and adjust axes in below plots accordingly

    plot_score_vs_generation(runs, ax=axes[0], mode="generation_best")
    plot_score_vs_generation(runs, ax=axes[1], mode="best_so_far")
    # plot_score_vs_battles(runs, ax=axes[0, 1], mode="generation_best")
    # plot_score_vs_battles(runs, ax=axes[1, 1], mode="best_so_far")

    fig.suptitle(f"{tier} — Aggregate Performance", fontsize=14)
    plt.tight_layout()
    if save:
        save_dir = Path("plots") / log_path.name
        save_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_dir / f"aggregate_performance.png")
    plt.show()

    # ------------------------------------------------------------------
    # EVALUATION AGAINST META (mean win-rate per method)
    # ------------------------------------------------------------------
    evaluation_files = sorted(
        p for p in log_path.iterdir()
        if p.name.startswith("EVALUATION_") and p.suffix == ".json"
    )

    if not evaluation_files:
        warnings.warn(f"No evaluation files found in {log_path}; skipping evaluation plot")
    
    else:

        # Group evaluation data by method
        by_method = defaultdict(list)

        for p in evaluation_files:
            name = p.stem[len("EVALUATION_"):]
            method = name.split("_", 1)[0]

            with open(p, "r") as f:
                entries = json.load(f)

            # map generation -> win_rate
            gen_to_wr = {
                e["generation"]: e["win_rate"]
                for e in entries
            }

            by_method[method].append(gen_to_wr)

        methods = sorted(by_method.keys())

        fig, ax = plt.subplots(figsize=(7, 5))

        for method in methods:
            eval_runs = by_method[method]

            # Union of all generations observed for this method
            all_generations = sorted(
                set().union(*[r.keys() for r in eval_runs])
            )

            mean_wr = []
            std_wr = []

            for g in all_generations:
                values = [r[g] for r in eval_runs if g in r]
                mean_wr.append(np.mean(values))
                std_wr.append(np.std(values))

            ax.plot(
                all_generations,
                mean_wr,
                marker="o",
                label=f"{method} (mean)",
            )

            # Optional: shaded variance
            ax.fill_between(
                all_generations,
                np.array(mean_wr) - np.array(std_wr),
                np.array(mean_wr) + np.array(std_wr),
                alpha=0.2,
            )

        ax.set_title(f"{tier} — Mean Evaluation Win Rate vs Generation")
        ax.set_xlabel("Generation")
        ax.set_ylabel("Win rate")
        ax.grid(True)
        ax.legend()
        plt.tight_layout()
        if save:
            save_dir = Path("plots") / log_path.name
            save_dir.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_dir / f"aggregate_evaluation.png")
        plt.show()


    # ------------------------------------------------------------------
    # TEAM EVOLUTION (single run)
    # plot the best team seen so far over each generation
    # ------------------------------------------------------------------
    if team_evolution_method is None:
        return
    
    for method in team_evolution_method:

        # Filter runs by method
        method_runs = [r for r in runs if r.method == method]

        if not method_runs:
            raise RuntimeError(
                f"No runs found for method={method}"
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
                f"for method {method}"
            )

        matching = [
            r for r in method_runs
            if r.run_seed == team_evolution_seed
        ]

        if not matching:
            raise RuntimeError(
                f"No run found for method={method}, "
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

        if save:
            save_path = Path("plots") / log
        else:
            save_path = None


        TeamViewer(run, filtered_entries, animation=animation, interval_ms=interval_ms, save_path=save_path)

    

# ----------------------------------------------------------------------
# Standalone usage (keeps old behavior)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    run_plots(
        log="ga_vs_rs_OU_2025-12-19_23-29-58",
        tier="OU",
        team_evolution_method=["EloGeneticAlgorithm", "EloRandomSearch"],
        team_evolution_seed=0,
        every_k_generations=1,
        animation=True,
        interval_ms=1000,
        save=True
    )

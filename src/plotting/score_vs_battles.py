import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from typing import Literal, Optional

from plotting.utils import group_runs_by_method, mean_and_se
from plotting.models import RunLog


def _per_run_curve(
    run: RunLog,
    mode: Literal["generation_best", "best_so_far"],
):
    """
    Returns list of (generation, score, battles).
    """
    if mode == "generation_best":
        return [
            (e.generation, e.score, e.total_battles_used)
            for e in run.best_per_generation()
        ]

    elif mode == "best_so_far":
        best = float("-inf")
        result = []
        for e in sorted(run.entries, key=lambda x: x.generation):
            best = max(best, e.score)
            result.append((e.generation, best, e.total_battles_used))
        return result

    else:
        raise ValueError(f"Unknown mode: {mode}")


def plot_score_vs_battles(
    runs: list[RunLog],
    ax: Optional[plt.Axes] = None,
    mode: Literal["generation_best", "best_so_far", "both"] = "both",
):
    by_method = group_runs_by_method(runs)

    linestyles = ["-", "--", "-.", ":"]
    method_styles = {
        method: linestyles[i % len(linestyles)]
        for i, method in enumerate(sorted(by_method.keys()))
    }

    if ax is not None:
        if mode == "both":
            raise ValueError("Cannot use mode='both' with provided single axis")
        axes = {mode: ax}
        created_fig = False
    else:
        if mode == "both":
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
            axes = {"generation_best": ax1, "best_so_far": ax2}
            created_fig = True
        else:
            fig, ax_single = plt.subplots(figsize=(8, 6))
            axes = {mode: ax_single}
            created_fig = True

    titles = {
        "generation_best": "Best Score Within Each Generation (mean ± SE)",
        "best_so_far": "Best Score So Far Over Time (mean ± SE)",
    }

    for method, method_runs in by_method.items():
        linestyle = method_styles[method]

        for m, ax_ in axes.items():
            scores_by_gen = defaultdict(list)
            battles_by_gen = defaultdict(list)

            for run in method_runs:
                for gen, score, battles in _per_run_curve(run, m):
                    scores_by_gen[gen].append(score)
                    battles_by_gen[gen].append(battles)

            gens = sorted(scores_by_gen)

            mean_scores = []
            ses = []
            mean_battles = []

            for g in gens:
                mean, se = mean_and_se(scores_by_gen[g])
                mean_scores.append(mean)
                ses.append(se)
                mean_battles.append(sum(battles_by_gen[g]) / len(battles_by_gen[g]))

            mean_scores = np.array(mean_scores)
            ses = np.array(ses)
            mean_battles = np.array(mean_battles)

            label = method

            ax_.plot(mean_battles, mean_scores, label=label, linestyle=linestyle)
            ax_.fill_between(
                mean_battles,
                mean_scores - ses,
                mean_scores + ses,
                alpha=0.25,
            )
            ax_.set_title(titles[m])
            ax_.set_ylabel("ELO Score (per method)")
            ax_.grid(True)
            ax_.legend()

    # Set xlabel only on bottom plot if multiple axes
    if len(axes) > 1:
        bottom_ax = list(axes.values())[-1]
        bottom_ax.set_xlabel("Total battles used")
    else:
        only_ax = list(axes.values())[0]
        only_ax.set_xlabel("Total battles used")

    if created_fig:
        plt.tight_layout()
        plt.show()

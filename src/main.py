import argparse
from pathlib import Path
from utils import now_vancouver

from experiments import EXPERIMENTS
from plotting.run_plots import run_plots


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--experiment",
        required=True,
        choices=EXPERIMENTS.keys(),
        help="Which experiment to run",
    )

    parser.add_argument(
        "--tier",
        default="OU",
        choices=["Uber", "OU", "UU", "NU", "PU", "ZU", "LC"],
        help="Tier to run (OU, UU, LC, etc.)",
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Automatically generate plots after experiment",
    )

    # --------------------------------------------------
    # Team evolution options
    # --------------------------------------------------
    parser.add_argument(
        "--team-evo-method",
        default=None,
        help="Method to visualize team evolution for",
    )

    parser.add_argument(
        "--team-evo-seed",
        type=int,
        default=None,
        help="Seed to visualize (default: best seed for method)",
    )

    parser.add_argument(
        "--team-evo-k",
        type=int,
        default=None,
        help="Show every k generations (default: generations // 5)",
    )

    args = parser.parse_args()

    now = now_vancouver()
    date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H-%M-%S")

    log = f"{args.experiment}_{args.tier}_{date}_{timestamp}"
    log_path = Path("logs") / log

    # -------------------------
    # Run experiment
    # -------------------------
    experiment_fn = EXPERIMENTS[args.experiment]
    experiment_fn(args.tier, log_path=log)

    # -------------------------
    # Run plotting
    # -------------------------
    if args.plot:
        run_plots(
            log_path=log_path,
            tier=args.tier,
            team_evolution_method=args.team_evo_method,
            team_evolution_seed=args.team_evo_seed,
            every_k_generations=args.team_evo_k,
        )


if __name__ == "__main__":
    main()

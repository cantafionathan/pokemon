import argparse
from pathlib import Path
from utils import now_vancouver

from experiments import EXPERIMENTS

def main():
    parser = argparse.ArgumentParser(add_help=False)

    # --------------------------------------------------
    # Global arguments
    # --------------------------------------------------

    parser.add_argument(
        "--experiment",
        required=True,
        choices=EXPERIMENTS.keys(),
        help="Which experiment to run",
    )

    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[0, 1, 2],
        help="Which seeds to run the experiment with (default: 0, 1, 2)"
    )

    parser.add_argument(
        "--tier",
        default="OU",
        choices=["Uber", "OU", "UU", "NU", "PU", "ZU", "LC"],
        help="Tier to run (OU, UU, LC, etc.)",
    )

    parser.add_argument(
        "--engine",
        default="poke-env",
        choices=["poke-env"],
        help="Battle engine to use (default: poke-env)"
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="If a plotting method exists, automatically generate plots after experiment",
    )

    parser.add_argument("-h", "--help", action="store_true")

    # Parse *only* known args
    args, remaining_argv = parser.parse_known_args()

    ###

    now = now_vancouver()
    date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H-%M-%S")

    log = f"{args.experiment}_{args.tier}_{date}_{timestamp}"
    log_path = Path("logs") / log

    # -------------------------
    # Run experiment
    # -------------------------
    experiment_cfg = EXPERIMENTS[args.experiment]
    add_args = experiment_cfg.get("add_args")
    experiment_fn = experiment_cfg["run"]
    plot_fn = experiment_cfg["plot"]

    if add_args is not None:
        add_args(parser)

    # If help was requested, print *full* help and exit
    if args.help:
        parser.print_help()
        return

    args = parser.parse_args()


    experiment_fn(args.tier, args.engine, log=log, args=args)

    # -------------------------
    # Run plotting
    # -------------------------
    if args.plot:
        if plot_fn is None:
            raise RuntimeError(
                f"Experiment '{args.experiment}' does not define a plot function"
            )

        plot_fn(
            log_path=log_path,
            tier=args.tier,
            team_evolution_method=args.team_evo_method,
            team_evolution_seed=args.team_evo_seed,
            every_k_generations=args.team_evo_k,
        )


if __name__ == "__main__":
    main()

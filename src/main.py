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
        help="Which seeds (separated by spaces) to run the experiment with (default: 0 1 2)"
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

    # Team evaluation option
    parser.add_argument(
        "--team-evaluation",
        default=True,
        choices=[True, False],
        help="Flag to indicate if team evaluation should be performed (default: True)",
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
    log = "ga_vs_rs_OU_2025-12-19_23-29-58"


    # -------------------------
    # Run experiment
    # -------------------------
    experiment_cfg = EXPERIMENTS[args.experiment]
    add_args = experiment_cfg.get("add_args")
    experiment_fn = experiment_cfg["run"]
    evaluate_fn = experiment_cfg["evaluation"]
    plot_fn = experiment_cfg["plot"]

    if add_args is not None:
        add_args(parser)

    # If help was requested, print *full* help and exit
    if args.help:
        parser.print_help()
        return

    args = parser.parse_args()

    
    # experiment_fn(args.tier, args.engine, log=log, args=args)

    # if args.team_evaluation:
    #     if evaluate_fn is None:
    #         raise RuntimeError(
    #             f"Experiment '{args.experiment}' does not define an evaluation function"
    #         )
        
    #     evaluate_fn(args.engine, args.tier, log = log)

    # -------------------------
    # Run plotting
    # -------------------------
    if args.plot:
        if plot_fn is None:
            raise RuntimeError(
                f"Experiment '{args.experiment}' does not define a plot function"
            )

        save = (
            True if args.save == "yes"
            else False if args.save == "no"
            else None
        )

        animation = (
            True if args.animation == "yes"
            else False if args.animation == "no"
            else None
        )


        plot_fn(
            log=log,
            tier = args.tier,
            team_evolution_method=args.team_evo_method,
            team_evolution_seed=args.team_evo_seed,
            every_k_generations=args.team_evo_k,
            animation=animation,
            interval_ms=args.interval_ms,
            save=save,
        )


if __name__ == "__main__":
    main()

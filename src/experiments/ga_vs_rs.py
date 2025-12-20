from pathlib import Path

from optimization.elo_ga import EloGeneticAlgorithm
from optimization.elo_rs import EloRandomSearch
from config import get_engine, get_format


def add_args(parser):

    # GA Hyperparameters
    parser.add_argument(
        "--population-size",
        type=int,
        default=30,
        help="Population size for GA (default: 30)",
    )

    parser.add_argument(
        "--survivors-count",
        type=int,
        default=6,
        help="Number of survivors for GA (default: 6)",
    )

    parser.add_argument(
        "--num-matchups",
        type=int,
        default=100,
        help="Number of matchups for GA at each generation to determine ELO (default: 100)",
    )

    parser.add_argument(
        "--generations",
        type=int,
        default=10,
        help="Number of generations for GA (default: 10)",
    )

    parser.add_argument(
        "--pokemon-mutation-rate",
        type=float,
        default=0.5,
        help="Mutation rate for Pokémon in GA (default: 0.5)",
    )

    parser.add_argument(
        "--move-mutation-rate",
        type=float,
        default=0.25,
        help="Mutation rate for moves in GA (default: 0.25)",
    )

    # Team evolution options
    parser.add_argument(
        "--team-evo-method",
        default=None,
        choices=["EloGeneticAlgorithm", "EloRandomSearch"],
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

def run_optimizer(tier: str, engine: str, log: str, optimizer_cls, args, extra_kwargs=None):
    if extra_kwargs is None:
        extra_kwargs = {}

    learnsets_file = Path(
        f"data/learnsets_by_tier/learnsets_{tier.lower()}.json"
    )
    battle_engine_func = get_engine(engine)
    battle_format = get_format(tier)

    for seed in args.seeds:
        optimizer = optimizer_cls(
            learnsets_path=learnsets_file,
            battle_engine_func=battle_engine_func,
            battle_format=battle_format,
            population_size=args.population_size,
            survivors_count=args.survivors_count,
            num_matchups=args.num_matchups,
            logging=log,
            seed=seed,
            **extra_kwargs,
        )

        optimizer.optimize(args.generations)


def run_ga_vs_rs(tier: str, engine: str, log: str, args):
    print(f"\n=== Running GA vs RS | Tier {tier} ===")

    run_optimizer(
        tier,
        engine,
        log,
        EloGeneticAlgorithm,
        args=args,
        extra_kwargs={
            "p_pokemon_mutation_rate": args.pokemon_mutation_rate,
            "move_mutation_rate": args.move_mutation_rate,
        },
    )

    run_optimizer(tier, engine, log, EloRandomSearch, args)

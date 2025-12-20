from pathlib import Path

from optimization.elo_ga import EloGeneticAlgorithm
from optimization.elo_rs import EloRandomSearch
from config import get_engine, get_format

SEEDS = [0, 1, 2]

POPULATION_SIZE = 10
SURVIVORS_COUNT = 2
NUM_MATCHUPS = 25
GENERATIONS = 3


def run_optimizer(tier: str, log_path: str, optimizer_cls, extra_kwargs=None):
    if extra_kwargs is None:
        extra_kwargs = {}

    learnsets_file = Path(
        f"data/learnsets_by_tier/learnsets_{tier.lower()}.json"
    )
    battle_engine_func = get_engine("poke-env")
    battle_format = get_format(tier)

    for seed in SEEDS:
        optimizer = optimizer_cls(
            learnsets_path=learnsets_file,
            battle_engine_func=battle_engine_func,
            battle_format=battle_format,
            population_size=POPULATION_SIZE,
            survivors_count=SURVIVORS_COUNT,
            num_matchups=NUM_MATCHUPS,
            logging=log_path,
            seed=seed,
            **extra_kwargs,
        )

        optimizer.optimize(GENERATIONS)


def run_ga_vs_rs(tier: str, log_path: str):
    print(f"\n=== Running GA vs RS | Tier {tier} ===")

    run_optimizer(
        tier,
        log_path,
        EloGeneticAlgorithm,
        extra_kwargs={
            "p_pokemon_mutation_rate": 0.1,
            "move_mutation_rate": 0.2,
        },
    )

    run_optimizer(tier, log_path, EloRandomSearch)

from pathlib import Path
from optimization.base import PopulationOptimizer, Evaluation
from config import get_format, get_engine
from utils import build_team_summary

BASE_ELO = 1000.0
K_FACTOR = 32
ELO_DECAY = 0.2  # 0.0 = full memory, 1.0 = full reset

class EloRandomSearch(PopulationOptimizer):
    def __init__(
        self,
        *,
        num_matchups: int,
        population_size: int,
        survivors_count: int,
        **kwargs,
    ):
        super().__init__(**kwargs)
        assert survivors_count < population_size, "survivors_count must be less than population_size"
        self.population_size = population_size
        self.survivors_count = survivors_count
        self.num_matchups = num_matchups
        self.elo = None  # initialized on first evaluation

    def initialize_population(self):
        self.population = [self.sample_random_team() for _ in range(self.population_size)]

    def evaluate_teams(self, population):
        n = len(population)

        if self.elo is None or len(self.elo) != n:
            self.elo = [BASE_ELO] * n
        else:
            self.elo = [
                (1 - ELO_DECAY) * r + ELO_DECAY * BASE_ELO
                for r in self.elo
            ]

        for _ in range(self.num_matchups):
            i, j = self.rng.sample(range(n), 2)

            ra, rb = self.elo[i], self.elo[j]
            ea = 1 / (1 + 10 ** ((rb - ra) / 400))
            eb = 1 - ea

            result = self.battle_engine_func(population[i], population[j], self.format)

            if result == 1:
                sa, sb = 1.0, 0.0
            elif result == 2:
                sa, sb = 0.0, 1.0
            else:
                sa, sb = 0.5, 0.5

            self.elo[i] += K_FACTOR * (sa - ea)
            self.elo[j] += K_FACTOR * (sb - eb)
            self.total_battles_used += 1

        return [
            Evaluation(
                score=self.elo[i],
                team=population[i],
                meta={"index": i}
            )
            for i in range(n)
        ]

    def produce_next_generation(self, evaluations):
        # Sort by fitness
        evaluations = sorted(evaluations, key=lambda e: e.score, reverse=True)

        # Select survivors
        survivors = evaluations[:self.survivors_count]

        # Build next population
        new_population = [e.team for e in survivors]
        new_population += [
            self.sample_random_team()
            for _ in range(self.population_size - self.survivors_count)
        ]

        # Carry over Elo in the corresponding to survivors in the new generation
        new_elo = [self.elo[e.meta["index"]] for e in survivors]

        # Reset Elo for newly sampled teams
        new_elo += [BASE_ELO] * (self.population_size - self.survivors_count)

        self.elo = new_elo
        return new_population


if __name__ == "__main__":
    tier = "OU"  # Choose any one of: "Uber", "OU", "UU", "NU", "PU", "ZU", "LC"
    learnsets_file = Path(f"data/learnsets_by_tier/learnsets_{tier.lower()}.json")
    battle_engine_func = get_engine("poke-env")
    battle_format = get_format(tier)

    # choose hyper parameters
    population_size = 10
    survivors_count = 2
    num_matchups = 25
    generations = 5

    optimizer = EloRandomSearch(learnsets_path=learnsets_file,
                               battle_engine_func=battle_engine_func, 
                               battle_format=battle_format, 
                               population_size=population_size, 
                               survivors_count=survivors_count,
                               num_matchups=num_matchups, 
                               logging="test_experiment",
                               seed = None)
    
    best_score, best_team = optimizer.optimize(generations)

    print("\nFinal Top Teams:")
    print(f"Score: {best_score}")
    print(build_team_summary(*best_team))
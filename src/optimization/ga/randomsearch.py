import random
from pathlib import Path
from typing import List, Tuple
from .base import Team, GeneticAlgorithm
from config import get_format
from utils import build_team_summary


class RandomSearchGA(GeneticAlgorithm):
        def evaluate_teams(self, population: List[Team]) -> List[Tuple[int, Team]]:
            scores = []
            for idx, team in enumerate(population):
                opponents = random.sample([t for i, t in enumerate(population) if i != idx], self.num_opponents)
                wins = self.evaluate_team(team, opponents)
                self.total_battles_used += self.num_opponents
                scores.append((wins, team))
            return scores

        def produce_next_generation(self, scores):
            survivors = [team for _, team in scores[:self.survivors_count]]
            new_teams = [self.sample_random_team() for _ in range(self.population_size - self.survivors_count)]
            return survivors + new_teams
        
if __name__ == "__main__":
    tier = "OU"  # "Uber", "OU", "UU", "NU", "PU", "ZU", "LC"
    learnsets_file = Path(f"data/learnsets_by_tier/learnsets_{tier.lower()}.json")
    battle_format = get_format(tier)
    population_size = 20
    survivors_count = 5
    num_opponents = 10
    generations = 10

    optimizer = RandomSearchGA(learnsets_file, 
                               battle_format, 
                               population_size, 
                               survivors_count,
                               num_opponents, 
                               logging=True)
    top_results = optimizer.optimize(generations)

    print("\nFinal Top Teams:")
    for score, team in top_results:
        print(f"Score: {score}")
        print(build_team_summary(*team))
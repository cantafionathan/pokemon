import random
import json
import time
from datetime import datetime, timezone
from typing import List, Tuple, Union
from pathlib import Path

from poke_env_engine.battle_simulator import battle_once
from config import get_format
from utils import build_team_summary

Team = Tuple[List[int], List[List[int]]]  # (pokemon_ids, moves_ids_per_pokemon)

class GeneticAlgorithm:
    def __init__(
        self,
        learnsets_path: Path,
        battle_format: str,
        population_size: int,
        survivors_count: int,
        num_opponents: int,
        logging: Union[bool, str] = False,  # False: no logs, True: default path, str: custom filename/folder
    ):
        assert survivors_count < population_size, "survivors_count must be less than population_size"
        assert num_opponents <= population_size, "num_opponents must be less than population_size"
        self.learnsets_path = learnsets_path
        self.format = battle_format
        self.population_size = population_size
        self.survivors_count = survivors_count
        self.num_opponents = num_opponents
        self.population: List[Team] = []

        # Logging setup
        self.logging = logging
        self.logs = []
        self.start_time = None
        self.total_battles_used = 0

    def sample_random_team(self) -> Team:
        with open(self.learnsets_path, encoding="utf-8") as f:
            learnsets = json.load(f)

        valid_pokemon = [
            pid for pid, pdata in learnsets.items()
            if len(pdata.get("learned", [])) >= 4
        ]
        if len(valid_pokemon) < 6:
            raise ValueError("Not enough Pokémon with 4+ moves to build a full team")

        chosen_pokemon = random.sample(valid_pokemon, 6)

        pokemon_ids = []
        moves_ids_per_pokemon = []

        for pid in chosen_pokemon:
            pdata = learnsets[pid]
            pokemon_ids.append(int(pid))  # convert string ID to int

            learned_moves = pdata.get("learned", [])
            chosen_moves = random.sample(learned_moves, 4)
            moves_ids = [move["move_id"] for move in chosen_moves]
            moves_ids_per_pokemon.append(moves_ids)

        return (pokemon_ids, moves_ids_per_pokemon)

    def initialize_population(self):
        self.population = [self.sample_random_team() for _ in range(self.population_size)]

    def log_entry(self, iteration: int, team: Team, wins: int):
        if not self.logging:
            return
        now_iso = datetime.now(timezone.utc).isoformat() + "Z"
        runtime_sec = time.time() - self.start_time if self.start_time else 0

        # Store team as a JSON array (no extra whitespace)
        team_str = json.dumps(team, separators=(',', ':'))

        entry = {
            "timestamp": now_iso,
            "team": team_str,
            "battles_used_for_this_generation": self.total_battles_used,
            "runtime_sec": runtime_sec,
            "generation": iteration,
            "wins": wins,
            "winrate": wins / self.survivors_count if self.survivors_count > 0 else 0
        }
        self.logs.append(entry)

    def save_logs(self, filename: Path = None):
        if not self.logging or not self.logs:
            return

        folder = Path("logs") / datetime.now(timezone.utc).strftime("%Y-%m-%d")
        folder.mkdir(parents=True, exist_ok=True)

        if filename is None:
            # Use subclass name as prefix
            prefix = self.__class__.__name__

            if self.logging is True:
                timestamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
                filename = folder / f"{prefix}_{timestamp}.json"
            elif isinstance(self.logging, str):
                # If user provided a string filename, still prefix it
                base_name = self.logging
                if base_name.lower().endswith(".json"):
                    base_name = base_name[:-5]
                filename = folder / f"{prefix}_{base_name}.json"
            else:
                timestamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
                filename = folder / f"{prefix}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)

        print(f"[LOG] Saved optimization logs to {filename}")

    def evaluate_team(self, team: Team, opponents: List[Team]) -> int:
        wins = 0
        for opp in opponents:
            result = battle_once(team, opp, self.format)
            if result == 1:
                wins += 1
        return wins

    def evaluate_teams(self, population: List[Team]) -> List[Tuple[int, Team]]:
        """
        Evaluate all teams in the given population and return their scores.
        
        Args:
            population: List of teams to evaluate.
            
        Returns:
            List of (score, team) tuples.
        """
        raise NotImplementedError("Must implement evaluate_teams")

    def produce_next_generation(self, scores: List[Tuple[int, Team]]) -> List[Team]:
        """
        Placeholder method to produce the next generation population.

        Args:
            scores: List of tuples (score, team), sorted by score descending.

        Returns:
            List of teams forming the next population.
        """
        raise NotImplementedError("Must implement produce_next_generation")

    def optimize(self, generations: int):
        self.initialize_population()
        self.start_time = time.time()

        for iteration in range(1, generations + 1):
            print(f"Generation {iteration}/{generations}")

            scores = self.evaluate_teams(self.population)

            # Logging
            for score, team in scores:
                self.log_entry(iteration, team, score)

            scores.sort(key=lambda x: x[0], reverse=True)
            top_teams = [team for _, team in scores[:self.survivors_count]]
            print(f"Top {self.survivors_count} teams selected with scores: {[score for score, _ in scores[:self.survivors_count]]}")

            self.population = self.produce_next_generation(scores)

        self.save_logs()

        return scores[:self.survivors_count]



if __name__ == "__main__":
    tier = "OU"  # "Uber", "OU", "UU", "NU", "PU", "ZU", "LC"
    learnsets_file = Path(f"data/learnsets_by_tier/learnsets_{tier.lower()}.json")
    battle_format = get_format(tier)
    population_size = 10
    survivors_count = 2
    num_opponents = 2
    generations = 2

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

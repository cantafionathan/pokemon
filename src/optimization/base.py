import random
import json
import time
import uuid
from datetime import datetime, timezone
from typing import List, Tuple, Union, Callable
from pathlib import Path
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Evaluation:
    score: float
    team: Team
    meta: Any = None

Team = Tuple[List[int], List[List[int]]]  # (pokemon_ids, moves_ids_per_pokemon)

class PopulationOptimizer:
    def __init__(
        self,
        learnsets_path: Path,
        battle_engine_func: Callable,
        battle_format: str,
        logging: Union[bool, str] = False,  # False: no logs, True: default path, str: custom filename/folder
        seed: int | None = None
    ):
        with open(learnsets_path, encoding="utf-8") as f:
            self.learnsets = json.load(f)
        self.battle_engine_func = battle_engine_func
        self.format = battle_format
        self.population: List[Team] = []

        # Logging setup
        self.logging = logging
        self.logs = []
        self.start_time = None
        self.total_battles_used = 0
        self.run_id = str(uuid.uuid4())

        # seeding
        self.seed = seed
        self.rng = random.Random(seed)

    
    def sample_random_team(self) -> Team:
        valid_pokemon = [
            pid for pid, pdata in self.learnsets.items()
            if len(pdata.get("learned", [])) >= 4
        ]
        if len(valid_pokemon) < 6:
            raise ValueError("Not enough Pokémon with 4+ moves to build a full team")

        chosen_pokemon = self.rng.sample(valid_pokemon, 6)

        pokemon_ids = []
        moves_ids_per_pokemon = []

        for pid in chosen_pokemon:
            pdata = self.learnsets[pid]
            pokemon_ids.append(int(pid))  # convert string ID to int

            learned_moves = pdata.get("learned", [])
            chosen_moves = self.rng.sample(learned_moves, 4)
            moves_ids = [move["move_id"] for move in chosen_moves]
            moves_ids_per_pokemon.append(moves_ids)

        return (pokemon_ids, moves_ids_per_pokemon)

    def log_entry(self, iteration: int, team: Team, score: float):
        if not self.logging:
            return

        now_iso = datetime.now(timezone.utc).isoformat() + "Z"
        runtime_sec = time.time() - self.start_time if self.start_time else 0

        team_str = json.dumps(team, separators=(',', ':'))

        entry = {
            "timestamp": now_iso,
            "team": team_str,
            "generation": iteration,
            "score": score,
            "total_battles_used": self.total_battles_used,
            "runtime_sec": runtime_sec,
            "run_seed": self.seed,
            "method": self.__class__.__name__,
            "format": self.format,
            "run_id": self.run_id,
        }

        self.logs.append(entry)


    def save_logs(self, filename: Path = None):
        if not self.logging or not self.logs:
            return

        date_folder = Path("logs") / datetime.now(timezone.utc).strftime("%Y-%m-%d")

        prefix = self.__class__.__name__
        timestamp = datetime.now(timezone.utc).strftime("%H-%M-%S")

        # Case 1: logging is a string → logs/YYYY-MM-DD/<string>/
        if isinstance(self.logging, str):
            folder = date_folder / self.logging
            folder.mkdir(parents=True, exist_ok=True)

            if filename is None:
                filename = folder / f"{prefix}_{timestamp}.json"

        # Case 2: logging is True → logs/YYYY-MM-DD/
        else:
            folder = date_folder
            folder.mkdir(parents=True, exist_ok=True)

            if filename is None:
                filename = folder / f"{prefix}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)

        print(f"[LOG] Saved optimization logs to {filename}")


    def initialize_population(self):
        """
        Placeholder method to initialize the population.
        """
        raise NotImplementedError("Must implement initialize_population")

    def evaluate_teams(self, population: List[Team]) -> List[Evaluation]:
        """
        Placeholder method to evaluate all teams in the given population and return their scores.
        
        Args:
            population: List of teams to evaluate.
            
        Returns:
            List of Evaluation objects, sorted by score descending.

        Note:
            This method must update self.total_battles_used.
        """
        raise NotImplementedError("Must implement evaluate_teams")
    

    def produce_next_generation(self, scores: List[Evaluation]) -> List[Team]:
        """
        Placeholder method to produce the next generation population.

        Args:
            scores: List of Evaluation objects, sorted by score descending.

        Returns:
            List of teams forming the next population.
        """
        raise NotImplementedError("Must implement produce_next_generation")
    

    def optimize(self, generations: int):
        self.initialize_population()
        self.start_time = time.time()

        best_score = float("-inf")
        best_team = None

        for iteration in range(1, generations + 1):
            print(f"Generation {iteration}/{generations}")

            scores = self.evaluate_teams(self.population)

            # Update global best
            for e in scores:
                if e.score > best_score:
                    best_score = e.score
                    best_team = e.team

            # Optional: sort only for logging / readability
            scores_sorted = sorted(scores, key=lambda e: e.score, reverse=True)

            if scores_sorted:
                print(f"Best score this generation: {scores_sorted[0].score}")
            else:
                print("No teams evaluated this generation.")


            # Logging
            for e in scores:
                score = e.score
                team = e.team
                self.log_entry(iteration, team, score)


            self.population = self.produce_next_generation(scores_sorted)

        self.save_logs()

        return best_score, best_team



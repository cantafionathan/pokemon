import random
import json
import time
from datetime import datetime, timezone
from typing import List, Tuple, Union
from pathlib import Path

from poke_env_engine.battle_simulator import battle_once
from config import get_format
from utils import build_team_summary


Team = Tuple[List[int], List[List[int]]]  # type alias for team: (pokemon_ids, moves_ids_per_pokemon)

class RandomSearchOptimizer:
    def __init__(
        self,
        learnsets_path: Path,
        battle_format: str,
        N: int,
        m: int,
        logging: Union[bool, str] = False,  # False: no logs, True: default path, str: custom folder suffix
    ):
        assert m < N, "m must be less than N"
        self.learnsets_path = learnsets_path
        self.format = battle_format
        self.N = N
        self.m = m
        self.pool: List[Team] = []

        # Logging setup
        self.logging = logging
        self.logs = []
        self.start_time = None
        self.total_battles_used = 0  # Accumulate total battles over all iterations

    def sample_random_team(self):
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

    def initialize_pool(self):
        self.pool = [self.sample_random_team() for _ in range(self.N)]

    def evaluate_team(self, team: Team, opponents: List[Team]) -> int:
        wins = 0
        for opp in opponents:
            result = battle_once(team, opp, self.format)
            if result == 1:
                wins += 1
        return wins

    def log_entry(self, iteration: int, team: Team, wins: int):
        if not self.logging:
            return
        now_iso = datetime.now(timezone.utc).isoformat() + "Z"
        runtime_sec = time.time() - self.start_time if self.start_time else 0

        team_str = json.dumps(team, separators=(',', ':'))

        entry = {
            "timestamp": now_iso,
            "team": team_str,
            "battles_used": self.total_battles_used,
            "runtime_sec": runtime_sec,
            "additional": {
                "iteration": iteration,
                "wins": wins,
                "winrate": wins / self.m if self.m > 0 else 0,
            }
        }
        self.logs.append(entry)


    def save_logs(self, filename: Path = None):
        if not self.logging or not self.logs:
            return

        # Base folder is always logs/YYYY-MM-DD
        folder = Path("logs") / datetime.now(timezone.utc).strftime("%Y-%m-%d")
        folder.mkdir(parents=True, exist_ok=True)

        if filename is None:
            # If self.logging is True, use timestamp + default name
            # If self.logging is a string, use that as the filename (with .json)
            if self.logging is True:
                timestamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
                filename = folder / f"random_search_{timestamp}.json"
            elif isinstance(self.logging, str):
                # Use self.logging as filename (add .json if missing)
                if not self.logging.lower().endswith(".json"):
                    filename = folder / f"{self.logging}.json"
                else:
                    filename = folder / self.logging
            else:
                # fallback filename
                timestamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
                filename = folder / f"random_search_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)

        print(f"[LOG] Saved optimization logs to {filename}")

    def optimize(self, num_iterations: int):
        self.initialize_pool()
        self.start_time = time.time()

        for iteration in range(1, num_iterations + 1):
            print(f"Iteration {iteration}/{num_iterations}")

            scores = []

            for idx, team in enumerate(self.pool):
                opponents = random.sample([t for i, t in enumerate(self.pool) if i != idx], self.m)
                wins = self.evaluate_team(team, opponents)
                self.total_battles_used += self.m  # accumulate total battles
                scores.append((wins, team))
                # print(f" Team {idx} scored {wins} wins")

                self.log_entry(iteration, team, wins)

            scores.sort(key=lambda x: x[0], reverse=True)

            top_teams = [team for _, team in scores[:self.m]]
            print(f"Top {self.m} teams selected with scores: {[score for score, _ in scores[:self.m]]}")

            new_teams = [self.sample_random_team() for _ in range(self.N - self.m)]
            self.pool = top_teams + new_teams

        self.save_logs()

        return scores[:self.m]


if __name__ == "__main__":
    # Example usage
    tier = "OU"  # "Uber", "OU", "UU", "NU", "PU", "ZU", "LC"
    learnsets_file = Path(f"data/learnsets_by_tier/learnsets_{tier.lower()}.json")
    battle_format = get_format(tier)
    N = 5  # pool size
    m = 2  # top teams to keep
    num_iterations = 5

    optimizer = RandomSearchOptimizer(learnsets_file, battle_format, N, m, logging=False)
    top_results = optimizer.optimize(num_iterations)

    print("\nFinal Top Teams:")
    for score, team in top_results:
        print(f"Score: {score}")
        print(build_team_summary(*team))

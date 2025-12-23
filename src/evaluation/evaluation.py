import json
from pathlib import Path
from typing import List, Tuple, Dict
from plotting.loader import load_run_log_file


from config import get_engine, get_format

Team = Tuple[List[int], List[List[int]]]

def load_parsed_teams_json(filename="parsed_teams.json") -> List[Team]:
    script_dir = Path(__file__).parent / "gen1ou"
    file_path = script_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Parsed teams JSON file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        teams = json.load(f)
    return teams

# Load opponents once here
opponents: Dict[str, List[Team]] = {
    "OU": load_parsed_teams_json(),
    # other tiers ...
}

def evaluate(team: Team, engine: str, tier: str) -> float:
    if tier not in opponents or not opponents[tier]:
        raise Exception(f"No pool of opponents available for tier {tier}")

    battle_func = get_engine(engine)
    battle_format = get_format(tier)

    count = 0
    wins = 0
    losses = 0
    timeouts = 0
    total = len(opponents[tier])

    for opp_team in opponents[tier]:
        count += 1
        # Assuming battle_func returns 1 if team wins, else 0
        print(f"Evaluating against opponent {count} out of {total} opponents...")
        result = battle_func(team, opp_team, battle_format)
        if result == 1:
            wins += 1
        if result == 2:
            losses += 1
        else:
            timeouts +=1

    return wins, losses, timeouts, total




def evaluate_run(engine: str, tier: str, log: str):
    """
    For each training log file in logs/log/, evaluate the best team per
    generation and write EVALUATION_<filename>.json
    """
    log_path = Path("logs") / log

    if not log_path.exists():
        raise RuntimeError(f"Log path does not exist: {log_path}")

    print(f"Evaluating runs in {log_path}")

    for train_log in log_path.glob("*.json"):
        if train_log.name.startswith("EVALUATION_"):
            continue

        print(f"  Evaluating {train_log.name}")

        # --------------------------------------------------
        # Load run
        # --------------------------------------------------
        run = load_run_log_file(train_log)
        # run.best_per_generation() -> list[Entry]

        eval_entries = []

        for entry in run.best_per_generation():
            wins, losses, timeouts, total = evaluate(
                team=entry.team,
                engine=engine,
                tier=tier,
            )

            eval_entries.append({
                "generation": entry.generation,
                "score": entry.score,
                "wins": wins,
                "losses": losses,
                "timeouts": timeouts,
                "total": total,
                "win_rate": wins / total,
            })

        # --------------------------------------------------
        # Write evaluation log
        # --------------------------------------------------
        out_file = train_log.with_name(
            f"EVALUATION_{train_log.name}"
        )

        with open(out_file, "w") as f:
            json.dump(eval_entries, f, indent=2)

        print(f"    → wrote {out_file.name}")



if __name__ == "__main__":
    test_team = (
        [65, 103, 143, 135, 128, 145],
        [[94, 69, 86, 105], [79, 94, 78, 153], [34, 89, 63, 120], [24, 42, 85, 86], [59, 34, 89, 63], [65, 86, 85, 87]]
    )
    winrate = evaluate(test_team, "poke-env", "OU")
    print(f"Winrate: {winrate}")

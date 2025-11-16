# bo/objective.py
import asyncio
import uuid
import json
import logging
from pathlib import Path

from poke_env.player import MaxBasePowerPlayer as PLAYER_CLASS
from poke_env.ps_client.server_configuration import LocalhostServerConfiguration


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OPP_PATH = DATA_DIR / "opponent_teams.json"

# Load opponents once
def load_opponent_teams():
    with open(OPP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

OPPONENTS = load_opponent_teams()

SERVER = LocalhostServerConfiguration


# ============================================================
# Battle helpers
# ============================================================

async def _battle_once(team_str: str, opponent_team_str: str) -> int:
    player = PLAYER_CLASS(
        battle_format="gen1ubers",
        server_configuration=SERVER,
        team=team_str,
        max_concurrent_battles=1,
    )
    opponent = PLAYER_CLASS(
        battle_format="gen1ubers",
        server_configuration=SERVER,
        team=opponent_team_str,
        max_concurrent_battles=1,
    )

    # Suppress verbose warnings from poke-env
    player.logger.setLevel(logging.ERROR)
    opponent.logger.setLevel(logging.ERROR)

    # Unique usernames
    player._username = f"p_{uuid.uuid4().hex[:6]}"
    opponent._username = f"o_{uuid.uuid4().hex[:6]}"

    try:
        await player.battle_against(opponent, n_battles=1)
        result = 1 if player.n_won_battles > 0 else 0
    finally:
        # *** CRITICAL FIX ***
        try:
            await player.ps_client.close()
        except:
            pass
        try:
            await opponent.ps_client.close()
        except:
            pass

        # Avoid room reuse
        await asyncio.sleep(0.05)

    return result


async def evaluate_team_async(team_str: str, n_battles_per_opponent: int = 1) -> float:
    """Evaluate team against each opponent with real battles."""
    wins = 0
    total = 0

    for opp in OPPONENTS:
        opp_team = opp["team"]
        for _ in range(n_battles_per_opponent):
            w = await _battle_once(team_str, opp_team)
            wins += w
            total += 1

    return wins / total if total else 0.0


def evaluate_team(team_str: str, n_battles_per_opponent: int = 1) -> float:
    """Synchronous wrapper for full battle evaluation."""
    return asyncio.run(evaluate_team_async(team_str, n_battles_per_opponent))
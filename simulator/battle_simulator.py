# simulator/battle_simulator.py
import asyncio
import uuid
import json
import logging
import gc
from pathlib import Path

from poke_env.player import SimpleHeuristicsPlayer as PLAYER_CLASS

from poke_env.ps_client.server_configuration import LocalhostServerConfiguration


# ============================================================
# Data
# ============================================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OPP_PATH = DATA_DIR / "opponent_teams.json"

def load_opponent_teams():
    with open(OPP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

OPPONENTS = load_opponent_teams()

SERVER = LocalhostServerConfiguration

class IgnoreLightScreenWarning(logging.Filter):
    def filter(self, record):
        return "Unexpected effect" not in record.getMessage()

logging.getLogger("poke_env").addFilter(IgnoreLightScreenWarning())


# ============================================================
# Battle helpers
# ============================================================

class BattleRunner:
    def __init__(self):
        self.loop = asyncio.get_event_loop_policy().new_event_loop()

    async def _battle_once(self, team_str: str, opponent_team_str: str) -> int:
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

        player.logger.setLevel(logging.ERROR)
        opponent.logger.setLevel(logging.ERROR)

        player._username = f"p_{uuid.uuid4().hex[:6]}"
        opponent._username = f"o_{uuid.uuid4().hex[:6]}"

        try:
            await asyncio.wait_for(player.battle_against(opponent, n_battles=1), timeout=60)
            win = 1 if player.n_won_battles > 0 else 0
        except asyncio.TimeoutError:
            logging.error("Battle timed out")
            win = 0
        except Exception as e:
            logging.error(f"Unexpected error during battle: {e}")
            win = 0
        finally:
            # Disconnect players and close websockets
            await player.ps_client.stop_listening()
            await opponent.ps_client.stop_listening()
            
            await asyncio.sleep(0.1)
            gc.collect()

        return win

    async def evaluate_team_async(self, team_str: str, n_battles_per_opponent: int = 1) -> float:
        """Evaluate team against all opponents sequentially."""
        wins = 0
        total = 0

        for opp in OPPONENTS:
            opp_team = opp["team"]
            for _ in range(n_battles_per_opponent):
                w = await self._battle_once(team_str, opp_team)
                wins += w
                total += 1

        return wins / total if total > 0 else 0.0

    def run_evaluation(self, team_str: str, n_battles_per_opponent: int = 1) -> float:
        asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(
            self.evaluate_team_async(team_str, n_battles_per_opponent)
        )



# ============================================================
# Synchronous API (safe for BO)
# ============================================================

_runner = BattleRunner()

def evaluate_team(team_str: str, n_battles_per_opponent: int = 1) -> float:
    """
    Public entrypoint for the BO pipeline.
    Safe for long runs and no parallelization.
    """
    return _runner.run_evaluation(team_str, n_battles_per_opponent)

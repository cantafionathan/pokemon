# battle_engine/battle_simulator.py
import asyncio
import uuid
import json
import logging
import gc
from pathlib import Path

from poke_env.player import SimpleHeuristicsPlayer as PLAYER_CLASS
from poke_env.ps_client.server_configuration import LocalhostServerConfiguration
from config import DATA_DIR, get_format


# ============================================================
# Helpers
# ============================================================

def ensure_ability_none(team_text: str) -> str:
    """
    Parses a team string and ensures every Pokémon block has 'Ability: None'.
    This is often required for Gen 1 simulations to prevent parser warnings 
    or defaults.
    """
    if not team_text:
        return team_text

    # Split into Pokémon blocks (separated by blank lines)
    mons = team_text.strip().split("\n\n")
    new_blocks = []

    for mon in mons:
        lines = mon.strip().splitlines()
        if not lines:
            continue
        
        # Check if "Ability:" is already present (case-insensitive)
        has_ability = any(line.lower().startswith("ability:") for line in lines)
        
        if not has_ability:
            # Insert at index 1 (after the Name/Item line)
            # If the list only has 1 line, this effectively appends it.
            lines.insert(1, "Ability: None")
        
        new_blocks.append("\n".join(lines))

    return "\n\n".join(new_blocks)


# ============================================================
# Data
# ============================================================

OPP_PATH = DATA_DIR() / "opponent_teams.json"

def load_opponent_teams():
    with open(OPP_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Pre-process opponent teams to ensure they have Ability: None
    for entry in data:
        entry["team"] = ensure_ability_none(entry["team"])
        
    return data

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
        fmt = get_format()
        
        player = PLAYER_CLASS(
            battle_format=fmt,
            server_configuration=SERVER,
            team=team_str,
            max_concurrent_battles=1,
        )
        opponent = PLAYER_CLASS(
            battle_format=fmt,
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
        
        # Ensure the player team has Ability: None before starting battles
        safe_team_str = ensure_ability_none(team_str)
        
        wins = 0
        total = 0

        for opp in OPPONENTS:
            # Opponent teams are already sanitized in load_opponent_teams
            opp_team = opp["team"]
            
            for _ in range(n_battles_per_opponent):
                w = await self._battle_once(safe_team_str, opp_team)
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
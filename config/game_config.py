# config/game_config.py

from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class GameConfig:
    generation: int = 1           # 1, 2, 3, ...
    format: str = "ou"            # "ou", "ubers", etc.

    def gen_dir(self) -> Path:
        return ROOT / "data" / f"gen{self.generation}"

    def format_dir(self) -> Path:
        return self.gen_dir() / self.format

    def data_file(self, name: str) -> Path:
        """
        Get a generation-specific (global) file, e.g.
        type_chart.json, move_list.csv, pokemon_stats.csv
        """
        return self.gen_dir() / name

    def format_file(self, name: str) -> Path:
        """
        Get a format-specific file:
         - banned_moves.json
         - opponent_teams.json
         - item_rules.json (for later gens)
        """
        return self.format_dir() / name

# battle_engine/engine/damage.py
import random

TYPE_CHART = {
  "normal": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 1.0,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 1.0,
    "flying": 1.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 0.5,
    "ghost": 0.0,
    "dragon": 1.0
  },
  "fire": {
    "normal": 1.0,
    "fire": 0.5,
    "water": 0.5,
    "electric": 1.0,
    "grass": 2.0,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 1.0,
    "flying": 1.0,
    "psychic": 1.0,
    "bug": 2.0,
    "rock": 0.5,
    "ghost": 1.0,
    "dragon": 0.5
  },
  "water": {
    "normal": 1.0,
    "fire": 2.0,
    "water": 0.5,
    "electric": 1.0,
    "grass": 0.5,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 2.0,
    "flying": 1.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 2.0,
    "ghost": 1.0,
    "dragon": 0.5
  },
  "electric": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 2.0,
    "electric": 0.5,
    "grass": 0.5,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 0.0,
    "flying": 2.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 1.0,
    "ghost": 1.0,
    "dragon": 0.5
  },
  "grass": {
    "normal": 1.0,
    "fire": 0.5,
    "water": 2.0,
    "electric": 1.0,
    "grass": 0.5,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 0.5,
    "ground": 2.0,
    "flying": 0.5,
    "psychic": 1.0,
    "bug": 0.5,
    "rock": 2.0,
    "ghost": 1.0,
    "dragon": 0.5
  },
  "ice": {
    "normal": 1.0,
    "fire": 0.5,
    "water": 0.5,
    "electric": 1.0,
    "grass": 2.0,
    "ice": 0.5,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 2.0,
    "flying": 2.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 1.0,
    "ghost": 1.0,
    "dragon": 2.0
  },
  "fighting": {
    "normal": 2.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 1.0,
    "ice": 2.0,
    "fighting": 1.0,
    "poison": 0.5,
    "ground": 1.0,
    "flying": 0.5,
    "psychic": 0.5,
    "bug": 0.5,
    "rock": 2.0,
    "ghost": 0.0,
    "dragon": 1.0
  },
  "poison": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 2.0,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 0.5,
    "ground": 0.5,
    "flying": 1.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 0.5,
    "ghost": 0.5,
    "dragon": 1.0
  },
  "ground": {
    "normal": 1.0,
    "fire": 2.0,
    "water": 1.0,
    "electric": 2.0,
    "grass": 0.5,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 2.0,
    "ground": 1.0,
    "flying": 0.0,
    "psychic": 1.0,
    "bug": 0.5,
    "rock": 2.0,
    "ghost": 1.0,
    "dragon": 1.0
  },
  "flying": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 0.5,
    "grass": 2.0,
    "ice": 1.0,
    "fighting": 2.0,
    "poison": 1.0,
    "ground": 1.0,
    "flying": 1.0,
    "psychic": 1.0,
    "bug": 2.0,
    "rock": 0.5,
    "ghost": 1.0,
    "dragon": 1.0
  },
  "psychic": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 1.0,
    "ice": 1.0,
    "fighting": 2.0,
    "poison": 1.0,
    "ground": 1.0,
    "flying": 1.0,
    "psychic": 0.5,
    "bug": 1.0,
    "rock": 1.0,
    "ghost": 1.0,
    "dragon": 1.0
  },
  "bug": {
    "normal": 1.0,
    "fire": 2.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 2.0,
    "ice": 1.0,
    "fighting": 0.5,
    "poison": 2.0,
    "ground": 1.0,
    "flying": 0.5,
    "psychic": 2.0,
    "bug": 1.0,
    "rock": 2.0,
    "ghost": 1.0,
    "dragon": 1.0
  },
  "rock": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 1.0,
    "ice": 2.0,
    "fighting": 0.5,
    "poison": 1.0,
    "ground": 0.5,
    "flying": 2.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 1.0,
    "ghost": 1.0,
    "dragon": 1.0
  },
  "ghost": {
    "normal": 0.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 1.0,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 1.0,
    "flying": 1.0,
    "psychic": 0.0,
    "bug": 1.0,
    "rock": 1.0,
    "ghost": 2.0,
    "dragon": 1.0
  },
  "dragon": {
    "normal": 1.0,
    "fire": 1.0,
    "water": 1.0,
    "electric": 1.0,
    "grass": 1.0,
    "ice": 1.0,
    "fighting": 1.0,
    "poison": 1.0,
    "ground": 1.0,
    "flying": 1.0,
    "psychic": 1.0,
    "bug": 1.0,
    "rock": 1.0,
    "ghost": 1.0,
    "dragon": 2.0
  }
}

DAMAGE_CATEGORIES = {
  "normal": "Physical",
  "fire": "Special",
  "water": "Special",
  "electric": "Special",
  "grass": "Special",
  "ice": "Special",
  "fighting": "Physical",
  "poison": "Physical",
  "ground": "Physical",
  "flying": "Physical",
  "psychic": "Special",
  "bug": "Physical",
  "rock": "Physical",
  "ghost": "Physical",
  "dragon": "Special"
}

def get_type_multiplier(move_type: str, defender_types: list[str]) -> float:
    """
    Calculate Gen 1 type effectiveness multiplier.

    Args:
        move_type: Attacking move's type (e.g. "Fire").
        defender_types: List or tuple of one or two defending Pokémon types.
        type_chart: Nested dict of type multipliers (attacking_type -> defending_type -> multiplier).

    Returns:
        Multiplier as a float (e.g., 0.5, 1.0, 2.0, 0.0).
    """

    # Defensive types can be 1 or 2 types.
    multiplier = 1.0

    for d_type in defender_types:
        # Defensive type must exist in chart; fallback to 1.0 if unknown
        type_eff = TYPE_CHART.get(move_type, {}).get(d_type, 1.0)
        multiplier *= type_eff

    return multiplier


def calculate_gen1_damage(base_power, move_type, user, target, critical=False, type_multiplier=1.0):
    """
    Simplified Gen1-style damage:
      damage = floor(((Level * 2 / 5 + 2) * Power * A / D) / 50) + 2
    This function uses user's atk and target's def (physical). For special moves you'll
    want to use special stat (spa) in Gen1 (single Special stat).
    """
    L = user.level
    A = user.get_modified_stat("atk")
    D = target.get_modified_stat("def")

    # Basic formula
    dmg = (((2 * L) / 5 + 2) * base_power * A / D) / 50 + 2

    # Random variance (Gen1: 217..255 / 255). We'll use 0.85..1.00 approximation.
    multiplier = random.uniform(0.85, 1.0)
    dmg = int(dmg * multiplier)

    # STAB and type effectiveness should be applied externally or added here.
    return max(1, dmg)

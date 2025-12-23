# config.py
from typing import Callable

import poke_env_engine.battle_simulator


# Define formats for each tier or category
FORMATS = {
    "LC": "gen1lc",
    "ZU": "gen1uu",
    "PU": "gen1uu",
    "NU": "gen1uu",
    "UU": "gen1uu",
    "OU": "gen1ou",
    "Uber": "gen1ubers",
}

# Default format if tier not found
DEFAULT_FORMAT = "gen1ou"


# Define battle functions for each engine
ENGINES: dict[str, Callable] = {
    "poke-env": poke_env_engine.battle_simulator.battle_once,
}

DEFAULT_ENGINE: Callable = poke_env_engine.battle_simulator.battle_once


def get_format(tier: str) -> str:
    """
    Returns the battle format string based on the tier.
    """
    return FORMATS.get(tier, DEFAULT_FORMAT)


def get_engine(engine: str) -> Callable:
    """
    Returns the battle function based on the engine name.
    """
    return ENGINES.get(engine, DEFAULT_ENGINE)

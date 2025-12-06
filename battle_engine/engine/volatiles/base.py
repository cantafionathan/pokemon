# battle_engine/engine/volatiles/base.py

from dataclasses import dataclass

@dataclass
class VolatileEffect:
    """
    Base class for volatile effects.
    Each effect must have a unique string name.
    """
    name: str
    duration: int | None = None  # optional, many Gen1 effects don’t use duration

    def on_apply(self, pokemon, battle): pass
    def on_before_move(self, pokemon, battle): pass
    def on_after_move(self, pokemon, battle): pass
    def on_end_turn(self, pokemon, battle): pass
    def on_remove(self, pokemon, battle): pass


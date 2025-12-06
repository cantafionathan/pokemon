# battle_engine/engine/volatiles/confusion.py
from random import randint
from .base import VolatileEffect

class Confusion(VolatileEffect):
    name = "Confusion"

    def __init__(self, duration=None):
        self.duration = duration or randint(2,5)

    def on_before_move(self, pokemon, battle):
        self.duration -= 1

        # 50% chance to hit self
        if randint(0,1) == 0:
            damage = battle.calc_confusion_damage(pokemon)
            pokemon.take_damage(damage)
            return "confused_hit_self"   # tells the battle engine to skip the move

        if self.duration <= 0:
            pokemon.remove_volatile("Confusion")

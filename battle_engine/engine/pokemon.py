# battle_engine/engine/pokemon.py

from math import floor
from battle_engine.engine.status import Status

def calc_stat(base, level, is_hp=False):
    if is_hp:
        return floor(((2 * base) * level) / 100) + level + 10
    return floor(((2 * base) * level) / 100) + 5

class Pokemon:
    def __init__(self, species, level, base_stats, moves=None):
        self.species = species
        self.types = []
        self.level = level
        self.base_stats = base_stats

        self.stats = {
            "HP": calc_stat(base_stats["HP"], level, True),
            "ATK": calc_stat(base_stats["ATK"], level),
            "DEF": calc_stat(base_stats["DEF"], level),
            "SPC": calc_stat(base_stats["SPC"], level),
            "SPE": calc_stat(base_stats["SPE"], level),
        }

        self.current_hp = self.stats["HP"]

        # Stat stages -6..+6
        self.stages = {k: 0 for k in ("ATK","DEF","SPC","SPE", "ACC", "EVA")}

        # Major status (BRN, PSN, PAR, SLP, FRZ, TOX)
        self.status: Status | None = None

        # Volatile effects (confusion, leech_seed, rage, trapped, bide, etc.)
        self.volatiles = {} # key: str name, value: VolatileEffect instance

        self.moves = moves or {} # key: str name, value: Move instance

    # ------------------------------
    # Stat modification
    # ------------------------------
    def get_modified_stat(self, stat):
        stage = self.stages.get(stat, 0)
        multipliers = {
            -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
             0: 2/2,
             1: 3/2,  2: 4/2,  3: 5/2,  4: 6/2,  5: 7/2,  6: 8/2,
        }
        return int(self.stats[stat] * multipliers[stage])

    def change_stat_stage(self, stat, delta):
        self.stages[stat] = max(-6, min(6, self.stages[stat] + delta))

    # ------------------------------
    # HP / Damage
    # ------------------------------
    def take_damage(self, amount):
        self.current_hp = max(self.current_hp - int(amount), 0)
        if self.current_hp == 0:
            self.faint()

    # ------------------------------
    # Status
    # ------------------------------
    def apply_status(self, condition, counter=None):
        self.status = Status(condition, counter)

    # ------------------------------
    # Volatile Effects
    # ------------------------------
    def add_volatile(self, effect):
        self.volatiles[effect.name] = effect

    def get_volatile(self, name):
        return self.volatiles.get(name, None)

    def remove_volatile(self, name):
        self.volatiles.pop(name, None)

    def has_volatile(self, name):
        return name in self.volatiles

    # ------------------------------
    # Fainting
    # ------------------------------
    def faint(self):
        # TODO: battle logic reacts to faint
        pass

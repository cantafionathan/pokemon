# battle_engine/engine/moves/pound.py

from .base import Move

class Pound(Move):
    def __init__(self):
        super().__init__(id=1)

    def execute(self, battle, user, target):
        if not self.can_use():
            return False

        self.take_pp()

        if not self.roll_hit(user, target):
            return {
                "hit": False,
                "damage": 0,
                "critical": False,
                "ko": target.current_hp == 0,
            }

        crit = self.roll_crit(user)

        # Calculate type effectiveness multiplier
        type_multiplier = self.type_multiplier(target)

        damage = self.calculate_damage(battle, user, target, crit, type_multiplier)

        target.take_damage(damage)

        return {
            "hit": True,
            "damage": damage,
            "critical": crit,
            "ko": target.current_hp == 0,
        }

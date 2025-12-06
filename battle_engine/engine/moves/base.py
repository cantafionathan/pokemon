# battle_engine/engine/moves/base.py
import csv
from pathlib import Path
from random import randint
from engine.damage import calculate_gen1_damage, get_type_multiplier
from dataclasses import dataclass

@dataclass
class Move:
    """
    Generic Move base class. Subclasses override `execute` for special behavior.
    """
    _move_data = None

    @classmethod
    def _load_moveset(cls):
        if cls._move_data is not None:
            return  # already loaded

        cls._move_data = {}
        path = Path("data/gen1/moveset.csv")
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                move_id = int(row["id"])
                cls._move_data[move_id] = row

    def __init__(self, id, name=None, type_=None, power=None, pp=None, accuracy=None, priority=None):
        self._load_moveset()

        if name is None or type_ is None or power is None or pp is None or accuracy is None:
            # Load from CSV if any of these are missing
            data = self._move_data.get(int(id))
            if not data:
                raise ValueError(f"Move data for id {id} not found")

            name = data["name"]
            type_ = data["type"]
            power = int(data["power"]) if data["power"].isdigit() else 0
            pp = int(data["pp"]) if data["pp"].isdigit() else 15
            accuracy = float(data["accuracy"]) if data["accuracy"].isdigit() else 100
            try:
                priority = int(data["priority"])
            except (ValueError, TypeError):
                priority = 0

        self.id = int(id)
        self.name = name
        self.type = type_
        self.power = power
        self.max_pp = int(pp)
        self.current_pp = int(pp)
        self.accuracy = accuracy
        self.priority = priority

    # -------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------
    def can_use(self):
        return self.current_pp > 0

    def take_pp(self):
        if self.current_pp > 0:
            self.current_pp -= 1

    def roll_hit(self, user, target):
        """
        Gen 1 accuracy calculation:

        Accuracy is a 1–255 byte value, calculated as:
        accuracy_byte = ceil(accuracy% * 255 / 100)

        Then modified by user's ACC and target's EVA stages.

        Returns True if the move hits.
        """

        multipliers = {
            -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
            0: 2/2,
            1: 3/2,  2: 4/2,  3: 5/2,  4: 6/2,  5: 7/2,  6: 8/2,
        }

        # Calculate accuracy byte with ceiling rounding to avoid off-by-1 errors
        accuracy_byte = (int(self.accuracy * 255) + 99) // 100

        acc_mult = multipliers[user.stages.get("ACC", 0)]
        eva_mult = multipliers[target.stages.get("EVA", 0)]

        # Compute final accuracy value
        final_acc = (accuracy_byte * acc_mult) / eva_mult
        final_acc = int(min(max(final_acc, 1), 255))  # Clamp 1 to 255

        # Roll a random integer from 0 to 255 inclusive
        roll = randint(0, 255)

        return roll < final_acc


    def roll_crit(self, user):
        """
        Gen 1 crit chance calculation.

        Base crit chance = floor(Speed / 2)

        Focus Energy bug quarters the crit chance instead of doubling it.

        High crit moves double the base chance before Focus Energy bug.

        Returns True if critical hit occurs.
        """

        HIGH_CRIT_MOVES = {163, 75, 2, 152}  # slash, razor leaf, karate chop, crabhammer

        base_speed = user.base_stats.get("SPE", 0)

        crit_chance = base_speed // 2  # Base crit chance out of 256

        if self.id in HIGH_CRIT_MOVES:
            # Double base chance before Focus Energy bug
            crit_chance = min(base_speed, 255)

        if user.has_volatile("FOCUS ENERGY"):
            # Bug: quarter crit chance instead of doubling
            crit_chance = crit_chance // 4

        crit_chance = min(crit_chance, 255)

        roll = randint(0, 255)

        return roll < crit_chance
    
    def type_multiplier(self, target):
        return get_type_multiplier(self.type, target.types)

    def calculate_damage(self, battle, user, target, crit=False, type_multiplier=1.0):
        if self.power is None:
            return 0
        return calculate_gen1_damage(self.power, self.type, user, target, crit, type_multiplier)


    def execute(self, battle, user, target):
        # implemented by each move subclass
        pass
       

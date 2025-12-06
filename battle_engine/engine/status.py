# battle_engine/engine/status.py

class Status:
    """
    Major non-volatile status: BRN, PAR, SLP, FRZ, PSN, TOX
    counter = e.g. sleep counter or toxic stage
    """
    def __init__(self, condition=None, counter=None):
        self.condition = condition  # 'BRN', 'PAR', ...
        self.counter = counter

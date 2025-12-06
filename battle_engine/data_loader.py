# battle_engine/engine/data_loader.py

from config.game_config import GameConfig
import json
import csv

class LegalBattleData:
    def __init__(self, mons, moves, learnsets, type_chart, rules):
        self.mons = mons
        self.moves = moves
        self.learnsets = learnsets
        self.type_chart = type_chart
        self.rules = rules


def load_battle_data(cfg: GameConfig) -> LegalBattleData:
    # === Load generation-level data ===
    pokemon = load_csv(cfg.data_file("pokemon.csv"))
    moves = load_csv(cfg.data_file("moves.csv"))
    learnsets = load_json(cfg.data_file("learnsets.json"))
    type_chart = load_csv(cfg.data_file("type_chart.csv"))
    mechanics = load_json(cfg.data_file("mechanics.json"))
    
    # === Load format-level rules ===
    banned_moves = load_json(cfg.format_file("banned_moves.json"))
    banned_mons = load_json(cfg.format_file("banned_mons.json"))
    clauses = load_json(cfg.format_file("clauses.json"))

    # === Filter mons ===
    legal_mons = {
        name: mon 
        for name, mon in pokemon.items()
        if name not in banned_mons
    }

    # === Filter learnsets ===
    legal_learnsets = {}
    for mon, ms in learnsets.items():
        if mon not in legal_mons:
            continue
        legal_learnsets[mon] = [m for m in ms if m not in banned_moves]

    # === Filter moves ===
    legal_moves = {m: d for m, d in moves.items() if m not in banned_moves}

    return LegalBattleData(
        mons=legal_mons,
        moves=legal_moves,
        learnsets=legal_learnsets,
        type_chart=type_chart,
        rules=clauses
    )

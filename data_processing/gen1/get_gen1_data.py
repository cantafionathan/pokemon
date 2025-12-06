# data_processing/gen1/get_gen1_data.py
"""
Run the full Gen1 data pipeline:
 - fetch pokedex -> data/gen1/pokedex.json
 - fetch moves + valid moves -> data/gen1/{ou,ubers}/...
 - parse raw teams -> data/gen1/{ou,ubers}/opponent_teams.json
"""

from data_processing.gen1.get_pokedex import main as get_pokedex
from data_processing.gen1.get_movelist import main as get_movelist
from data_processing.gen1.get_learnsets import main as get_learnsets
from data_processing.gen1.parse_teams import main as parse_teams
from data_processing.gen1.get_static_gen1_files import main as get_static_files

if __name__ == "__main__":
    get_pokedex()
    get_movelist()
    get_learnsets()
    parse_teams()
    get_static_files()

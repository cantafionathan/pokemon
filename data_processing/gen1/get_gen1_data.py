# data_processing/gen1/get_gen1_data.py
"""
Run the full Gen1 data pipeline:
 - fetch pokedex -> data/gen1/pokedex.json
 - fetch moves + valid moves -> data/gen1/{ou,ubers}/...
 - parse raw teams -> data/gen1/{ou,ubers}/opponent_teams.json
"""

from data_processing.gen1.get_pokedex import main as get_pokedex
from data_processing.gen1.scrape_moves import main as scrape_moves
from data_processing.gen1.parse_teams import main as parse_teams

if __name__ == "__main__":
    get_pokedex(gen=1)
    scrape_moves(gen=1)
    parse_teams(gen=1)

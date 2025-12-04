from parse_teams import main as parse_teams
from reduce_embeddings import main as reduce_embeddings
from scrape_moves import main as scrape_moves
from scrape_competitive_movesets import main as scrape_competitive_movesets

if __name__ == "__main__":
    scrape_moves()
    parse_teams()
    reduce_embeddings()
    scrape_competitive_movesets()
import re
import json
from pathlib import Path
from utils import normalize_name, parse_movelist, load_pokedex_from_tiers, build_team_summary, MOVELIST_CSV

def parse_teams(text: str):
    # Load pokedex and movelist from utils functions
    pokedex = load_pokedex_from_tiers()
    movelist = {v: k for k, v in parse_movelist(MOVELIST_CSV).items()}  # reverse move_id->name to name->id
    poke_name_to_id = {v: k for k, v in pokedex.items()}

    teams = []
    current_team_pokes = []
    current_team_moves = []

    lines = text.splitlines()

    poke_re = re.compile(r"^[A-Za-z\-\s]+$")
    move_re = re.compile(r"^- (.+)$")

    for line in lines:
        line = line.strip()
        if line.startswith("==="):
            if current_team_pokes and current_team_moves:
                teams.append((current_team_pokes, current_team_moves))
            current_team_pokes = []
            current_team_moves = []
            continue

        if not line:
            continue

        if poke_re.match(line) and not line.startswith("-"):
            poke_name = normalize_name(line)
            poke_id = poke_name_to_id.get(poke_name)
            if poke_id is None:
                print(f"Warning: Unknown Pokémon '{poke_name}'")
                poke_id = -1
            current_team_pokes.append(poke_id)
            current_team_moves.append([])
            continue

        move_match = move_re.match(line)
        if move_match:
            move_name = normalize_name(move_match.group(1))
            move_id = movelist.get(move_name)
            if move_id is None:
                print(f"Warning: Unknown move '{move_name}'")
                move_id = -1
            current_team_moves[-1].append(move_id)

    if current_team_pokes and current_team_moves:
        teams.append((current_team_pokes, current_team_moves))

    return teams

def save_parsed_teams(teams, filename="parsed_teams.json"):
    script_dir = Path(__file__).parent
    output_file = script_dir / filename

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(teams, f, indent=2)

    print(f"Saved parsed teams to {output_file}")

def parse_gen1ou_teams():
    script_dir = Path(__file__).parent
    teams_file = script_dir / "teams.txt"

    if not teams_file.exists():
        print(f"Error: {teams_file} does not exist!")
        exit(1)

    teams_text = teams_file.read_text(encoding="utf-8")

    teams = parse_teams(teams_text)

    save_parsed_teams(teams)  # save to parsed_teams.json by default

    return teams

    

if __name__ == "__main__":
    teams = parse_gen1ou_teams()

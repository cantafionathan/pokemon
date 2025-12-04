# parse_teams.py

import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"

RAW_PATH = DATA_DIR / "raw_teams.txt"

FORMAT_DIRS = {
    "gen1ou": DATA_DIR / "gen1ou",
    "gen1ubers": DATA_DIR / "gen1ubers"
}

TEAM_HEADER = re.compile(
    r"^=== \[(?P<format>[^\]]+)\] (?P<name>.+) ===$",
    re.MULTILINE
)

MOVE_LINE = re.compile(r"^- (.+)$")


def normalize_move_name(move_name: str) -> str:
    """Convert hyphenated move names like 'Soft-Boiled' → 'Soft Boiled'."""
    move_name = re.sub(r"(?<=\w)-(?=\w)", " ", move_name)
    return move_name.strip()


# ----------------------------------------------------
# PARSING
# ----------------------------------------------------

def parse_raw_teams(raw_text):
    matches = list(TEAM_HEADER.finditer(raw_text))
    teams = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)

        block = raw_text[start:end].strip()

        format_name = match.group("format").strip().lower()
        team_name = match.group("name").strip()

        # Pokémon sections separated by blank lines
        mons = [m.strip() for m in re.split(r"\n\s*\n", block) if m.strip()]
        mon_blocks = []

        for mon in mons:
            lines = [ln.strip() for ln in mon.splitlines() if ln.strip()]
            if not lines:
                continue

            # Normalize moves
            for j, ln in enumerate(lines):
                m = MOVE_LINE.match(ln)
                if m:
                    move = normalize_move_name(m.group(1))
                    lines[j] = f"- {move}"

            mon_blocks.append("\n".join(lines))

        team_text = "\n\n".join(mon_blocks)

        teams.append({
            "name": team_name,
            "format": format_name,  # gen1ou / gen1ubers
            "team": team_text
        })

    return teams


# ----------------------------------------------------
# ROUTING TO FORMAT DIRECTORIES
# ----------------------------------------------------

def save_teams(teams):

    # OU gets only OU-tagged teams
    ou_teams = [t for t in teams if t["format"] == "gen1ou"]

    # UBERS gets BOTH
    ubers_teams = teams[:]  # copy entire list

    # Save
    (DATA_DIR / "gen1ou").mkdir(exist_ok=True)
    (DATA_DIR / "gen1ubers").mkdir(exist_ok=True)

    (DATA_DIR / "gen1ou" / "opponent_teams.json").write_text(
        json.dumps(ou_teams, indent=2), encoding="utf-8"
    )

    (DATA_DIR / "gen1ubers" / "opponent_teams.json").write_text(
        json.dumps(ubers_teams, indent=2), encoding="utf-8"
    )

    print(f"Saved {len(ou_teams)} → data/gen1ou/opponent_teams.json")
    print(f"Saved {len(ubers_teams)} → data/gen1ubers/opponent_teams.json")


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

def main():
    raw_text = RAW_PATH.read_text(encoding="utf-8")
    teams = parse_raw_teams(raw_text)

    print(f"Parsed {len(teams)} teams total")
    save_teams(teams)


if __name__ == "__main__":
    main()
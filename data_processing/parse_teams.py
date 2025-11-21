# parse_teams.py

import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

RAW_PATH = DATA_DIR / "raw_teams.txt"
OUT_PATH = DATA_DIR / "opponent_teams.json"

TEAM_HEADER = re.compile(r"^=== \[(?P<format>[^\]]+)\] (?P<name>.+) ===$", re.MULTILINE)

# regex to find move lines like "- Soft-Boiled"
MOVE_LINE = re.compile(r"^- (.+)$")

def normalize_move_name(move_name: str) -> str:
    """Convert hyphenated move names like 'Soft-Boiled' → 'Soft Boiled'."""
    # Replace hyphens only if surrounded by letters (not numeric or punctuation cases)
    move_name = re.sub(r"(?<=\w)-(?=\w)", " ", move_name)
    return move_name.strip()

def parse_raw_teams(raw_text):
    matches = list(TEAM_HEADER.finditer(raw_text))
    teams = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        block = raw_text[start:end].strip()

        format_name = match.group("format").strip().lower()
        team_name = match.group("name").strip()

        # Split block into Pokémon sections separated by blank lines
        mons = [m.strip() for m in re.split(r"\n\s*\n", block) if m.strip()]
        mon_blocks = []

        for mon in mons:
            lines = [ln.strip() for ln in mon.splitlines() if ln.strip()]
            if not lines:
                continue

            # Insert "Ability: None" after Pokémon name if missing
            if not any(ln.lower().startswith("ability:") for ln in lines):
                lines.insert(1, "Ability: None")

            # Normalize move names
            for j, ln in enumerate(lines):
                match = MOVE_LINE.match(ln)
                if match:
                    move = match.group(1)
                    move = normalize_move_name(move)
                    lines[j] = f"- {move}"

            mon_blocks.append("\n".join(lines))

        # Join Pokémon sections with a blank line between them
        team_text = "\n\n".join(mon_blocks)

        teams.append({
            "name": team_name,
            "format": format_name,
            "team": team_text
        })

    return teams


def main():
    raw_text = RAW_PATH.read_text(encoding="utf-8")
    teams = parse_raw_teams(raw_text)
    print(f"Parsed {len(teams)} teams")
    OUT_PATH.write_text(json.dumps(teams, indent=2))
    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()

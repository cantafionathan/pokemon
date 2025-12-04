# data_processing/gen1/parse_teams.py
"""
Parse raw_teams.txt into format-specific opponent_teams.json files.

Old behavior replicated:
 - Read raw_teams.txt containing team headers of the form:
       === [gen1ou] My Team Name ===
 - Extract (format, team_text, team_name)
 - OU gets only gen1ou teams
 - Ubers gets ALL teams (OU + Ubers)
 - Output JSON files to:
       data/gen1/ou/opponent_teams.json
       data/gen1/ubers/opponent_teams.json
"""

import re
import json
from pathlib import Path
from data_processing.common.paths import data_dir

# Path to raw team file under new structure
RAW_TEAMS_PATH = Path(__file__).resolve().parents[2] / "data" / "gen1" / "raw_teams.txt"

# ----------------------------------------------------
# REGEX PATTERNS (from original implementation)
# ----------------------------------------------------

TEAM_HEADER = re.compile(
    r"^=== \[(?P<format>[^\]]+)\] (?P<name>.+) ===$",
    re.MULTILINE
)

MOVE_LINE = re.compile(r"^- (.+)$")


def normalize_move_name(move_name: str) -> str:
    """Convert hyphenated move names like 'Soft-Boiled' → 'Soft Boiled'."""
    return re.sub(r"(?<=\w)-(?=\w)", " ", move_name).strip()


# ----------------------------------------------------
# PARSE RAW TEAMS (old logic)
# ----------------------------------------------------

def parse_raw_teams(raw_text: str):
    matches = list(TEAM_HEADER.finditer(raw_text))
    teams = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)

        # Raw text for this team block
        block = raw_text[start:end].strip()

        format_name = match.group("format").strip().lower()  # gen1ou / gen1ubers
        team_name = match.group("name").strip()

        # Split into Pokémon blocks by blank lines
        mons = [m.strip() for m in re.split(r"\n\s*\n", block) if m.strip()]
        mon_blocks = []

        for mon in mons:
            lines = [ln.strip() for ln in mon.splitlines() if ln.strip()]

            # Normalize move names just like before
            for j, ln in enumerate(lines):
                m = MOVE_LINE.match(ln)
                if m:
                    fixed = normalize_move_name(m.group(1))
                    lines[j] = f"- {fixed}"

            mon_blocks.append("\n".join(lines))

        team_text = "\n\n".join(mon_blocks)

        teams.append({
            "name": team_name,
            "format": format_name,
            "team": team_text
        })

    return teams


# ----------------------------------------------------
# SAVE TEAMS (old behavior)
# ----------------------------------------------------

def save_teams(teams, gen_dir: Path):
    ou_dir = gen_dir / "ou"
    ubers_dir = gen_dir / "ubers"

    ou_dir.mkdir(parents=True, exist_ok=True)
    ubers_dir.mkdir(parents=True, exist_ok=True)

    # Old logic:
    #   - OU gets ONLY gen1ou teams
    #   - Ubers gets ALL teams
    ou_teams = [t for t in teams if t["format"] == "gen1ou"]
    ubers_teams = teams[:]  # everything

    (ou_dir / "opponent_teams.json").write_text(
        json.dumps(ou_teams, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    (ubers_dir / "opponent_teams.json").write_text(
        json.dumps(ubers_teams, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Saved {len(ou_teams)} → {ou_dir}/opponent_teams.json")
    print(f"Saved {len(ubers_teams)} → {ubers_dir}/opponent_teams.json")


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

def main(gen: int = 1):
    gen_dir = data_dir(gen)
    gen_dir.mkdir(parents=True, exist_ok=True)

    if not RAW_TEAMS_PATH.exists():
        raise FileNotFoundError(f"Missing raw teams file: {RAW_TEAMS_PATH}")

    raw_text = RAW_TEAMS_PATH.read_text(encoding="utf-8")
    teams = parse_raw_teams(raw_text)

    print(f"Parsed {len(teams)} teams")
    save_teams(teams, gen_dir)


if __name__ == "__main__":
    main()

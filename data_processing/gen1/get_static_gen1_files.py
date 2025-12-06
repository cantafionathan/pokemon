# data_processing/gen1/generate_static_gen1_files.py
"""
Generate static Gen 1 data files:
 - type_chart.json
 - ou/banned_moves.json
 - ou/banned_mons.json
 - ubers/banned_moves.json
 - ubers/banned_mons.json
"""

import json
from pathlib import Path
from data_processing.common.paths import data_dir

# OU & Ubers Rules

OU_BANNED_MONS = ["Mewtwo", "Mew"]
UBERS_BANNED_MONS = []

BANNED_MOVES = [
    "Fissure", "Horn Drill", "Guillotine",
    "Double Team", "Minimize"
]

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))
    print(f"Wrote {path}")

def main(gen: int = 1):
    base = data_dir(gen)

    # ---- OU ----
    ou_dir = base / "ou"
    write_json(ou_dir / "banned_mons.json", OU_BANNED_MONS)
    write_json(ou_dir / "banned_moves.json", BANNED_MOVES)

    # ---- Ubers ----
    ubers_dir = base / "ubers"
    write_json(ubers_dir / "banned_mons.json", UBERS_BANNED_MONS)
    write_json(ubers_dir / "banned_moves.json", BANNED_MOVES)

    print("Done.")


if __name__ == "__main__":
    main()

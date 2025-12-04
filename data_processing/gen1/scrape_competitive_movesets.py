import re
import json
import html
import time
import requests
from pathlib import Path

# ─────────────────────────────────────────────
# Formats handled by this script
# ─────────────────────────────────────────────

FORMATS = ["gen1ubers", "gen1ou"]


# ─────────────────────────────────────────────
# Utility: Normalize move names
# ─────────────────────────────────────────────

def normalize_move_name(m):
    s = m.strip().lower()
    s = s.replace("’", "").replace("‘", "").replace("'", "")
    s = s.replace(" ", "_").replace("-", "_")
    return s


# ─────────────────────────────────────────────
# HTML → JSON moveset extraction helpers
# ─────────────────────────────────────────────

def find_matching_bracket(s, start_idx):
    stack = []
    for i in range(start_idx, len(s)):
        if s[i] == "[":
            stack.append("[")
        elif s[i] == "]":
            stack.pop()
            if not stack:
                return i
    raise ValueError("No matching bracket")

def extract_all_movesets_blocks(html_text):
    blocks = []
    for m in re.finditer(r'"movesets"\s*:\s*\[', html_text):
        start = m.end() - 1
        end = find_matching_bracket(html_text, start)
        blocks.append(html_text[start:end+1])
    return blocks

def expand_moveslots(moveslots, normalized_to_original):
    from itertools import product

    slot_moves = []
    for slot in moveslots:
        slot_moves.append([
            normalize_move_name(mv["move"])
            for mv in slot if "move" in mv
        ])

    all_combos = list(product(*slot_moves))

    restored_sets = []
    for combo in all_combos:
        restored = [normalized_to_original.get(m, m) for m in combo]
        restored_sets.append(restored)

    return restored_sets


# ─────────────────────────────────────────────
# Move filtering
# ─────────────────────────────────────────────

def is_valid_moveset(pokemon_name, moveset, valid_move_dict):
    legal = {normalize_move_name(m) for m in valid_move_dict.get(pokemon_name, [])}

    for m in moveset:
        if normalize_move_name(m) not in legal:
            return False

    return True


# ─────────────────────────────────────────────
# URL slug generation
# ─────────────────────────────────────────────

def slugify(name):
    s = name.lower()
    s = re.sub(r"[.'’]", "", s)
    s = s.replace(" ", "-")
    return s


# ─────────────────────────────────────────────
# Scraping + parsing of a single Pokémon
# ─────────────────────────────────────────────

BASE_URL = "https://www.smogon.com/dex/rb/pokemon/{}/"

def scrape_pokemon_movesets(slug_name, real_name,
                            valid_move_dict,
                            normalized_to_original,
                            allowed_moves_set):

    url = BASE_URL.format(slug_name)

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        html_text = response.text
    except Exception as e:
        print(f"Failed to fetch {slug_name}: {e}")
        return []

    blocks = extract_all_movesets_blocks(html_text)
    all_movesets = []

    for block in blocks:
        try:
            movesets = json.loads(block)

            for ms in movesets:
                moveslots = ms.get("moveslots")
                if not moveslots:
                    continue

                expanded = expand_moveslots(moveslots, normalized_to_original)

                # No duplicate moves in a moveset
                expanded = [m for m in expanded if len(set(m)) == len(m)]

                # Must be legal for this Pokémon (format-specific valid_moves.json)
                expanded = [
                    m for m in expanded if is_valid_moveset(real_name, m, valid_move_dict)
                ]

                # Must be in the allowed move pool of the format (important!)
                expanded = [
                    m for m in expanded
                    if all(move in allowed_moves_set for move in m)
                ]

                all_movesets.extend(expanded)

        except Exception as e:
            print(f"Error parsing movesets for {slug_name}: {e}")

    # Deduplicate movesets (order-independent)
    unique = []
    seen = set()
    for ms in all_movesets:
        key = tuple(sorted(ms))
        if key not in seen:
            seen.add(key)
            unique.append(ms)

    return unique

def main():
    with open("data/gen1_pokedex.json") as f:
        pokedex = json.load(f)

    for fmt in FORMATS:
        fmt_dir = Path("data") / fmt
        valid_path = fmt_dir / "valid_moves.json"
        vocab_path = fmt_dir / "move_vocab.json"
        output_path = fmt_dir / "competitive_movesets.json"

        print(f"\n======================================")
        print(f"   Processing FORMAT: {fmt.upper()}")
        print(f"======================================\n")

        # Load format-specific data
        with valid_path.open() as f:
            valid_move_dict = json.load(f)

        with vocab_path.open() as f:
            move_vocab = json.load(f)

        # Allowed moves: all moves in the move vocab of this format
        allowed_moves_set = set(move_vocab)

        # Build normalization table
        normalized_to_original = {
            normalize_move_name(m): m for m in move_vocab
        }

        # Scraping begins
        all_data = {}

        for key, name in pokedex.items():
            slug = slugify(name)
            print(f"Scraping {name} → {slug}")

            movesets = scrape_pokemon_movesets(
                slug,
                name,
                valid_move_dict,
                normalized_to_original,
                allowed_moves_set,
            )

            if movesets:
                all_data[name] = movesets
                print(f"  → {len(movesets)} unique moveset(s)")
            else:
                print("  → No movesets found")

            time.sleep(0.25)

        # Save per-format output
        with output_path.open("w") as f:
            json.dump(all_data, f, indent=2)

        print(f"\nSaved {fmt.upper()} movesets → {output_path}")


# ─────────────────────────────────────────────
# Main execution
# ─────────────────────────────────────────────

if __name__ == "__main__":
    main()
   

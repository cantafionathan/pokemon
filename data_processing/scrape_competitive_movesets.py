import re
import json
import html
import time
import requests

UBERS_BANNED_MOVES = {
    "Fissure",
    "Horn Drill",
    "Guillotine",
    "Double Team",
    "Minimize",
}

with open("data/valid_moves.json") as f:
    VALID_MOVES = json.load(f)


BASE_URL = "https://www.smogon.com/dex/rb/pokemon/{}/"
OUTPUT_FILE = "data/competitive_movesets.json"
with open("data/move_vocab.json") as f:
    move_vocab_list = json.load(f)

# Build mapping normalized name -> original name
def normalize_move_name(m):
    s = m.strip().lower()
    # Remove all apostrophes, both plain and fancy
    s = s.replace("’", "").replace("‘", "").replace("'", "")
    s = s.replace(" ", "_").replace("-", "_")
    return s


normalized_to_original = {
    normalize_move_name(move): move for move in move_vocab_list
}

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

def extract_all_movesets_blocks(html):
    movesets_blocks = []
    for m in re.finditer(r'"movesets"\s*:\s*\[', html):
        start = m.end() - 1
        end = find_matching_bracket(html, start)
        block_text = html[start:end+1]
        movesets_blocks.append(block_text)
    return movesets_blocks


def parse_moveslots_json(array_text):
    cleaned = html.unescape(array_text)
    cleaned = re.sub(r",\s*([\]\}])", r"\1", cleaned)  # remove trailing commas
    return json.loads(cleaned)

def expand_moveslots(moveslots):
    from itertools import product
    slot_moves = []
    for slot in moveslots:
        slot_moves.append([normalize_move_name(mv['move']) for mv in slot if 'move' in mv])
    all_combos = list(product(*slot_moves))

    # Restore original move names with correct casing and spacing
    result = []
    for combo in all_combos:
        restored = [normalized_to_original.get(mv, mv) for mv in combo]
        result.append(restored)
    return result

def is_valid_moveset(pokemon_name, moveset):
    # Normalize the valid move names
    valid = {normalize_move_name(m) for m in VALID_MOVES.get(pokemon_name, [])}
    # Normalize all moves in the moveset
    return all(normalize_move_name(move) in valid for move in moveset)


def slugify(name):
    s = name.lower()
    s = re.sub(r"[.'’]", "", s)      # Remove dots and apostrophes
    s = s.replace(" ", "-")           # Replace spaces with dash
    return s

def scrape_pokemon_movesets(slug_name, real_name):
    url = BASE_URL.format(slug_name)
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        html_text = response.text
    except Exception as e:
        print(f"Failed to fetch {slug_name}: {e}")
        return []

    movesets_blocks = extract_all_movesets_blocks(html_text)
    all_movesets = []

    for block_text in movesets_blocks:
        try:
            movesets = json.loads(block_text)
            for moveset in movesets:
                moveslots = moveset.get("moveslots")
                if moveslots:
                    variants = expand_moveslots(moveslots)

                    # filter out any moveset with duplicates
                    variants = [
                        combo for combo in variants
                        if len(set(combo)) == len(combo)
                    ]

                    # remove combos containing moves not legal in Gen 1
                    variants = [
                        combo for combo in variants
                        if is_valid_moveset(real_name, combo)
                    ]

                    all_movesets.extend(variants)
        except Exception as e:
            print(f"Error parsing movesets for {slug_name}: {e}")


    # Filter out movesets with banned moves
    filtered_movesets = [
        ms for ms in all_movesets
        if not any(move in UBERS_BANNED_MOVES for move in ms)
    ]

    # Deduplicate ignoring order
    unique_movesets = []
    seen = set()
    for ms in filtered_movesets:
        key = tuple(sorted(ms))
        if key not in seen:
            seen.add(key)
            unique_movesets.append(ms)

    return unique_movesets


if __name__ == "__main__":
    # Load your pokedex file - assumed format: { "bulbasaur": "Bulbasaur", "ivysaur": "Ivysaur", ... }
    with open("data/gen1_pokedex.json") as f:
        pokedex = json.load(f)

    all_data = {}

    for key, name in pokedex.items():
        slug = slugify(name)
        print(f"Scraping movesets for {name} → {slug}")
        movesets = scrape_pokemon_movesets(slug, name)
        if movesets:
            all_data[name] = movesets
            print(f"  Found {len(movesets)} unique moveset(s)")
        else:
            print(f"  No movesets found")
        time.sleep(0.3)


    # Write to output file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"Saved all movesets to {OUTPUT_FILE}")

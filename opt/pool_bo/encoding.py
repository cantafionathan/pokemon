# bo/encoding.py
import json
import random
import torch
from pathlib import Path
from typing import List, Dict
from config import DATA_DIR

DEBUG_DECODE = True  # set to True manually when debugging

# ============================================================
# === CONFIG AND DATA LOADING ===
# ============================================================


POKEMON_MOVESETS_PATH = DATA_DIR() / "competitive_movesets.json"


# -----------------------------
# Load Pokémon embeddings
# -----------------------------
with open(DATA_DIR() / "pokemon_embeddings_reduced.json", "r") as f:
    POKEMON_EMBEDDINGS = {k: torch.tensor(v, dtype=torch.double) for k, v in json.load(f).items()}

EMBED_DIM = len(next(iter(POKEMON_EMBEDDINGS.values())))

FEATURE_DIM = 6 * EMBED_DIM

# -----------------------------
# Load moveset pool
# -----------------------------
with open(POKEMON_MOVESETS_PATH, "r", encoding="utf-8") as f:
    POKEMON_MOVESETS = json.load(f)

def parse_showdown_team(team_str: str) -> list[dict]:
    """
    Parses a Showdown team string into list of {species, moveset} dicts.

    Example input chunk:

    Clefable
    - Mega Kick
    - Hyper Beam
    - Blizzard
    - Sing

    Returns:
        [
          {"species": "Clefable", "moveset": ["Mega Kick", "Hyper Beam", "Blizzard", "Sing"]},
          ...
        ]
    """
    teams = []
    blocks = team_str.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        species = lines[0].strip()
        moves = [line[2:].strip() for line in lines if line.startswith("- ")]
        teams.append({"species": species, "moveset": moves})

    return teams



# ============================================================
# === BASIC HELPERS ===
# ============================================================


def normalize(v: torch.Tensor) -> torch.Tensor:
    """Normalize a vector to unit length."""
    return v / (torch.norm(v) + 1e-8)


def cosine_sim(a: torch.Tensor, b: torch.Tensor) -> float:
    """Compute cosine similarity between two vectors."""
    return torch.dot(normalize(a), normalize(b)).item()


def encode_pokemon(name: str) -> torch.Tensor:
    """Return dense embedding for a Pokémon by name."""
    return POKEMON_EMBEDDINGS.get(name, torch.zeros(EMBED_DIM))


# ============================================================
# === ENCODING HELPERS ===
# ============================================================


def encode_team(team_dict: dict) -> torch.Tensor:
    """
    Encodes a team using the 6 Pokémon embeddings.
    Moves are ignored in the encoding.
    """
    team_text = team_dict["team"]
    mons = [m.strip() for m in team_text.split("\n\n") if m.strip()]

    team_vecs = []
    for mon in mons[:6]:
        name = mon.split("\n")[0].strip()
        team_vecs.append(encode_pokemon(name))

    # pad to 6 mons if needed
    while len(team_vecs) < 6:
        team_vecs.append(torch.zeros(EMBED_DIM))

    return torch.cat(team_vecs, dim=0)



# ============================================================
# === DECODING HELPERS ===
# ============================================================


def decode_single_pokemon(vec: torch.Tensor) -> str:
    """Return the Pokémon whose embedding is most similar to `vec`."""
    vec = normalize(vec)
    best = None
    best_score = -1e9
    for name, emb in POKEMON_EMBEDDINGS.items():
        s = cosine_sim(vec, emb)
        if s > best_score:
            best_score = s
            best = name
    return best


def random_legal_moves(p: str) -> list:
    movesets = POKEMON_MOVESETS.get(p, [])
    
    try:
        ms = random.choice(movesets)
        return ms
    except IndexError:
        print(f"[ERROR] No legal movesets available for Pokémon: '{p}'")
        print(f"POKEMON_MOVESETS[{p!r}] = {movesets}")
        raise



def format_team(pokemon_moves: Dict[str, List[str]]) -> str:
    """Format Gen 1 team."""
    blocks = []
    for mon, moves in pokemon_moves.items():
        move_lines = "\n".join(f"- {m}" for m in moves)
        block = f"{mon}\n{move_lines}"
        blocks.append(block)
    return "\n\n".join(blocks)

def decode_team_pokemon_only(team_vec: torch.Tensor) -> dict:
    """
    Decode only the Pokémon names from an embedding.
    (Moves are not assigned here.)
    """
    pokemon_list = []

    for i in range(6):
        start = i * EMBED_DIM
        end = start + EMBED_DIM
        subvec = team_vec[start:end]

        name = decode_single_pokemon(subvec)
        if name is None:
            name = next(iter(POKEMON_EMBEDDINGS.keys()))
        
        # Handle ambiguous Nidoran from embedding file
        if name.lower() == "nidoran":
            name = random.choice(["Nidoran-M", "Nidoran-F"])


        pokemon_list.append(name)

    return pokemon_list


def decode_team_from_embedding(team_vec: torch.Tensor) -> dict:
    """
    Decode a team using ONLY Pokémon embeddings.
    Moves are assigned randomly from the moveset pool.
    """
    pokemon_list = decode_team_pokemon_only(team_vec)

    # assign random legal moves
    pokemon_moves = {p: random_legal_moves(p) for p in pokemon_list}

    return {
        "name": "decoded_team",
        "format": "gen1ubers",
        "team": format_team(pokemon_moves),
    }



if __name__ == "__main__":
    # quick local test
    example_team = {
        "name": "example",
        "format": "gen1ubers",
        "team": """Gengar
- Hypnosis
- Thunderbolt
- Night Shade
- Explosion

Chansey
- Ice Beam
- Thunderbolt
- Thunder Wave
- Soft Boiled

Snorlax
- Body Slam
- Earthquake
- Hyper Beam
- Self Destruct

Exeggutor
- Sleep Powder
- Stun Spore
- Psychic
- Explosion

Mr. Mime
- Body Slam

Lapras
- Blizzard
- Thunderbolt
- Body Slam
- Confuse Ray"""
    }

    vec = encode_team(example_team)
    decoded = decode_team_from_embedding(vec)
    print(decoded["team"])

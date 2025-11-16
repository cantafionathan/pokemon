# bo/encoding.py
import json
import numpy as np
import pandas as pd
import random
import torch
from pathlib import Path
from typing import List, Dict

DEBUG_DECODE = True  # set to True manually when debugging

# ============================================================
# === CONFIG AND DATA LOADING ===
# ============================================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MOVE_VOCAB_PATH = DATA_DIR / "move_vocab.json"
VALID_MOVES_PATH = DATA_DIR / "valid_moves.json"


# -----------------------------
# Load Pokémon embeddings
# -----------------------------
with open(DATA_DIR / "pokemon_embeddings_reduced.json", "r") as f:
    POKEMON_EMBEDDINGS = {k: torch.tensor(v, dtype=torch.double) for k, v in json.load(f).items()}

EMBED_DIM = len(next(iter(POKEMON_EMBEDDINGS.values())))

FEATURE_DIM = 6 * EMBED_DIM

# -----------------------------
# Load move vocabulary and valid moves
# -----------------------------
with open(MOVE_VOCAB_PATH, "r", encoding="utf-8") as f:
    MOVE_VOCAB = json.load(f)
MOVE_INDEX = {m: i for i, m in enumerate(MOVE_VOCAB)}
NUM_MOVES = len(MOVE_VOCAB)

with open(VALID_MOVES_PATH, "r", encoding="utf-8") as f:
    VALID_MOVES = json.load(f)


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
    Encodes a team using ONLY the 6 Pokémon embeddings.
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


def random_legal_moves(p: str, k=4) -> list:
    legal = VALID_MOVES.get(p, [])

    # If no legal moves at all → give one safe generic move.
    if len(legal) == 0:
        return ["Body Slam"]  # always legal in gen1

    # If 1 ≤ #legal < k → return all legal moves (1 to k moves)
    if len(legal) <= k:
        return legal[:]  # return all, no repeats

    # If many legal moves → sample k
    return random.sample(legal, k=k)

def format_team(pokemon_moves: Dict[str, List[str]]) -> str:
    """Format Gen 1 team with explicit Ability: None lines so poke-env won't crash."""
    blocks = []
    for mon, moves in pokemon_moves.items():
        move_lines = "\n".join(f"- {m}" for m in moves)
        block = f"{mon}\nAbility: None\n{move_lines}"
        blocks.append(block)
    return "\n\n".join(blocks)


def decode_team_from_embedding(team_vec: torch.Tensor) -> dict:
    """
    Decode a team using ONLY Pokémon embeddings.
    Moves are assigned randomly from the legal move list.
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

    # assign random legal moves
    pokemon_moves = {p: random_legal_moves(p, k=4) for p in pokemon_list}

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

Tauros
- Body Slam
- Earthquake
- Hyper Beam
- Blizzard

Lapras
- Blizzard
- Thunderbolt
- Body Slam
- Confuse Ray"""
    }

    vec = encode_team(example_team)
    decoded = decode_team_from_embedding(vec)
    print(decoded["team"])

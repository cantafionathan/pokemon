# save_embeddings.py

import pandas as pd
from pathlib import Path

# Paths relative to the project root (not current working directory)
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "pokemon_embeddings.parquet"

def main():
    print("Loading Pokémon embeddings from Hugging Face...")
    df = pd.read_parquet("hf://datasets/minimaxir/pokemon-embeddings/pokemon_embeddings.parquet")
    print(f"Loaded {len(df)} entries")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH)
    print(f"Saved embeddings to {OUT_PATH}")

if __name__ == "__main__":
    main()

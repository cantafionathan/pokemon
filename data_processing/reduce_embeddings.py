#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

# ============================================
# CONFIG
# ============================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
POKEMON_EMBED_PATH = DATA_DIR / "pokemon_embeddings.parquet"
POKEDEX_PATH = DATA_DIR / "gen1_pokedex.json"
OUT_JSON_PATH = DATA_DIR / "pokemon_embeddings_reduced.json"


# ============================================
# LOAD DATA
# ============================================

def load_text_embeddings():
    df = pd.read_parquet(POKEMON_EMBED_PATH)

    # load pokedex mapping (id → name)
    with open(POKEDEX_PATH, "r", encoding="utf-8") as f:
        dex = {int(k): v for k, v in json.load(f).items()}

    names = []
    X = []

    for _, row in df.iterrows():
        pid = int(row["id"])
        if pid not in dex:
            continue
        names.append(dex[pid])
        X.append(np.array(row["text_embedding"], dtype=np.float32))

    X = np.stack(X, axis=0)
    return names, X


# ============================================
# METRICS / DIAGNOSTICS
# ============================================

def nearest_neighbour_accuracy(orig, reduced):
    d_orig = cdist(orig, orig, metric="cosine")
    d_red = cdist(reduced, reduced, metric="cosine")

    nn_orig = np.argmin(d_orig + np.eye(len(orig)) * 1e9, axis=1)
    nn_red = np.argmin(d_red + np.eye(len(orig)) * 1e9, axis=1)

    return np.mean(nn_orig == nn_red)


def distance_spearman(orig, reduced):
    d_orig = cdist(orig, orig, metric="cosine").flatten()
    d_red = cdist(reduced, reduced, metric="cosine").flatten()
    corr, _ = spearmanr(d_orig, d_red)
    return corr


# ============================================
# MAIN
# ============================================

def main(dim):
    print("=== LOADING ===")
    names, X = load_text_embeddings()
    print(f"Loaded {len(names)} Pokémon embeddings")
    print(f"Original dim = {X.shape[1]}")

    print("\n=== PCA REDUCTION ===")
    pca = PCA(n_components=dim)
    X_reduced = pca.fit_transform(X)

    explained = pca.explained_variance_ratio_.sum()
    print(f"PCA → {dim} dims, explained variance = {explained:.4f}")

    print("\n=== METRICS ===")
    nn_acc = nearest_neighbour_accuracy(X, X_reduced)
    print(f"Nearest-neighbour match rate: {nn_acc:.4f}")

    spearman = distance_spearman(X, X_reduced)
    print(f"Spearman distance correlation: {spearman:.4f}")

    print("\n=== SAVING JSON ===")
    out_dict = {
        name: X_reduced[i].astype(float).tolist()
        for i, name in enumerate(names)
    }

    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2)

    print(f"Saved reduced embeddings → {OUT_JSON_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dim", type=int, default=32, help="PCA output dimension")
    args = parser.parse_args()
    main(args.dim)

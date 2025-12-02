import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# -------------------------------------------------------------------
# Load all experiment files
# -------------------------------------------------------------------
EXP_DIR = "results/experiments/*.json"

records = []

for path in glob.glob(EXP_DIR):
    with open(path, "r") as f:
        d = json.load(f)

    seed = d["seed"]
    if seed not in [0, 1, 2, 3]:
        continue  # exclude seed 4

    method = d["method"]
    B = d["budget"]
    nb = d["battles_per_opponent"]
    final_wr = d["final_wr"]
    runtime = d.get("runtime_sec", None)

    # Record row
    records.append({
        "method": method,
        "seed": seed,
        "B": B,
        "nb": nb,
        "final_wr": final_wr,
        "runtime_sec": runtime,
        "history": d["history"]
    })

df = pd.DataFrame(records)
print("Loaded", len(df), "experiment records")

# -------------------------------------------------------------------
# (1) Average runtime grouped by configuration (B, nb, method)
# -------------------------------------------------------------------
avg_runtime_cfg = (
    df.groupby(["B", "nb", "method"])["runtime_sec"]
      .mean()
      .unstack("method")  # optional: wide table by method
)

print("\n=== Average Runtime (secs) for each configuration (B, nb, method) ===")
print(avg_runtime_cfg)


# -------------------------------------------------------------------
# (2) Mixed-effects ANOVA on final_wr with seed as random effect
# -------------------------------------------------------------------

# Filter to the B × nb combinations we care about
df_sub = df[(df["B"].isin([5000, 10000])) & (df["nb"].isin([1, 3]))].copy()

# Convert factors to categorical variables
df_sub["B"] = df_sub["B"].astype("category")
df_sub["nb"] = df_sub["nb"].astype("category")
df_sub["seed"] = df_sub["seed"].astype("category")

# Mixed-effects model:
#   final_wr ~ B * nb  (fixed effects: main effects of B, nb, and interaction)
#   + (1 | seed)       (random intercept per seed)
model = smf.mixedlm("final_wr ~ B * nb", df_sub, groups=df_sub["seed"])
result = model.fit(reml=False)

print("\n=== Mixed-Effects ANOVA (LMM) ===")
print(result.summary())

# Optional: likelihood ratio test of interaction (B:nb)
# Fit reduced model without interaction
model_reduced = smf.mixedlm("final_wr ~ B + nb", df_sub, groups=df_sub["seed"])
result_reduced = model_reduced.fit(reml=False)

LR = 2 * (result.llf - result_reduced.llf)
df_diff = result.df_modelwc - result_reduced.df_modelwc

from scipy.stats import chi2
p_val = chi2.sf(LR, df_diff)

print("\n=== Likelihood Ratio Test for Interaction B:nb ===")
print(f"LR statistic = {LR:.3f}")
print(f"df = {df_diff}")
print(f"p = {p_val:.4g}")


# -------------------------------------------------------------------
# (3) Plot best_wr_so_far vs B_used for EACH configuration
# -------------------------------------------------------------------

configs = [(5000, 1), (5000, 3), (10000, 1), (10000, 3)]

for (B_target, nb_target) in configs:
    plt.figure(figsize=(8, 6))
    plt.title(f"Progress Curves (B={B_target}, nb={nb_target})")

    df_cfg = df[(df["B"] == B_target) & (df["nb"] == nb_target)]

    for method in df_cfg["method"].unique():
        curves = {}

        # Collect curves for this method and config
        for _, row in df_cfg[df_cfg["method"] == method].iterrows():
            for h in row["history"]:
                B_used = h["B_used"]
                wr = h["best_wr_so_far"]
                curves.setdefault(B_used, []).append(wr)

        if len(curves) == 0:
            continue

        xs = sorted(curves.keys())
        means = np.array([np.mean(curves[x]) for x in xs])
        stds = np.array([np.std(curves[x], ddof=1) for x in xs])
        ns = np.array([len(curves[x]) for x in xs])

        # standard error
        se = stds / np.sqrt(ns)

        # 95% CI = mean ± 1.96 * SE
        ci_lower = means - 1.96 * se
        ci_upper = means + 1.96 * se

        # Plot mean curve
        plt.plot(xs, means, marker="o", label=method.upper())

        # Plot confidence band
        plt.fill_between(xs, ci_lower, ci_upper, alpha=0.2)

    plt.xlabel("B_used (battle budget consumed)")
    plt.ylabel("Best win rate so far (averaged across seeds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

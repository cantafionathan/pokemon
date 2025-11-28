# bo/optimizer.py
import torch
import logging
import random
import json
import numpy as np
from botorch.acquisition import LogExpectedImprovement
from botorch.optim import optimize_acqf
from botorch.utils.transforms import normalize, unnormalize

from .encoding import FEATURE_DIM, parse_showdown_team
from .models import build_gp
from .blackbox import black_box_eval

logger = logging.getLogger("bo.optimizer")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

def safe_standardize(Y: torch.Tensor):
    mean = Y.mean()
    std = Y.std()

    # Fix: if std is NaN or Inf or 0, replace with 1
    if torch.isnan(std) or torch.isinf(std) or std < 1e-8:
        std = torch.tensor(1.0, dtype=Y.dtype, device=Y.device)

    Y_norm = (Y - mean) / std
    return Y_norm, mean, std

class BOOptimizer:
    """
    Bayesian Optimization loop.
    """

    def __init__(self, bounds_scale: float = 3.0, device: str = "cpu"):
        """
        Args:
            bounds_scale: A scaling factor to define the search space for the
                team embeddings. The space will be [-scale, +scale] for each dimension.
            device: The torch device to use for tensors ('cpu' or 'cuda').
        """
        self.device = torch.device(device)
        dtype = torch.double

        # Embedding space is unbounded; we clamp with soft bounds.
        self.bounds = torch.stack(
            [
                -bounds_scale * torch.ones(FEATURE_DIM, device=self.device, dtype=dtype),
                +bounds_scale * torch.ones(FEATURE_DIM, device=self.device, dtype=dtype),
            ]
        )

    def run_bo(
        self,
        n_iters: int = 3,
        n_init: int = 1,
        n_battles_per_opponent: int = 1,
        n_moveset_samples: int = 5,
        seed: int | None = None,
        history_file: str | None = None
    ):
        """
        Runs the Bayesian Optimization loop.

        Args:
            n_iters: Number of optimization iterations.
            n_init: Number of initial random points to sample.
            n_battles_per_opponent: Number of battles to run per opponent for evaluation.
            n_moveset_samples: Number of random moveset assignments to try per team.
            seed: Random seed for reproducibility.
        """

        # set up history
        history = []

        # set seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            # for CUDA determinism
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)

            logger.info(f"BO seed set to {seed}")

        logger.info("=== Initializing BO with %d random teams ===", n_init)
        dtype = torch.double

        # --- Initial data (random embeddings)
        X_unit = torch.rand(n_init, FEATURE_DIM, device=self.device, dtype=dtype)
        X = unnormalize(X_unit, self.bounds) # scale to real bounds

        initial_results = [black_box_eval(x=x, 
                                          n_battles_per_opponent=n_battles_per_opponent, 
                                          n_moveset_samples=n_moveset_samples) for x in X]
        Y = torch.tensor([[score] for score, _ in initial_results], device=self.device, dtype=dtype)
        team_strings = [team_str for _, team_str in initial_results]

        best_idx = torch.argmax(Y).item()
        best_x = X[best_idx]
        best_y = Y[best_idx].item()
        best_team_str = team_strings[best_idx]

        logger.info("Initial best: %.4f", best_y)

        # record initial state
        history.append({
            "iteration": 0,
            "best_wr_so_far": best_y,
        })
        if history_file is not None:
            with open(history_file, "w") as f:
                json.dump(history, f, indent=2)

        # --- BO Loop ---
        for it in range(n_iters):
            logger.info("\n=== Iteration %d/%d ===", it + 1, n_iters)

            # Normalize X into [0, 1]
            norm_X = normalize(X, self.bounds)

            # Standardize Y
            Y_norm, Y_mean, Y_std = safe_standardize(Y)

            # Fit GP on standardized Y_norm
            model = build_gp(norm_X, Y_norm)

            # Acquisition function: best_f also needs to be normalized
            best_f_norm = (Y.max() - Y_mean) / Y_std

            acq = LogExpectedImprovement(
                model,
                best_f=best_f_norm,
            )

            # Optimize acquisition in normalized space
            candidates, _ = optimize_acqf(
                acq_function=acq,
                bounds=torch.tensor(
                    [[0.0] * FEATURE_DIM, [1.0] * FEATURE_DIM],
                    device=self.device,
                    dtype=dtype),
                q=1,
                num_restarts=10,
                raw_samples=128,
            )

            # Unnormalize candidates back to real space
            new_candidates = unnormalize(candidates.detach(), self.bounds)

            # Evaluate
            new_results = [black_box_eval(x=x, 
                                          n_battles_per_opponent=n_battles_per_opponent, 
                                          n_moveset_samples=n_moveset_samples) for x in new_candidates]
            Y_new = torch.tensor([[score] for score, _ in new_results], device=self.device, dtype=dtype)
            new_team_strings = [team_str for _, team_str in new_results]

            # Append unnormalized Y
            X = torch.cat([X, new_candidates], dim=0)
            Y = torch.cat([Y, Y_new], dim=0)
            team_strings.extend(new_team_strings)

            max_idx_new = torch.argmax(Y_new).item()
            max_score_new = Y_new[max_idx_new].item()
            if max_score_new > best_y:
                best_y = max_score_new
                best_x = new_candidates[max_idx_new]
                best_team_str = new_team_strings[max_idx_new]

            parsed_team = parse_showdown_team(new_team_strings[max_idx_new])
            print("\n=== NEW TEAM ===")
            print(f"Score {max_score_new:.4f}")
            for i, b in enumerate(parsed_team, 1):
                print(f"{i}. {b['species']}: {b['moveset']}")

            logger.info(
                " -> New candidates: %s",
                ", ".join([f"{float(y):.3f}" for y in Y_new.flatten()])
            )
            logger.info(" -> Best so far: %.4f", best_y)

            ### record iteration state
            history.append({
                "iteration": it,
                "best_wr_so_far": best_y,
            })
            if history_file is not None:
                with open(history_file, "w") as f:
                    json.dump(history, f, indent=2)


        logger.info("=== BO Finished ===")
        logger.info("Best score found: %.4f", best_y)

        return best_x, best_y, best_team_str

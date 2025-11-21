# bo/optimizer.py
import torch
import logging
from botorch.acquisition import LogExpectedImprovement
from botorch.optim import optimize_acqf
from botorch.utils.transforms import normalize, unnormalize

from .encoding import FEATURE_DIM
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
        batch_size: int = 1,
    ):
        """
        Runs the Bayesian Optimization loop.

        Args:
            n_iters: Number of optimization iterations.
            n_init: Number of initial random points to sample.
            batch_size: Number of candidates to evaluate in each iteration.
        """
        logger.info("=== Initializing BO with %d random teams ===", n_init)
        dtype = torch.double

        # --- Initial data (random embeddings)
        X_unit = torch.rand(n_init, FEATURE_DIM, device=self.device, dtype=dtype)
        X = unnormalize(X_unit, self.bounds)  # now X is inside [-bounds_scale, bounds_scale]

        initial_results = [black_box_eval(x) for x in X]
        Y = torch.tensor([[score] for score, _ in initial_results], device=self.device, dtype=dtype)
        team_strings = [team_str for _, team_str in initial_results]

        best_idx = torch.argmax(Y).item()
        best_x = X[best_idx]
        best_y = Y[best_idx].item()
        best_team_str = team_strings[best_idx]

        logger.info("Initial best: %.4f", best_y)

        # --- BO Loop ---
        for it in range(n_iters):
            logger.info("=== Iteration %d/%d ===", it + 1, n_iters)

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
                q=batch_size,
                num_restarts=10,
                raw_samples=128,
            )

            # Unnormalize candidates back to real space
            new_candidates = unnormalize(candidates.detach(), self.bounds)

            # Evaluate
            new_results = [black_box_eval(x) for x in new_candidates]
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

            logger.info(
                " -> New candidates: %s",
                ", ".join([f"{float(y):.3f}" for y in Y_new.flatten()])
            )
            logger.info(" -> Best so far: %.4f", best_y)


        logger.info("=== BO Finished ===")
        logger.info("Best score found: %.4f", best_y)

        return best_x, best_y, best_team_str

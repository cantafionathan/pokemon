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


class BOOptimizer:
    """
    Clean, modern Bayesian Optimization loop.
    Uses ONLY real battle results (black_box_eval).
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
        X = torch.randn(n_init, FEATURE_DIM, device=self.device, dtype=dtype)
        Y = torch.tensor([[black_box_eval(x)] for x in X], device=self.device, dtype=dtype)

        logger.info("Initial best: %.4f", Y.max().item())

        # --- BO Loop ---
        for it in range(n_iters):
            logger.info("=== Iteration %d/%d ===", it + 1, n_iters)

            # Train GP
            # Normalize inputs to [0, 1] cube for GP
            norm_X = normalize(X, self.bounds)
            model = build_gp(norm_X, Y)

            acq = LogExpectedImprovement(
                model,
                best_f=Y.max(),
                # The objective is not needed for simple EI
            )

            # Optimize acquisition
            candidates, _ = optimize_acqf(
                acq_function=acq,
                # Optimize on the normalized [0, 1] cube
                bounds=torch.tensor([[0.0] * FEATURE_DIM, [1.0] * FEATURE_DIM], device=self.device, dtype=dtype),
                q=batch_size,
                num_restarts=10,
                raw_samples=128,
            )
            # Unnormalize candidates back to original space
            new_candidates = unnormalize(candidates.detach(), self.bounds)

            # Evaluate with real battles
            Y_new = torch.tensor(
                [[black_box_eval(x)] for x in new_candidates],
                device=self.device,
                dtype=dtype,
            )

            # Update dataset
            X = torch.cat([X, new_candidates], dim=0)
            Y = torch.cat([Y, Y_new], dim=0)

            logger.info(
                " -> New candidates: %s",
                ", ".join([f"{float(y):.3f}" for y in Y_new.flatten()])
            )
            logger.info(" -> Best so far: %.4f", Y.max().item())

        # --- Final best ---
        best_idx = torch.argmax(Y).item()
        best_x = X[best_idx]
        best_y = Y[best_idx].item()

        logger.info("=== BO Finished ===")
        logger.info("Best score found: %.4f", best_y)

        return best_x, best_y

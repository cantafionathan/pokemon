# models.py

import torch
from botorch.models import SingleTaskGP
from botorch.fit import fit_gpytorch_mll
from gpytorch.mlls import ExactMarginalLogLikelihood


def build_gp(train_x: torch.Tensor, train_y: torch.Tensor) -> SingleTaskGP:
    """
    Build and fit a GP model given observed data.
    Args:
        train_x: (N, D)
        train_y: (N, 1)
    """
    gp = SingleTaskGP(train_x, train_y)
    mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
    fit_gpytorch_mll(mll)
    return gp

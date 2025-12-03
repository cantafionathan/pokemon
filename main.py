# main.py
from opt.optimizer import Optimizer

if __name__ == "__main__":
    method = "ga"   # "bo", "ga", "rs"
    B = 500
    seed = 0
    n_battles_per_opponent = 1

    opt = Optimizer(
        method=method,
        B=B,
        seed=seed,
        n_battles_per_opponent=n_battles_per_opponent,
        format="ou"  # "ou", "ubers"
    )

    opt.run()

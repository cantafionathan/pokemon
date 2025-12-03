# main.py
from opt.optimizer import Optimizer

if __name__ == "__main__":
    method = "bo"   # "bo", "ga", "rs"
    B = 750 + 150*55
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

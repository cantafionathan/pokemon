# main.py
from opt.optimizer import Optimizer

if __name__ == "__main__":
    method = "pool_rs"   # "pool_bo", "pool_ga", "pool_rs"
    B = 750 + 150*55
    seed = 0
    n_battles_per_opponent = 1
    format = "ou" # "ou", "ubers"

    opt = Optimizer(
        method=method,
        B=B,
        seed=seed,
        n_battles_per_opponent=n_battles_per_opponent,
        format=format  
    )

    opt.run()

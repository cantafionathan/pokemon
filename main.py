# main.py
from opt.optimizer import Optimizer

if __name__ == "__main__":
    method = "rs"   # "pool_bo", "pool_ga", "pool_rs"
    B = 750 + 150*55
    seed = 0
    format = "gen1ou" # "gen1ou", "gen1ubers"

    opt = Optimizer(
        method=method,
        B=B,
        seed=seed,
        format=format  
    )

    opt.run()

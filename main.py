# main.py

from opt.bo.optimizer import BOOptimizer
from opt.bo.encoding import decode_team_from_embedding as decode

if __name__ == "__main__":
    opt = BOOptimizer()
    best_x, best_y, best_team_str = opt.run_bo(n_iters=100, n_init=5, batch_size=1)

    print("\n=== BEST TEAM ===")
    print("Score:", best_y)
    print("Team:\n", best_team_str)


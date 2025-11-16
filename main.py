# main.py

from bo.optimizer import TeamOptimizer
from bo.encoding import decode_team_from_embedding as decode

if __name__ == "__main__":
    opt = TeamOptimizer()
    best_x, best_y = opt.run_bo(n_iters=80, n_init=5, batch_size=1)

    print("\n=== BEST TEAM ===")
    team = decode(best_x)
    print(team["team"])
    print("Score:", best_y)

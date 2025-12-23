from experiments.ga_vs_rs import run_ga_vs_rs, add_args
from evaluation.evaluation import evaluate_run
from plotting.plot_ga_vs_rs import run_plots as plot_ga_vs_rs



# -------------------------
# Experiment configuration
# -------------------------

EXPERIMENTS = {
    "ga_vs_rs": {
        "run": run_ga_vs_rs,
        "evaluation": evaluate_run,
        "plot": plot_ga_vs_rs,
        "add_args": add_args
    }
}

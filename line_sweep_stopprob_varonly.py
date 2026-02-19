import random

import numpy as np
import matplotlib.pyplot as plt

from demo_composite_flow_robot import demo_composite_flow as run_robot
from demo_variable_conveyor import demo_composite_flow as run_variable
from demo_variable_conveyor_tempon import demo_composite_flow as run_tempon
import Parameter_horizontal as PH


def run_stats(fn, n_runs, seed_base, **kwargs):
    bottles = []
    blocked_pct = []
    busy_pct = []
    for i in range(n_runs):
        random.seed(seed_base + i)
        np.random.seed(seed_base + i)
        result = fn(plot=False, **kwargs)
        total_time = float(result.get("total_time", 0.0)) or 1.0
        blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
        busy_time = float(result.get("busy_time", 0.0))
        bottles.append(len(result.get("inspected_times", [])))
        blocked_pct.append(blocked_time * 100.0 / total_time)
        busy_pct.append(busy_time * 100.0 / total_time)
    def mean_ci(arr):
        arr = np.array(arr, dtype=float)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        ci = 1.96 * std / np.sqrt(len(arr)) if len(arr) > 1 else 0.0
        return mean, ci
    b_mean, b_ci = mean_ci(bottles)
    blk_mean, blk_ci = mean_ci(blocked_pct)
    busy_mean, busy_ci = mean_ci(busy_pct)
    return (b_mean, b_ci), (blk_mean, blk_ci), (busy_mean, busy_ci)


def sweep_stop_prob(fn, p_vals, s_fixed, n_runs, seed_base, variable_speed):
    bottles = []
    blocked = []
    busy = []
    for j, p in enumerate(p_vals):
        (b_mean, b_ci), (blk_mean, blk_ci), (busy_mean, busy_ci) = run_stats(
            fn,
            n_runs=n_runs,
            seed_base=seed_base + j * 10,
            down_time=p,
            s=s_fixed,
            variable_speed=variable_speed,
        )
        bottles.append((b_mean, b_ci))
        blocked.append((blk_mean, blk_ci))
        busy.append((busy_mean, busy_ci))
    return np.array(bottles), np.array(blocked), np.array(busy)


def main():
    p_vals = np.linspace(0.0, 0.15, 16)  # 0.00 -> 0.15 step 0.01
    s_fixed = 0.2
    n_runs = 4

    series = [
        ("Robot (var)", "tab:blue", 1100, run_robot),
        ("Variable (var)", "tab:orange", 2100, run_variable),
        ("Tampon (var)", "tab:green", 3100, run_tempon),
    ]

    results = {}
    for label, _, seed, fn in series:
        results[label] = sweep_stop_prob(fn, p_vals, s_fixed, n_runs, seed, variable_speed=True)

    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True, constrained_layout=True)

    for label, color, _, _ in series:
        data = results[label][0]
        mean = data[:, 0]
        ci = data[:, 1]
        axes[0].plot(p_vals, mean, label=label, color=color)
        axes[0].fill_between(p_vals, mean - ci, mean + ci, color=color, alpha=0.2)
    axes[0].set_ylabel("Bouteilles inspectées (moyenne)")
    axes[0].set_title(rf"Impact probabilité d'inspection longue à {s_fixed} (entre {PH.min} - {PH.max} s), inspection normale entre {PH.inspect_min} - {PH.inspect_max} s")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    for label, color, _, _ in series:
        data = results[label][1]
        mean = data[:, 0]
        ci = data[:, 1]
        axes[1].plot(p_vals, mean, label=label, color=color)
        axes[1].fill_between(p_vals, mean - ci, mean + ci, color=color, alpha=0.2)
    axes[1].set_ylabel("Temps d'arrêt grenailleuse (%)")
    axes[1].grid(True, alpha=0.3)

    for label, color, _, _ in series:
        data = results[label][2]
        mean = data[:, 0]
        ci = data[:, 1]
        axes[2].plot(p_vals, mean, label=label, color=color)
        axes[2].fill_between(p_vals, mean - ci, mean + ci, color=color, alpha=0.2)
    axes[2].set_ylabel("Occupation inspecteur (%)")
    axes[2].set_xlabel("Probabilité d'arrêt")
    axes[2].grid(True, alpha=0.3)

    out_path = rf"line_sweep_stopprob_varonly_old_parameters{s_fixed}{PH.inspect_min}{PH.inspect_max}.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()

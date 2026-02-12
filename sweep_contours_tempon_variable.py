import random

import numpy as np
import matplotlib.pyplot as plt

import Parameter_horizontal as P
from demo_variable_conveyor import demo_composite_flow as run_variable
from demo_variable_conveyor_tempon import demo_composite_flow as run_tempon


def run_mean(fn, n_runs, seed_base, **kwargs):
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
    return float(np.mean(bottles)), float(np.mean(blocked_pct)), float(np.mean(busy_pct))


def sweep(fn, p_vals, s_vals, n_runs, seed_base):
    bottles_grid = np.zeros((len(s_vals), len(p_vals)))
    blocked_grid = np.zeros((len(s_vals), len(p_vals)))
    busy_grid = np.zeros((len(s_vals), len(p_vals)))
    for i, s in enumerate(s_vals):
        for j, p in enumerate(p_vals):
            b_mean, blk_mean, busy_mean = run_mean(
                fn,
                n_runs=n_runs,
                seed_base=seed_base + i * 1000 + j * 10,
                down_time=p,
                s=s,
            )
            bottles_grid[i, j] = b_mean
            blocked_grid[i, j] = blk_mean
            busy_grid[i, j] = busy_mean
    return bottles_grid, blocked_grid, busy_grid


def plot_contours(x, y, z, title, cbar_label, ax, vmin=None, vmax=None):
    levels = 12
    contour = ax.contourf(x, y, z, levels=levels, cmap="viridis", vmin=vmin, vmax=vmax)
    ax.set_title(title)
    ax.set_xlabel("Probabilité interruption")
    ax.set_ylabel("Probabilité inspection longue")
    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label(cbar_label)


def main():
    p_vals = np.linspace(0.0, 0.15, 6)
    s_vals = np.linspace(0.0, 0.15, 6)
    n_runs = 20

    bottles_variable, blocked_variable, busy_variable = sweep(run_variable, p_vals, s_vals, n_runs, seed_base=1000)
    bottles_tempon, blocked_tempon, busy_tempon = sweep(run_tempon, p_vals, s_vals, n_runs, seed_base=2000)

    X, Y = np.meshgrid(p_vals, s_vals)

    fig, axes = plt.subplots(3, 2, figsize=(11, 11), constrained_layout=True)
    bottles_min = float(min(np.min(bottles_variable), np.min(bottles_tempon)))
    bottles_max = float(max(np.max(bottles_variable), np.max(bottles_tempon)))
    blocked_min = float(min(np.min(blocked_variable), np.min(blocked_tempon)))
    blocked_max = float(max(np.max(blocked_variable), np.max(blocked_tempon)))
    busy_min = float(min(np.min(busy_variable), np.min(busy_tempon)))
    busy_max = float(max(np.max(busy_variable), np.max(busy_tempon)))
    # Row 1: Bottles
    plot_contours(
        X, Y, bottles_variable,
        "Variable - Bouteilles inspectées (moyenne)",
        "Bouteilles",
        axes[0, 0],
        vmin=bottles_min,
        vmax=bottles_max,
    )
    plot_contours(
        X, Y, bottles_tempon,
        "Tampon - Bouteilles inspectées (moyenne)",
        "Bouteilles",
        axes[0, 1],
        vmin=bottles_min,
        vmax=bottles_max,
    )
    # Row 2: Grenailleuse stop %
    plot_contours(
        X, Y, blocked_variable,
        "Variable - Temps d'arrêt grenailleuse (%)",
        "% arrêt",
        axes[1, 0],
        vmin=blocked_min,
        vmax=blocked_max,
    )
    plot_contours(
        X, Y, blocked_tempon,
        "Tampon - Temps d'arrêt grenailleuse (%)",
        "% arrêt",
        axes[1, 1],
        vmin=blocked_min,
        vmax=blocked_max,
    )
    # Row 3: Inspector busy %
    plot_contours(
        X, Y, busy_variable,
        "Variable - Temps occupation inspecteur (%)",
        "% occupé",
        axes[2, 0],
        vmin=busy_min,
        vmax=busy_max,
    )
    plot_contours(
        X, Y, busy_tempon,
        "Tampon - Temps occupation inspecteur (%)",
        "% occupé",
        axes[2, 1],
        vmin=busy_min,
        vmax=busy_max,
    )

    out_path = "sweep_contours_tempon_variable.png"
    fig.suptitle("Balayage probabilité d'arrêt vs pause longue (moyenne sur 10 runs)", fontsize=12)
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()

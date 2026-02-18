import csv
import random

import matplotlib.pyplot as plt
import numpy as np

import Parameter_horizontal as PH
from demo_variable_conveyor_tempon import demo_composite_flow as run_tempon


def run_stats(n_runs, seed_base, weights, base_kwargs):
    bottles = []
    blocked_pct = []

    for i in range(n_runs):
        seed = seed_base + i
        random.seed(seed)
        np.random.seed(seed)
        result = run_tempon(
            plot=False,
            animate=False,
            variable_speed=True,
            speed_ctrl_w_step_out=weights[0],
            speed_ctrl_w_pre_var=weights[1],
            speed_ctrl_w_var=weights[2],
            speed_ctrl_w_cont=weights[3],
            speed_ctrl_w_inspect=weights[4],
            **base_kwargs,
        )
        total_time = float(result.get("total_time", 0.0)) or 1.0
        blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
        bottles.append(len(result.get("inspected_times", [])))
        blocked_pct.append(blocked_time * 100.0 / total_time)

    return float(np.mean(bottles)), float(np.mean(blocked_pct))


def pareto_front(points):
    points_sorted = sorted(points, key=lambda p: p["blocked"])
    front = []
    best_bottles = -1e18
    for p in points_sorted:
        if p["bottles"] > best_bottles:
            front.append(p)
            best_bottles = p["bottles"]
    return front


def main():
    n_candidates = 140
    n_runs = 5
    rng_seed = 62
    seed_base = 15000

    base_kwargs = {
        "mean_interval": PH.mean_interval,
        "down_time": PH.down_time,
        "min_inter": PH.min_iter,
        "max_inter": PH.max_iter,
        "t_dis": PH.t_dis,
        "t_dis2": PH.t_dis2,
        "inspect_min": PH.inspect_min,
        "inspect_max": PH.inspect_max,
        "max_long": PH.max,
        "min_long": PH.min,
        "s": PH.s,
        "step_time": PH.step_time,
        "step_time_2": PH.step_time_2,
        "steps": PH.steps,
        "gr_conv": PH.gr_conv,
        "cont_out_capacity": 1,
        "length_first": PH.length_first,
        "length_second": PH.length_second,
        "length_third": PH.length_third,
        "horizontal_spacing": PH.horizontal_spacing,
        "vertical_spacing": PH.vertical_spacing,
        "speed_tempon": PH.speed_tempon,
        "first_speed": PH.first_speed,
        "second_speed": PH.second_speed,
        "dt": PH.dt,
        "env_time": PH.env_time,
        "sample_time": 1.0,
        "det_hold_time": PH.det_hold_time,
        "mode_switch_delay": PH.mode_switch_delay,
    }

    rng = np.random.default_rng(rng_seed)
    candidates = rng.dirichlet(alpha=np.ones(5), size=n_candidates).tolist()
    default_weights = [0.10, 0.10, 0.20, 0.30, 0.30]
    candidates = [default_weights] + candidates

    points = []
    for idx, w in enumerate(candidates):
        bottles, blocked = run_stats(
            n_runs=n_runs,
            seed_base=seed_base + idx * 100,
            weights=w,
            base_kwargs=base_kwargs,
        )
        score = bottles - 0.5 * blocked
        points.append(
            {
                "idx": idx,
                "w_step_out": float(w[0]),
                "w_pre_var": float(w[1]),
                "w_var": float(w[2]),
                "w_cont": float(w[3]),
                "w_inspect": float(w[4]),
                "bottles": bottles,
                "blocked": blocked,
                "score": score,
                "is_default": idx == 0,
            }
        )

    top = sorted(points, key=lambda p: p["score"], reverse=True)[:10]
    front = pareto_front(points)

    print("=== Top 10 by score (bottles - 0.5 * blocked%) ===")
    for i, p in enumerate(top, start=1):
        tag = " (default)" if p["is_default"] else ""
        print(
            f"[{i}] bottles={p['bottles']:.1f} | blocked={p['blocked']:.2f}% | "
            f"weights=({p['w_step_out']:.3f}, {p['w_pre_var']:.3f}, {p['w_var']:.3f}, {p['w_cont']:.3f}, {p['w_inspect']:.3f}){tag}"
        )

    csv_path = "sweep_tempon_pressure_weights.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "idx",
                "w_step_out",
                "w_pre_var",
                "w_var",
                "w_cont",
                "w_inspect",
                "bottles",
                "blocked",
                "score",
                "is_default",
            ],
        )
        writer.writeheader()
        writer.writerows(points)

    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    blocked_vals = [p["blocked"] for p in points]
    bottle_vals = [p["bottles"] for p in points]
    color_vals = [p["w_inspect"] for p in points]

    sc = ax.scatter(
        blocked_vals,
        bottle_vals,
        c=color_vals,
        cmap="viridis",
        alpha=0.75,
        s=34,
        edgecolors="none",
    )

    front_x = [p["blocked"] for p in front]
    front_y = [p["bottles"] for p in front]
    ax.plot(front_x, front_y, color="black", linewidth=1.8, label="Pareto front")

    default_point = next(p for p in points if p["is_default"])
    ax.scatter(
        [default_point["blocked"]],
        [default_point["bottles"]],
        color="red",
        s=90,
        marker="x",
        linewidths=2.0,
        label="Default weights",
    )

    ax.set_xlabel("Grenailleuse stop (%)")
    ax.set_ylabel("Inspected bottles (mean)")
    ax.set_title("Variable conveyor + tempon flow: pressure-weight sweep")
    ax.grid(True, alpha=0.3)
    ax.legend()
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("w_inspect")
    plt.tight_layout()
    fig_path = "sweep_tempon_pressure_weights.png"
    plt.savefig(fig_path, dpi=150)
    print(f"Saved: {csv_path}")
    print(f"Saved: {fig_path}")


if __name__ == "__main__":
    main()

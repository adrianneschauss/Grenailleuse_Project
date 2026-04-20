import csv
import random
from statistics import mean

import matplotlib.pyplot as plt
import numpy as np

import Parameter_horizontal as PH
from demo_variable_conveyor_tempon import demo_composite_flow as run_tempon


def run_profile(profile, n_runs, seed_base):
    bottles = []
    blocked_pct = []
    busy_pct = []

    for i in range(n_runs):
        seed = seed_base + i
        random.seed(seed)
        np.random.seed(seed)
        result = run_tempon(
            plot=False,
            animate=False,
            variable_speed=True,
            s=0.1,  # fixed as requested
            speed_ctrl_w_step_out=profile["w_step_out"],
            speed_ctrl_w_pre_var=profile["w_pre_var"],
            speed_ctrl_w_var=profile["w_var"],
            speed_ctrl_w_cont=profile["w_cont"],
            speed_ctrl_w_inspect=profile["w_inspect"],
        )

        total_time = float(result.get("total_time", 0.0)) or 1.0
        blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
        busy_time = float(result.get("busy_time", 0.0))

        bottles.append(len(result.get("inspected_times", [])))
        blocked_pct.append(blocked_time * 100.0 / total_time)
        busy_pct.append(busy_time * 100.0 / total_time)

    return {
        "bottles_mean": mean(bottles) if bottles else 0.0,
        "blocked_pct_mean": mean(blocked_pct) if blocked_pct else 0.0,
        "busy_pct_mean": mean(busy_pct) if busy_pct else 0.0,
    }


def build_profiles():
    # Ordered from upstream-heavy to downstream-heavy.
    return [
        {
            "name": "Cas 1: Début dominant",
            "labelled": True,
            "w_step_out": 0.45,
            "w_pre_var": 0.25,
            "w_var": 0.20,
            "w_cont": 0.07,
            "w_inspect": 0.03,
        },
        {
            "name": "Cas 2: Amont favorisé",
            "labelled": True,
            "w_step_out": 0.35,
            "w_pre_var": 0.20,
            "w_var": 0.25,
            "w_cont": 0.13,
            "w_inspect": 0.07,
        },
        {
            "name": "Cas 3: Équilibré",
            "labelled": True,
            "w_step_out": 0.30,
            "w_pre_var": 0.15,
            "w_var": 0.30,
            "w_cont": 0.15,
            "w_inspect": 0.10,
        },
        {
            "name": "Cas 4: Aval favorisé",
            "labelled": True,
            "w_step_out": 0.18,
            "w_pre_var": 0.12,
            "w_var": 0.22,
            "w_cont": 0.23,
            "w_inspect": 0.25,
        },
        {
            "name": "Cas 5: Fin dominante",
            "labelled": True,
            "w_step_out": 0.05,
            "w_pre_var": 0.05,
            "w_var": 0.15,
            "w_cont": 0.30,
            "w_inspect": 0.45,
        },
    ]


def interpolate_profiles(anchor_profiles, points_between=2):
    keys = ["w_step_out", "w_pre_var", "w_var", "w_cont", "w_inspect"]
    out = []
    for i in range(len(anchor_profiles) - 1):
        p0 = anchor_profiles[i]
        p1 = anchor_profiles[i + 1]
        out.append(dict(p0))
        for k in range(1, points_between + 1):
            t = k / (points_between + 1)
            p = {"name": "", "labelled": False}
            for key in keys:
                p[key] = (1.0 - t) * p0[key] + t * p1[key]
            out.append(p)
    out.append(dict(anchor_profiles[-1]))
    return out


def main():
    n_runs = 4
    anchor_profiles = build_profiles()
    profiles = interpolate_profiles(anchor_profiles, points_between=2)

    rows = []
    for idx, profile in enumerate(profiles, start=1):
        metrics = run_profile(profile=profile, n_runs=n_runs, seed_base=20000 + idx * 100)
        rows.append(
            {
                "case": profile["name"],
                "labelled": profile["labelled"],
                "s_fixed": 0.05,
                "down_time": PH.down_time,
                "w_step_out": profile["w_step_out"],
                "w_pre_var": profile["w_pre_var"],
                "w_var": profile["w_var"],
                "w_cont": profile["w_cont"],
                "w_inspect": profile["w_inspect"],
                "bottles_mean": round(metrics["bottles_mean"], 1),
                "blocked_pct_mean": round(metrics["blocked_pct_mean"], 2),
                "busy_pct_mean": round(metrics["busy_pct_mean"], 1),
            }
        )

    csv_path = "tempon_weight_profiles_s01.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "labelled",
                "s_fixed",
                "down_time",
                "w_step_out",
                "w_pre_var",
                "w_var",
                "w_cont",
                "w_inspect",
                "bottles_mean",
                "blocked_pct_mean",
                "busy_pct_mean",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("=== Results (s fixed at 0.1) ===")
    for r in rows:
        if not r["labelled"]:
            continue
        print(
            f"{r['case']}: bottles={r['bottles_mean']}, "
            f"blocked={r['blocked_pct_mean']}%, busy={r['busy_pct_mean']}%"
        )
    print(f"Saved: {csv_path}")

    bottles = [r["bottles_mean"] for r in rows]
    blocked = [r["blocked_pct_mean"] for r in rows]

    x = np.arange(len(rows))
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax2 = ax1.twinx()

    ax1.plot(x, bottles, color="#0E7490", marker="o", linewidth=2.0, label="Bouteilles")
    ax2.plot(x, blocked, color="#B91C1C", marker="s", linewidth=2.0, label="Arrêt grenailleuse (%)")

    labelled_idx = [i for i, r in enumerate(rows) if r["labelled"]]
    labelled_txt = [rows[i]["case"].replace("Cas ", "C") for i in labelled_idx]
    ax1.set_xticks(labelled_idx)
    ax1.set_xticklabels(labelled_txt, rotation=0)
    ax1.set_ylabel("Bouteilles inspectées (moyenne)")
    ax2.set_ylabel("Arrêt grenailleuse (%)")
    ax1.set_title("Variable tempon: profils de poids (inspecteur=0.05, grenailleuse=0.15)")
    ax1.grid(True, alpha=0.3)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

    fig.tight_layout()
    fig_path = "tempon_weight_profiles_s005_015.png"
    plt.savefig(fig_path, dpi=150)
    print(f"Saved: {fig_path}")


if __name__ == "__main__":
    main()

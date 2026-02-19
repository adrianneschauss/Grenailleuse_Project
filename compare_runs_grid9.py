import csv
import random
from statistics import mean

import numpy as np

from demo_composite_flow_robot import demo_composite_flow as run_robot
from demo_variable_conveyor import demo_composite_flow as run_variable
from demo_variable_conveyor_tempon import demo_composite_flow as run_tempon


def run_n(label, fn, n, seed_base=1234):
    busy_times = []
    blocked_times = []
    bottle_counts = []
    step_times = []
    cont_times = []
    total_times = []
    bottles_per_hour_after_600 = []
    occ_after_600 = []
    warmup_s = 600.0

    for i in range(n):
        random.seed(seed_base + i)
        np.random.seed(seed_base + i)
        result = fn(plot=False)

        busy_times.append(float(result.get("busy_time", 0.0)))
        blocked_times.append(float(result.get("grenailleuse_blocked_time", 0.0)))
        bottle_counts.append(len(result.get("inspected_times", [])))
        step_times.append(float(result.get("step_time_total", 0.0)))
        cont_times.append(float(result.get("cont_time_total", 0.0)))
        total_time = float(result.get("total_time", 0.0))
        total_times.append(total_time)

        inspected_times = result.get("inspected_times", []) or []
        if total_time > warmup_s:
            tail_duration = total_time - warmup_s
            tail_bottles = sum(1 for t in inspected_times if t >= warmup_s)
            bottles_per_hour_after_600.append(tail_bottles * 3600.0 / tail_duration)
        else:
            bottles_per_hour_after_600.append(0.0)

        monitor = result.get("monitor", {}) or {}
        mon_t = monitor.get("t", []) or []
        mon_busy = monitor.get("inspector_busy", []) or []
        if mon_t and mon_busy:
            busy_samples = [b for t, b in zip(mon_t, mon_busy) if t >= warmup_s]
            occ_after_600.append(float(np.mean(busy_samples)) * 100.0 if busy_samples else 0.0)
        else:
            occ_after_600.append(0.0)

    total_mean = mean(total_times) if total_times else 0.0

    def pct(x):
        return (x / total_mean * 100.0) if total_mean else 0.0

    return {
        "case": label,
        "busy_time_mean": pct(mean(busy_times) if busy_times else 0.0),
        "blocked_time_mean": pct(mean(blocked_times) if blocked_times else 0.0),
        "bottles_mean": mean(bottle_counts) if bottle_counts else 0.0,
        "bottles_per_hour_after_600_mean": mean(bottles_per_hour_after_600) if bottles_per_hour_after_600 else 0.0,
        "busy_after_600_mean": mean(occ_after_600) if occ_after_600 else 0.0,
        "step_time_mean": pct(mean(step_times) if step_times else 0.0),
        "cont_time_mean": pct(mean(cont_times) if cont_times else 0.0),
    }


def one_decimal(value):
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return value


def rounded_int(value):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return value


def main():
    # 3x3 grid => 9 cases.
    # If you want a 4x4 grid, change to [0.0, 0.05, 0.1, 0.2].
    s_values = [0.0, 0.1, 0.2]
    p_values = [0.0, 0.1, 0.2]
    n_runs = 3

    rows = []
    case_id = 0

    for s_val in s_values:
        for p_val in p_values:
            case_id += 1
            results = [
                run_n(
                    "Verticale",
                    lambda **kwargs: run_robot(variable_speed=False, s=s_val, down_time=p_val, **kwargs),
                    n_runs,
                    seed_base=10000 + case_id * 100,
                ),
                run_n(
                    "Horizontale (sans tampon)",
                    lambda **kwargs: run_variable(variable_speed=False, s=s_val, down_time=p_val, **kwargs),
                    n_runs,
                    seed_base=20000 + case_id * 100,
                ),
                run_n(
                    "Horizontale avec tampon",
                    lambda **kwargs: run_tempon(variable_speed=False, s=s_val, down_time=p_val, **kwargs),
                    n_runs,
                    seed_base=30000 + case_id * 100,
                ),
                run_n(
                    "Verticale avec Vitesse Variable",
                    lambda **kwargs: run_robot(variable_speed=True, s=s_val, down_time=p_val, **kwargs),
                    n_runs,
                    seed_base=40000 + case_id * 100,
                ),
                run_n(
                    "Horizontale (sans tampon) avec Vitesse Variable",
                    lambda **kwargs: run_variable(variable_speed=True, s=s_val, down_time=p_val, **kwargs),
                    n_runs,
                    seed_base=50000 + case_id * 100,
                ),
                run_n(
                    "Horizontale avec tampon et Vitesse Variable",
                    lambda **kwargs: run_tempon(variable_speed=True, s=s_val, down_time=p_val, **kwargs),
                    n_runs,
                    seed_base=60000 + case_id * 100,
                ),
            ]

            for r in results:
                rows.append(
                    {
                        "grid_case": case_id,
                        "s": s_val,
                        "grenailleuse_prob": p_val,
                        "flow_case": r["case"],
                        "occupation_inspecteur_pct": one_decimal(r["busy_time_mean"]),
                        "arret_grenailleuse_pct": one_decimal(r["blocked_time_mean"]),
                        "bouteilles_inspectees": rounded_int(r["bottles_mean"]),
                        "bouteilles_h_apres_600s": one_decimal(r["bottles_per_hour_after_600_mean"]),
                        "occupation_apres_600s_pct": one_decimal(r["busy_after_600_mean"]),
                    }
                )

    out_path = "compare_runs_grid9.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "grid_case",
                "s",
                "grenailleuse_prob",
                "flow_case",
                "occupation_inspecteur_pct",
                "arret_grenailleuse_pct",
                "bouteilles_inspectees",
                "bouteilles_h_apres_600s",
                "occupation_apres_600s_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: {out_path}")
    print(f"Rows: {len(rows)} (9 grid cases x 6 flow cases)")


if __name__ == "__main__":
    main()

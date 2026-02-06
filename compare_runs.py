import random
from statistics import mean

import numpy as np

import Parameter_horizontal as P
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
    for i in range(n):
        random.seed(seed_base + i)
        np.random.seed(seed_base + i)
        result = fn(plot=False)
        busy_times.append(float(result.get("busy_time", 0.0)))
        blocked_times.append(float(result.get("grenailleuse_blocked_time", 0.0)))
        bottle_counts.append(len(result.get("inspected_times", [])))
        step_times.append(float(result.get("step_time_total", 0.0)))
        cont_times.append(float(result.get("cont_time_total", 0.0)))
        total_times.append(float(result.get("total_time", 0.0)))
    total_mean = mean(total_times) if total_times else 0.0
    def pct(x):
        return (x / total_mean * 100.0) if total_mean else 0.0
    return {
        "case": label,
        "busy_time_mean": pct(mean(busy_times) if busy_times else 0.0),
        "blocked_time_mean": pct(mean(blocked_times) if blocked_times else 0.0),
        "bottles_mean": mean(bottle_counts) if bottle_counts else 0.0,
        "step_time_mean": pct(mean(step_times) if step_times else 0.0),
        "cont_time_mean": pct(mean(cont_times) if cont_times else 0.0),
    }


def print_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, key in enumerate(headers):
            col_widths[idx] = max(col_widths[idx], len(str(row[key])))
    line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(line)
    print(sep)
    for row in rows:
        print(" | ".join(str(row[h]).ljust(col_widths[i]) for i, h in enumerate(headers)))

def one_decimal(value):
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return value


def main():
    n_runs = 10
    results = [
        run_n("robot", run_robot, n_runs),
        run_n("variable", run_variable, n_runs),
        run_n("tempon", run_tempon, n_runs),
    ]

    for row in results:
        for key in (
            "busy_time_mean",
            "blocked_time_mean",
            "step_time_mean",
            "cont_time_mean",
        ):
            row[key] = one_decimal(row[key])

    print("=== Résultats moyens (n=10) ===")
    print_table(
        results,
        [
            "case",
            "busy_time_mean",
            "blocked_time_mean",
            "bottles_mean",
            "step_time_mean",
            "cont_time_mean",
        ],
    )

    params = {
        "mean_interval": P.mean_interval,
        "down_time": P.down_time,
        "min_iter": P.min_iter,
        "max_iter": P.max_iter,
        "inspect_min": P.inspect_min,
        "inspect_max": P.inspect_max,
        "s": P.s,
        "min_long": P.min,
        "max_long": P.max,
        "step_time": P.step_time,
        "step_time_2": getattr(P, "step_time_2", None),
        "steps": P.steps,
        "gr_conv": P.gr_conv,
        "length_first": getattr(P, "length_first", None),
        "length_second": P.length_second,
        "length_third": getattr(P, "length_third", None),
        "horizontal_spacing": P.horizontal_spacing,
        "vertical_spacing": getattr(P, "vertical_spacing", None),
        "first_speed": getattr(P, "first_speed", None),
        "second_speed": P.second_speed,
        "dt": P.dt,
        "env_time": P.env_time,
        "det_hold_time": getattr(P, "det_hold_time", None),
        "mode_switch_delay": getattr(P, "mode_switch_delay", None),
    }

    print("\n=== Paramètres (Parameter_horizontal.py) ===")
    param_rows = [{"param": k, "value": params[k]} for k in params]
    print_table(param_rows, ["param", "value"])


if __name__ == "__main__":
    main()

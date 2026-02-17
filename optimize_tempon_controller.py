import random
from typing import Dict, List, Tuple

import numpy as np

import Parameter_horizontal as PH
from demo_variable_conveyor_tempon import demo_composite_flow as run_tempon


def run_stats(n_runs: int, seed_base: int, **kwargs) -> Dict[str, float]:
    bottles = []
    blocked_pct = []
    busy_pct = []

    for i in range(n_runs):
        seed = seed_base + i
        random.seed(seed)
        np.random.seed(seed)
        result = run_tempon(plot=False, animate=False, **kwargs)

        total_time = float(result.get("total_time", 0.0)) or 1.0
        blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
        busy_time = float(result.get("busy_time", 0.0))

        bottles.append(len(result.get("inspected_times", [])))
        blocked_pct.append(blocked_time * 100.0 / total_time)
        busy_pct.append(busy_time * 100.0 / total_time)

    return {
        "bottles_mean": float(np.mean(bottles)),
        "blocked_mean": float(np.mean(blocked_pct)),
        "busy_mean": float(np.mean(busy_pct)),
    }


def sample_candidate(rng: random.Random) -> Dict[str, float]:
    return {
        "speed_ctrl_control_dt": 1.0,
        "speed_ctrl_window_s": rng.choice([8.0, 12.0, 16.0, 20.0, 24.0, 30.0]),
        "speed_ctrl_slow_band": rng.choice([0.65, 0.70, 0.75, 0.80, 0.85]),
        "speed_ctrl_fast_band": rng.choice([0.10, 0.15, 0.20, 0.25, 0.30]),
        "speed_ctrl_streak_required": rng.choice([2, 3, 4, 5, 6, 8]),
        "speed_ctrl_slow_factor": rng.choice([1.01, 1.02, 1.03, 1.04, 1.05]),
        "speed_ctrl_fast_factor": rng.choice([0.85, 0.88, 0.90, 0.92, 0.95, 0.97]),
        "speed_ctrl_min_step_mult": rng.choice([0.35, 0.40, 0.50, 0.60, 0.70]),
        "speed_ctrl_max_step_mult": rng.choice([1.20, 1.40, 1.60, 1.80, 2.00]),
    }


def score(metrics: Dict[str, float], busy_target: float = 85.0) -> float:
    bottles = metrics["bottles_mean"]
    busy = metrics["busy_mean"]
    blocked = metrics["blocked_mean"]
    busy_penalty = max(0.0, busy_target - busy)
    return bottles - 2.0 * busy_penalty - 0.3 * blocked


def optimize(
    trials: int = 80,
    n_runs: int = 10,
    seed_base: int = 5000,
    rng_seed: int = 42,
) -> Tuple[Dict[str, float], Dict[str, float], List[Tuple[float, Dict[str, float], Dict[str, float]]], Dict[str, float], Dict[str, float]]:
    base_kwargs = {
        "mean_interval": PH.mean_interval,
        "down_time": PH.down_time,
        "min_inter": PH.min_iter,
        "max_inter": PH.max_iter,
        "step_time": PH.step_time,
        "steps": PH.steps,
        "gr_conv": PH.gr_conv,
        "inspect_min": PH.inspect_min,
        "inspect_max": PH.inspect_max,
        "s": PH.s,
        "max_long": PH.max,
        "min_long": PH.min,
        "t_dis": PH.t_dis,
        "t_dis2": PH.t_dis2,
        "env_time": PH.env_time,
        "cont_out_capacity": 1,
        "sample_time": 1.0,
        "horizontal_spacing": PH.horizontal_spacing,
        "vertical_spacing": PH.vertical_spacing,
        "first_speed": PH.first_speed,
        "second_speed": PH.second_speed,
        "speed_tempon": PH.speed_tempon,
        "dt": PH.dt,
        "mode_switch_delay": PH.mode_switch_delay,
        "det_hold_time": PH.det_hold_time,
        "step_time_2": PH.step_time_2,
        "length_first": PH.length_first,
        "length_second": PH.length_second,
        "length_third": PH.length_third,
    }

    fixed_metrics = run_stats(
        n_runs=n_runs,
        seed_base=seed_base,
        variable_speed=False,
        **base_kwargs,
    )

    default_var_metrics = run_stats(
        n_runs=n_runs,
        seed_base=seed_base,
        variable_speed=True,
        **base_kwargs,
    )

    rng = random.Random(rng_seed)
    leaderboard = []
    best = None

    for t in range(trials):
        candidate = sample_candidate(rng)
        metrics = run_stats(
            n_runs=n_runs,
            seed_base=seed_base + 1000 + t * 20,
            variable_speed=True,
            **base_kwargs,
            **candidate,
        )
        s = score(metrics)
        record = (s, candidate, metrics)
        leaderboard.append(record)
        if best is None or s > best[0]:
            best = record

    leaderboard.sort(key=lambda x: x[0], reverse=True)
    assert best is not None
    return best[1], best[2], leaderboard[:10], fixed_metrics, default_var_metrics


def fmt_metrics(name: str, m: Dict[str, float]) -> str:
    return (
        f"{name:<28} | bottles={m['bottles_mean']:.1f} | "
        f"busy={m['busy_mean']:.1f}% | blocked={m['blocked_mean']:.2f}%"
    )


def main() -> None:
    trials = 80
    n_runs = 10

    best_params, best_metrics, top10, fixed_metrics, default_var_metrics = optimize(
        trials=trials,
        n_runs=n_runs,
        seed_base=5000,
        rng_seed=42,
    )

    print("=== Baseline comparison (tampon) ===")
    print(fmt_metrics("No variable speed", fixed_metrics))
    print(fmt_metrics("Variable speed (default)", default_var_metrics))
    print(fmt_metrics("Variable speed (best)", best_metrics))

    print("\n=== Best controller params for variable tampon ===")
    for k in sorted(best_params.keys()):
        print(f"{k} = {best_params[k]}")

    print("\n=== Top 5 candidates ===")
    for idx, (s, params, metrics) in enumerate(top10[:5], start=1):
        print(f"[{idx}] score={s:.2f} | bottles={metrics['bottles_mean']:.1f} | busy={metrics['busy_mean']:.1f}% | blocked={metrics['blocked_mean']:.2f}%")
        print(
            "    "
            + ", ".join(f"{k}={params[k]}" for k in sorted(params.keys()))
        )

    print("\n=== Paste into Parameter_horizontal.py (if desired) ===")
    for k in sorted(best_params.keys()):
        print(f"{k} = {best_params[k]}")


if __name__ == "__main__":
    main()

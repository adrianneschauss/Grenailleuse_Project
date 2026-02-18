import random
from statistics import mean

import numpy as np
import matplotlib.pyplot as plt

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
            if busy_samples:
                occ_after_600.append(float(np.mean(busy_samples)) * 100.0)
            else:
                occ_after_600.append(0.0)
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

def rounded_int(value):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return value


def main():
    n_runs = 3
    results = [
        run_n("Verticale", lambda **kwargs: run_robot(variable_speed=False, **kwargs), n_runs),
        run_n("Horizontale (sans tampon)", lambda **kwargs: run_variable(variable_speed=False, **kwargs), n_runs),
        run_n("Horizontale avec tampon", lambda **kwargs: run_tempon(variable_speed=False, **kwargs), n_runs),
        run_n("Verticale avec Vitesse Variable (Grenailleuse)", lambda **kwargs: run_robot(variable_speed=True, **kwargs), n_runs),
        run_n("Horizontale (sans tampon) avec Vitesse Variable (Grenailleuse)", lambda **kwargs: run_variable(variable_speed=True, **kwargs), n_runs),
        run_n("Horizontale avec tampon et Vitesse Variable (Grenailleuse)", lambda **kwargs: run_tempon(variable_speed=True, **kwargs), n_runs),
    ]

    for row in results:
        for key in (
            "busy_time_mean",
            "busy_after_600_mean",
            "blocked_time_mean",
            "bottles_per_hour_after_600_mean",
            "step_time_mean",
            "cont_time_mean",
        ):
            row[key] = one_decimal(row[key])
        row["bottles_mean"] = rounded_int(row["bottles_mean"])

    display_headers = [
        "Cas",
        "Occupation inspecteur (%)",
        "Arrêt grenailleuse (%)",
        "Bouteilles inspectées",
        "Bouteilles/h (après 600s)",
        "Occupation inspecteur % (après 600s)",
        "Temps pas à pas (%)",
        "Temps continu (%)",
    ]
    display_rows = []
    for row in results:
        display_rows.append(
            {
                "Cas": row["case"],
                "Occupation inspecteur (%)": row["busy_time_mean"],
                "Arrêt grenailleuse (%)": row["blocked_time_mean"],
                "Bouteilles inspectées": row["bottles_mean"],
                "Bouteilles/h (après 600s)": row["bottles_per_hour_after_600_mean"],
                "Occupation inspecteur % (après 600s)": row["busy_after_600_mean"],
                "Temps pas à pas (%)": row["step_time_mean"],
                "Temps continu (%)": row["cont_time_mean"],
            }
        )
    print("=== Résultats moyens (n=10) ===")
    print_table(display_rows, display_headers)

    params_common = [
        ("Intervalle moyen (s)", P.mean_interval),
        ("Probabilité d'arrêt", P.down_time),
        ("Interruption min (s)", P.min_iter),
        ("Interruption max (s)", P.max_iter),
        ("Temps de pas (s)", P.step_time),
        ("Nombre d'étapes", P.steps),
        ("Déchargement vers convoyeur (s)", P.gr_conv),
        ("Variation de Vitesse", getattr(P, "variable_speed", None)),
        ("Inspection min (s)", P.inspect_min),
        ("Inspection max (s)", P.inspect_max),
        ("Probabilité pause longue", P.s),
        ("Pause longue min (s)", P.min),
        ("Pause longue max (s)", P.max),
        ("Délai de chargement (s)", P.t_dis2),
        ("Délai de déchargement (s)", P.t_dis),
        ("Temps de simulation (s)", P.env_time),
        ("Capacité du tampon avant inspection", 1),
        ("Temps d'échantillonnage (s)", 1.0),
    ]

    params_horizontal_only = [
        ("Espacement horizontal (cm)", P.horizontal_spacing),
        ("Espacement vertical (cm)", getattr(P, "vertical_spacing", None)),
        ("Vitesse convoyeur (cm/s) variable", getattr(P, "first_speed", None)),
        ("Vitesse convoyeur (cm/s) continu", P.second_speed),
        ("Vitesse tampon (cm/s)", getattr(P, "speed_tempon", None)),
        ("Pas de temps (dt en s)", P.dt),
        ("Délai changement mode (s)", getattr(P, "mode_switch_delay", None)),
        ("Temps déclenchement détecteurs (s)", getattr(P, "det_hold_time", None)),
        ("Temps de pas variable (s)", getattr(P, "step_time_2", None)),
        ("Longueur convoyeur 1 (cm)", getattr(P, "length_first", None)),
        ("Longueur convoyeur 2 (cm)", P.length_second),
        ("Longueur convoyeur 3 (cm)", getattr(P, "length_third", None)),
    ]

    params_vertical_only = [
        ("Longueur (cm)", P.length),
        ("Espacement (cm)", P.spacing),
        ("Vitesse (cm/min)", P.speed),
    ]

    print("\n=== Paramètres (Communs) ===")
    param_rows = [{"param": k, "value": v} for k, v in params_common]
    print_table(param_rows, ["param", "value"])

    print("\n=== Paramètres (Horizontale seulement) ===")
    param_rows = [{"param": k, "value": v} for k, v in params_horizontal_only]
    print_table(param_rows, ["param", "value"])

    print("\n=== Paramètres (Verticale seulement) ===")
    param_rows = [{"param": k, "value": v} for k, v in params_vertical_only]
    print_table(param_rows, ["param", "value"])

    print("\n=== Graphe vitesse grenailleuse ===")
    random.seed(777)
    np.random.seed(777)
    speed_traces = [
        ("Verticale (var)", run_robot(variable_speed=True, plot=False)),
        ("Horizontale sans tampon (var)", run_variable(variable_speed=True, plot=False)),
        ("Horizontale avec tampon (var)", run_tempon(variable_speed=True, plot=False)),
    ]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for label, result in speed_traces:
        monitor = result.get("monitor", {}) or {}
        t_vals = monitor.get("t", []) or []
        speed_vals = monitor.get("grenailleuse_speed_hz", []) or []
        if t_vals and speed_vals:
            ax.plot(t_vals, speed_vals, label=label, linewidth=1.8)

    ax.set_title("Evolution de la vitesse grenailleuse (1 / step_time)")
    ax.set_xlabel("Temps simulation (s)")
    ax.set_ylabel("Vitesse grenailleuse (Hz)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    out_path = "compare_runs_grenailleuse_speed.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")
    plt.show()


if __name__ == "__main__":
    main()

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
    n_runs = 4
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
            "blocked_time_mean",
            "step_time_mean",
            "cont_time_mean",
        ):
            row[key] = one_decimal(row[key])

    display_headers = [
        "Cas",
        "Occupation inspecteur (%)",
        "Arrêt grenailleuse (%)",
        "Bouteilles inspectées",
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


if __name__ == "__main__":
    main()

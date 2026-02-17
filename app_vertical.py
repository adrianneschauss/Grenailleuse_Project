import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

import Parameter_horizontal as Parameter
from demo_composite_flow_robot import demo_composite_flow
from sidebar_verticale import build_sidebar


st.set_page_config(page_title="Simulateur de Grenailleuse avec Bouteilles en Verticale (avec Robot)", layout="wide")
st.title("Simulateur de Grenailleuse avec Bouteilles en Verticale (avec Robot)")

sidebar = build_sidebar(Parameter)

result = demo_composite_flow(
    variable_speed=sidebar["variable_speed"],
    mean_interval=sidebar["mean_interval"],
    down_time=sidebar["down_time"],
    min_inter=sidebar["min_inter"],
    max_inter=sidebar["max_inter"],
    t_dis=sidebar["t_dis"],
    t_dis2=sidebar["t_dis2"],
    inspect_min=sidebar["inspect_min"],
    inspect_max=sidebar["inspect_max"],
    max_long=sidebar["max_long"],
    min_long=sidebar["min_long"],
    s=sidebar["s"],
    step_time=sidebar["step_time"],
    steps=sidebar["steps"],
    gr_conv=sidebar["gr_conv"],
    cont_out_capacity=sidebar["cont_out_capacity"],
    length=sidebar["length"],
    spacing=sidebar["spacing"],
    speed=sidebar["speed"],
    dt=Parameter.dt,
    env_time=sidebar["env_time"],
    sample_time=sidebar["sample_time"],
    plot=False,
)

st.subheader("Résumé")
total_time = float(result.get("total_time", 0.0))
busy_time = float(result.get("busy_time", 0.0))
blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
inspected_count = len(result["inspected_times"])
inspected_after_10min = sum(1 for t in result["inspected_times"] if t >= 600.0)
duration_after_10min = max(0.0, total_time - 600.0)
rate_after_10min = np.round((inspected_after_10min * 3600.0 / duration_after_10min), 2) if duration_after_10min else 0.0
def pct(value, total):
    return np.round((value * 100.0 / total), 2) if total else 0.0
resume_rows = [
    {"Metric": "Inspectées", "Valeur": inspected_count},
    {"Metric": "Bouteilles/heure après 10 min", "Valeur": rate_after_10min},
    {"Metric": "Bouteilles/heure", "Valeur": np.round((inspected_count * 3600.0 / total_time), 2) if total_time else 0.0},
    {"Metric": "Temps total (s)", "Valeur": np.round(total_time, 2)},
    {"Metric": "% temps d'occupation inspecteur", "Valeur": pct(busy_time, total_time)},
    {"Metric": "% temps arret de grenailleuse", "Valeur": pct(blocked_time, total_time)},
]
st.table(resume_rows)

inspected_times = result["inspected_times"]
if inspected_times:
    inspected_times_sorted = sorted(inspected_times)
    counts = list(range(1, len(inspected_times_sorted) + 1))
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.plot(inspected_times_sorted, counts, linestyle="-", color="#00c8ff", label="Cumul")
    marker_idx = [i for i, c in enumerate(counts) if c % 50 == 0]
    if marker_idx:
        marker_times = [inspected_times_sorted[i] for i in marker_idx]
        marker_counts = [counts[i] for i in marker_idx]
        ax.plot(
            marker_times,
            marker_counts,
            linestyle="None",
            marker="o",
            color="#ff9f1a",
            label="Marqueur / 50",
        )
    ax.set_xlabel("Temps", color="white")
    ax.set_ylabel("Bouteilles inspectées cumulées", color="white")
    ax.set_title("Sortie des bouteilles dans le temps", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")
    ax.grid(True, color="#444444", alpha=0.6)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    st.pyplot(fig)
else:
    st.info("Aucune bouteille inspectée pour l'instant.")


st.subheader("Goulot d'étranglement de la ligne")

def cumulative_series(times):
    if not times:
        return [], []
    times_sorted = sorted(times)
    counts = list(range(1, len(times_sorted) + 1))
    return times_sorted, counts

monitor = result["monitor"]
fig, ax1 = plt.subplots()
fig.patch.set_facecolor("black")
ax1.set_facecolor("black")

arrival_t, arrival_c = cumulative_series(result["arrival_times"])
inspect_t, inspect_c = cumulative_series(result["inspected_times"])

if arrival_t:
    ax1.step(
        arrival_t,
        arrival_c,
        where="post",
        color="#a36be6",
        label="Bouteilles arrivées (cumulatif)",
    )
if inspect_t:
    ax1.step(
        inspect_t,
        inspect_c,
        where="post",
        color="#2bd92b",
        label="Bouteilles inspectées (cumulatif)",
    )
gren_t, gren_c = cumulative_series(result["grenailleuse_exit_times"])
conv_t, conv_c = cumulative_series(result["conveyor_exit_times"])
if gren_t:
    ax1.step(
        gren_t,
        gren_c,
        where="post",
        color="#00c8ff",
        label="Sortie grenailleuse (cumulatif)",
    )
if conv_t:
    ax1.step(
        conv_t,
        conv_c,
        where="post",
        color="#ff9f1a",
        label="Sortie convoyeur continu (cumulatif)",
    )

ax1.set_xlabel("Temps (sec)", color="white")
ax1.set_ylabel("Nb de bouteilles", color="white")
ax1.set_title("Fonctionnement de la ligne de production", color="white")

ax1.tick_params(colors="white")
for spine in ax1.spines.values():
    spine.set_color("white")
ax1.grid(True, color="#444444", alpha=0.6)

handles1, labels1 = ax1.get_legend_handles_labels()
ax1.legend(handles1, labels1, loc="center left", bbox_to_anchor=(1.02, 0.5))

st.pyplot(fig)

st.subheader("Occupation de l'inspecteur")
fig2, ax_left = plt.subplots()
fig2.patch.set_facecolor("black")
ax_left.set_facecolor("black")

ax_left.step(
    monitor["t"],
    monitor["inspector_busy"],
    where="post",
    color="#e6e600",
    linestyle="-",
    label="Occupation de l'inspecteur",
)

ax_left.set_xlabel("Temps (sec)", color="white")
ax_left.set_ylabel("Occupation opérateur", color="white")
ax_left.set_title("Occupation de l'inspecteur", color="white")

ax_left.tick_params(colors="white")
for spine in ax_left.spines.values():
    spine.set_color("white")
ax_left.grid(True, color="#444444", alpha=0.6)

handles1, labels1 = ax_left.get_legend_handles_labels()
ax_left.legend(handles1, labels1, loc="center left", bbox_to_anchor=(1.02, 0.5))
st.pyplot(fig2)

st.subheader("Retard entre arrivées")
arrival_times = result["arrival_times"]
if len(arrival_times) > 1:
    arrival_times_sorted = sorted(arrival_times)
    deltas = [arrival_times_sorted[i] - arrival_times_sorted[i - 1] for i in range(1, len(arrival_times_sorted))]
    delays = [max(0.0, d - sidebar["mean_interval"]) for d in deltas]
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    fig3.patch.set_facecolor("black")
    ax3.set_facecolor("black")
    ax3.plot(arrival_times_sorted[1:], delays, linestyle="-", color="#00c8ff")
    ax3.set_xlabel("Temps", color="white")
    ax3.set_ylabel("Retard vs intervalle moyen (s)", color="white")
    ax3.set_title("Retard d'arrivée des bouteilles", color="white")
    ax3.tick_params(colors="white")
    for spine in ax3.spines.values():
        spine.set_color("white")
    ax3.grid(True, color="#444444", alpha=0.6)
    st.pyplot(fig3)
else:
    st.info("Pas assez d'arrivées pour calculer les retards.")

st.subheader("Distribution des arrivées")
if len(arrival_times) > 1:
    arrival_times_sorted = sorted(arrival_times)
    inter = [arrival_times_sorted[i] - arrival_times_sorted[i - 1] for i in range(1, len(arrival_times_sorted))]
    fig_arr, ax_arr = plt.subplots(figsize=(6, 4))
    fig_arr.patch.set_facecolor("black")
    ax_arr.set_facecolor("black")
    ax_arr.hist(inter, bins=20, color="#2bd92b", alpha=0.8)
    mean_inter = float(np.mean(inter)) if inter else 0.0
    ax_arr.axvline(mean_inter, color="#ff9f1a", linestyle="--", linewidth=2, label=f"Moyenne = {mean_inter:.2f}s")
    ax_arr.set_xlabel("Temps entre arrivées (s)", color="white")
    ax_arr.set_ylabel("Nombre", color="white")
    ax_arr.set_title("Distribution des arrivées fixes", color="white")
    ax_arr.tick_params(colors="white")
    for spine in ax_arr.spines.values():
        spine.set_color("white")
    ax_arr.grid(True, color="#444444", alpha=0.6)
    ax_arr.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    st.pyplot(fig_arr)
else:
    st.info("Pas assez d'arrivées pour la distribution.")

st.subheader("Occupation du convoyeur continu")
cont_times = monitor.get("t", [])
cont_counts = monitor.get("cont_items", [])
fallback_counts = monitor.get("cont_out", [])
plot_counts = cont_counts if cont_counts else fallback_counts
if cont_times and plot_counts:
    fig_occ, ax_occ = plt.subplots(figsize=(6, 4))
    fig_occ.patch.set_facecolor("black")
    ax_occ.set_facecolor("black")
    ax_occ.plot(cont_times, plot_counts, linestyle="-", color="#00c8ff", label="Occupation")
    full_idx = [
        i for i, c in enumerate(fallback_counts)
        if c >= sidebar["cont_out_capacity"]
    ]
    if full_idx:
        full_t = [cont_times[i] for i in full_idx]
        full_c = [plot_counts[i] for i in full_idx]
        ax_occ.plot(
            full_t,
            full_c,
            linestyle="None",
            marker="o",
            color="#ff9f1a",
            label="Tampon plein",
        )
    ax_occ.set_xlabel("Temps", color="white")
    ax_occ.set_ylabel("Bouteilles", color="white")
    ax_occ.set_title("Occupation du convoyeur continu dans le temps", color="white")
    ax_occ.tick_params(colors="white")
    for spine in ax_occ.spines.values():
        spine.set_color("white")
    ax_occ.grid(True, color="#444444", alpha=0.6)
    ax_occ.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    st.pyplot(fig_occ)
else:
    st.info("Pas assez de données pour l'occupation du convoyeur continu.")

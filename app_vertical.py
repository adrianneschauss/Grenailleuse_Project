import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

import Parameter_horizontal as Parameter
from demo_composite_flow_robot import demo_composite_flow


st.set_page_config(page_title="Simulateur de Grenailleuse avec Bouteilles en Verticale (avec Robot)", layout="wide")
st.title("Simulateur de Grenailleuse avec Bouteilles en Verticale (avec Robot)")

st.sidebar.header("Arrivée")
mean_interval = st.sidebar.number_input(
    "Intervalle moyen (s)", min_value=0.1, value=float(Parameter.mean_interval), step=1.0
)
down_time = st.sidebar.slider(
    "Probabilité d'arrêt", min_value=0.0, max_value=1.0, value=float(Parameter.down_time)
)
min_inter = st.sidebar.number_input(
    "Interruption min (s)", min_value=0.0, value=float(Parameter.min_iter), step=1.0
)
max_inter = st.sidebar.number_input(
    "Interruption max (s)", min_value=0.0, value=float(Parameter.max_iter), step=1.0
)

st.sidebar.header("Grenailleuse")
step_time = st.sidebar.number_input(
    "Temps de pas (s)", min_value=0.1, value=float(Parameter.step_time), step=1.0
)
steps = st.sidebar.number_input(
    "Nombre d'étapes", min_value=1, value=int(Parameter.steps), step=1
)
gr_conv = st.sidebar.number_input(
    "Déchargement vers convoyeur (s)", min_value=0.0, value=float(Parameter.gr_conv), step=1.0
)
variable_speed = st.sidebar.checkbox(
    "Variation de Vitesse", value=bool(getattr(Parameter, "variable_speed", False))
)

st.sidebar.header("Convoyeur continu")
length = st.sidebar.number_input(
    "Longueur (cm)", min_value=0.1, value=float(Parameter.length), step=0.1
)
spacing = st.sidebar.number_input(
    "Espacement (cm)", min_value=0.1, value=float(Parameter.spacing), step=0.1
)
speed = st.sidebar.number_input(
    "Vitesse (cm/min)", min_value=0.1, value=float(Parameter.speed), step=0.1
)
dt = st.sidebar.number_input(
    "Pas de temps (dt en s)", min_value=0.1, value=float(Parameter.dt), step=0.1
)

st.sidebar.header("Inspecteur")
inspect_min = st.sidebar.number_input(
    "Inspection min (s)", min_value=0.1, value=float(Parameter.inspect_min), step=1.0
)
inspect_max = st.sidebar.number_input(
    "Inspection max (s)", min_value=0.1, value=float(Parameter.inspect_max), step=1.0
)
s = st.sidebar.slider(
    "Probabilité pause longue", min_value=0.0, max_value=1.0, value=float(Parameter.s), step=0.01
)
min_long = st.sidebar.slider(
    "Pause longue min (s)", min_value=0.0, max_value=200.0, value=float(Parameter.min), step=1.0
)
max_long = st.sidebar.slider(
    "Pause longue max (s)", min_value=0.0, max_value=200.0, value=float(Parameter.max), step=1.0
)
t_dis = st.sidebar.number_input(
    "Délai de chargement (s)", min_value=0.0, value=float(Parameter.t_dis2), step=1.0
)
t_dis2 = st.sidebar.number_input(
    "Délai de déchargement (s)", min_value=0.0, value=float(Parameter.t_dis), step=1.0
)

st.sidebar.header("Lancement")
env_time = st.sidebar.number_input(
    "Temps de simulation (s)", min_value=1.0, value=float(Parameter.env_time), step=10.0
)
cont_out_capacity = st.sidebar.number_input(
    "Capacité du tampon avant inspection", min_value=1, value=1, step=1
)
sample_time = st.sidebar.number_input(
    "Temps d'échantillonnage (s)", min_value=0.1, value=1.0, step=0.1
)

result = demo_composite_flow(
    variable_speed=variable_speed,
    mean_interval=mean_interval,
    down_time=down_time,
    min_inter=min_inter,
    max_inter=max_inter,
    t_dis=t_dis,
    t_dis2=t_dis2,
    inspect_min=inspect_min,
    inspect_max=inspect_max,
    max_long=max_long,
    min_long=min_long,
    s=s,
    step_time=step_time,
    steps=steps,
    gr_conv=gr_conv,
    cont_out_capacity=cont_out_capacity,
    length=length,
    spacing=spacing,
    speed=speed,
    dt=dt,
    env_time=env_time,
    sample_time=sample_time,
    plot=False,
)

st.subheader("Résumé")
total_time = float(result.get("total_time", 0.0))
busy_time = float(result.get("busy_time", 0.0))
blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
def pct(value, total):
    return np.round((value * 100.0 / total), 2) if total else 0.0
resume_rows = [
    {"Metric": "Inspectées", "Valeur": np.round(float(len(result["inspected_times"])), 2)},
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
    delays = [max(0.0, d - mean_interval) for d in deltas]
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
    full_idx = [i for i, c in enumerate(fallback_counts) if c >= cont_out_capacity]
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

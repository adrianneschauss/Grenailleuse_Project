import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

import Parameter_horizontal as Parameter
from demo_composite_horizontal import demo_composite_flow


def to_float(value):
    if isinstance(value, tuple):
        return float("".join(str(part) for part in value))
    return float(value)


st.set_page_config(page_title="Simulateur Grenailleuse avec Bouteilles en Horizontale", layout="wide")
st.title("Simulateur de grenailleuse - Ligne horizontale")

st.sidebar.header("Arrivée")
mean_interval = st.sidebar.number_input(
    "Intervalle moyen (s)", min_value=0.1, value=to_float(Parameter.mean_interval), step=1.0
)
down_time = st.sidebar.slider(
    "Probabilité d'arrêt", min_value=0.0, max_value=1.0, value=to_float(Parameter.down_time)
)
min_inter = st.sidebar.number_input(
    "Interruption min (s)", min_value=0.0, value=to_float(Parameter.min_iter), step=1.0
)
max_inter = st.sidebar.number_input(
    "Interruption max (s)", min_value=0.0, value=to_float(Parameter.max_iter), step=1.0
)

st.sidebar.header("Grenailleuse")
step_time = st.sidebar.number_input(
    "Temps de pas (s)", min_value=0.1, value=to_float(Parameter.step_time), step=1.0
)
steps = st.sidebar.number_input(
    "Nombre d'étapes", min_value=1, value=int(to_float(Parameter.steps)), step=1
)
gr_conv = st.sidebar.number_input(
    "Déchargement vers convoyeur (s)", min_value=0.0, value=to_float(Parameter.gr_conv), step=1.0
)

st.sidebar.header("Convoyeurs horizontaux")
length_first = st.sidebar.number_input(
    "Longueur convoyeur 1 (cm)", min_value=0.1, value=to_float(Parameter.length_first), step=0.1
)
length_second = st.sidebar.number_input(
    "Longueur convoyeur 2 (cm)", min_value=0.1, value=to_float(Parameter.length_second), step=0.1
)
horizontal_spacing = st.sidebar.number_input(
    "Espacement horizontal (cm)", min_value=0.1, value=to_float(Parameter.horizontal_spacing), step=0.1
)
first_speed = st.sidebar.number_input(
    "Vitesse convoyeur 1 (cm/min)", min_value=0.1, value=to_float(Parameter.first_speed), step=0.1
)
second_speed = st.sidebar.number_input(
    "Vitesse convoyeur 2 (cm/min)", min_value=0.1, value=to_float(Parameter.second_speed), step=0.1
)
dt = st.sidebar.number_input(
    "Pas de temps (dt en s)", min_value=0.1, value=to_float(Parameter.dt), step=0.1
)

st.sidebar.header("Inspecteur")
inspect_min = st.sidebar.number_input(
    "Inspection min (s)", min_value=0.1, value=to_float(Parameter.inspect_min), step=1.0
)
inspect_max = st.sidebar.number_input(
    "Inspection max (s)", min_value=0.1, value=to_float(Parameter.inspect_max), step=1.0
)
t_dis = st.sidebar.number_input(
    "Délai de chargement (s)", min_value=0.0, value=to_float(Parameter.t_dis2), step=1.0
)
t_dis2 = st.sidebar.number_input(
    "Délai de déchargement (s)", min_value=0.0, value=to_float(Parameter.t_dis), step=1.0
)

st.sidebar.header("Lancement")
env_time = st.sidebar.number_input(
    "Temps de simulation (s)", min_value=1.0, value=to_float(Parameter.env_time), step=10.0
)
cont_out_capacity = st.sidebar.number_input(
    "Capacité du tampon avant inspection", min_value=1, value=1, step=1
)
sample_time = st.sidebar.number_input(
    "Temps d'échantillonnage (s)", min_value=0.1, value=1.0, step=0.1
)

result = demo_composite_flow(
    mean_interval=mean_interval,
    down_time=down_time,
    min_inter=min_inter,
    max_inter=max_inter,
    t_dis=t_dis,
    t_dis2=t_dis2,
    inspect_min=inspect_min,
    inspect_max=inspect_max,
    step_time=step_time,
    steps=steps,
    gr_conv=gr_conv,
    cont_out_capacity=cont_out_capacity,
    length=length_second,
    length_first=length_first,
    length_second=length_second,
    spacing=horizontal_spacing,
    horizontal_spacing=horizontal_spacing,
    speed=second_speed,
    first_speed=first_speed,
    second_speed=second_speed,
    dt=dt,
    env_time=env_time,
    sample_time=sample_time,
    plot=False,
)

st.subheader("Résumé")
st.write(
    {
        "Inspectées": len(result["inspected_times"]),
        "Temps occupation": np.round(float(result["busy_time"]), 2),
        "Temps total": result["total_time"],
        "% du temps occupé": np.round(float(result["busy_time"] * 100 / result["total_time"]), 3),
    }
)

inspected_times = result["inspected_times"]
if inspected_times:
    inspected_times_sorted = sorted(inspected_times)
    counts = list(range(1, len(inspected_times_sorted) + 1))
    fig, ax = plt.subplots()
    ax.plot(inspected_times_sorted, counts, marker="x", linestyle="-")
    ax.set_xlabel("Temps")
    ax.set_ylabel("Bouteilles inspectées cumulées")
    ax.set_title("Sortie des bouteilles dans le temps")
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
ax1.step(
    monitor["t"],
    monitor["cont_out_1"],
    where="post",
    color="#ff4d4d",
    label="Tampon convoyeur 1",
)
ax1.step(
    monitor["t"],
    monitor["cont_out_2"],
    where="post",
    color="#ff9f1a",
    label="Tampon convoyeur 2",
)
ax1.step(
    monitor["t"],
    monitor["inspect_buffer"],
    where="post",
    color="#4d79ff",
    label="Tampon inspecteur",
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
conv1_t, conv1_c = cumulative_series(result["conveyor_exit_times_1"])
conv2_t, conv2_c = cumulative_series(result["conveyor_exit_times_2"])
if gren_t:
    ax1.step(
        gren_t,
        gren_c,
        where="post",
        color="#00c8ff",
        label="Sortie grenailleuse (cumulatif)",
    )
if conv1_t:
    ax1.step(
        conv1_t,
        conv1_c,
        where="post",
        color="#ffd166",
        label="Sortie convoyeur 1 (cumulatif)",
    )
if conv2_t:
    ax1.step(
        conv2_t,
        conv2_c,
        where="post",
        color="#ff6f61",
        label="Sortie convoyeur 2 (cumulatif)",
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

handles2, labels2 = ax_left.get_legend_handles_labels()
ax_left.legend(handles2, labels2, loc="center left", bbox_to_anchor=(1.02, 0.5))
st.pyplot(fig2)

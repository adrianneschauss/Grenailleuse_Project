import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from matplotlib import animation

import Parameter_horizontal as Parameter
from demo_variable_conveyor import demo_composite_flow


def to_float(value):
    if isinstance(value, tuple):
        return float("".join(str(part) for part in value))
    return float(value)


st.set_page_config(page_title="Simulateur de Grenailleuse Variable (Horizontal)", layout="wide")
st.title("Simulateur de Grenailleuse Variable (Horizontal)")

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

st.sidebar.header("Convoyeur horizontal variable")
length_second = st.sidebar.number_input(
    "Longueur convoyeur (cm)", min_value=0.1, value=to_float(Parameter.length_second), step=0.1
)
horizontal_spacing = st.sidebar.number_input(
    "Espacement horizontal (cm)", min_value=0.1, value=to_float(Parameter.horizontal_spacing), step=0.1
)
second_speed = st.sidebar.number_input(
    "Vitesse convoyeur (cm/min)", min_value=0.1, value=to_float(Parameter.second_speed), step=0.1
)
dt = st.sidebar.number_input(
    "Pas de temps (dt en s)", min_value=0.1, value=to_float(Parameter.dt), step=0.1
)
mode_switch_delay = st.sidebar.number_input(
    "Délai changement mode (s)", min_value=0.0, value=to_float(Parameter.mode_switch_delay), step=0.1
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
hold_at_det2 = st.sidebar.number_input(
    "Attente det2 (s)", min_value=0.0, value=to_float(Parameter.hold_at_det2), step=1.0
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
show_animation = st.sidebar.checkbox("Afficher animation", value=True)
animation_interval_ms = st.sidebar.number_input(
    "Animation interval (ms)", min_value=10, value=50, step=10
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
    length_second=length_second,
    spacing=horizontal_spacing,
    horizontal_spacing=horizontal_spacing,
    speed=second_speed,
    second_speed=second_speed,
    dt=dt,
    env_time=env_time,
    sample_time=sample_time,
    plot=False,
    mode_switch_delay=mode_switch_delay,
    hold_at_det2=hold_at_det2,
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
    monitor["cont_out"],
    where="post",
    color="#ff9f1a",
    label="Tampon convoyeur",
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
        color="#ff6f61",
        label="Sortie convoyeur (cumulatif)",
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

st.subheader("Retard entre arrivées")
arrival_times = result["arrival_times"]
if len(arrival_times) > 1:
    arrival_times_sorted = sorted(arrival_times)
    deltas = [arrival_times_sorted[i] - arrival_times_sorted[i - 1] for i in range(1, len(arrival_times_sorted))]
    delays = [max(0.0, d - mean_interval) for d in deltas]
    fig3, ax3 = plt.subplots()
    ax3.plot(arrival_times_sorted[1:], delays, marker="o", linestyle="-")
    ax3.set_xlabel("Temps")
    ax3.set_ylabel("Retard vs intervalle moyen (s)")
    ax3.set_title("Retard d'arrivée des bouteilles")
    st.pyplot(fig3)
else:
    st.info("Pas assez d'arrivées pour calculer les retards.")

if show_animation:
    position_log = result.get("position_log", {})
    times = position_log.get("t", [])
    positions = position_log.get("positions", [])
    if times and positions:
        inspector_arrivals = result.get("inspector_arrival_times", [])
        arrivals_sorted = sorted(inspector_arrivals)
        arrival_counts = []
        arrival_idx = 0
        for t in times:
            while arrival_idx < len(arrivals_sorted) and arrivals_sorted[arrival_idx] <= t:
                arrival_idx += 1
            arrival_counts.append(arrival_idx)

        fig_anim, ax_anim = plt.subplots(figsize=(8, 2.5))
        ax_anim.set_xlim(-horizontal_spacing, length_second + horizontal_spacing)
        ax_anim.set_ylim(-1, 1.5)
        ax_anim.set_yticks([])
        ax_anim.set_xlabel("Conveyor position")
        ax_anim.set_title("Variable Conveyor Bottle Movement")

        ax_anim.hlines(0, 0, length_second, color="black", linewidth=2)
        ax_anim.vlines(0, -0.2, 0.2, color="tab:green", linewidth=2)
        ax_anim.vlines(length_second, -0.2, 0.2, color="tab:red", linewidth=2)
        ax_anim.text(0, 0.35, "Step G exit", ha="left", va="bottom", fontsize=9)
        ax_anim.text(length_second, 0.35, "Inspector", ha="right", va="bottom", fontsize=9)

        scat = ax_anim.scatter([], [], s=60, color="tab:blue")
        header = ax_anim.text(0.5, 1.05, "", transform=ax_anim.transAxes, ha="center", fontsize=9)

        def init_anim():
            scat.set_offsets(np.empty((0, 2)))
            header.set_text("")
            return scat, header

        def update_anim(frame):
            frame_positions = positions[frame]
            offsets = (
                np.column_stack((frame_positions, np.zeros(len(frame_positions))))
                if frame_positions
                else np.empty((0, 2))
            )
            scat.set_offsets(offsets)
            mode = "STEP" if position_log.get("step_mode", [False])[frame] else "CONT"
            det1 = position_log.get("det1", [0])[frame]
            det2 = position_log.get("det2", [0])[frame]
            det3 = position_log.get("det3", [0])[frame]
            det4 = position_log.get("det4", [0])[frame]
            header.set_text(
                "Mode: "
                f"{mode} | det1:{det1} det2:{det2} det3:{det3} det4:{det4}"
                f" | Arrived: {arrival_counts[frame]}"
            )
            return scat, header

        anim = animation.FuncAnimation(
            fig_anim,
            update_anim,
            frames=len(times),
            init_func=init_anim,
            interval=animation_interval_ms,
            blit=False,
        )
        html = anim.to_jshtml()
        components.html(html, height=260)
    else:
        st.info("Animation indisponible : aucune position enregistrée.")

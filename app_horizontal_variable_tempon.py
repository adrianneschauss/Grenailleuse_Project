import matplotlib.pyplot as plt
import matplotlib as mpl
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from matplotlib import animation

# Allow larger embedded animations in Streamlit.
mpl.rcParams["animation.embed_limit"] = 200

import Parameter_horizontal as Parameter
from demo_variable_conveyor_tempon import demo_composite_flow


def to_float(value):
    if isinstance(value, tuple):
        return float("".join(str(part) for part in value))
    return float(value)


st.set_page_config(page_title="Simulateur de Grenailleuse Variable (Horizontal) avec Tampon", layout="wide")
st.title("Simulateur de Grenailleuse Variable (Horizontal) avec Tampon")

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
variable_speed = st.sidebar.checkbox(
    "Variation de Vitesse", value=bool(getattr(Parameter, "variable_speed", False))
)

st.sidebar.header("Convoyeur horizontal variable")
horizontal_spacing = st.sidebar.number_input(
    "Espacement horizontal (cm)", min_value=0.1, value=to_float(Parameter.horizontal_spacing), step=0.1
)
vertical_spacing = st.sidebar.number_input(
    "Espacement vertical (cm)", min_value=0.1, value=to_float(Parameter.vertical_spacing), step=0.1
)
second_speed = st.sidebar.number_input(
    "Vitesse convoyeur (cm/s)", min_value=0.1, value=to_float(Parameter.second_speed), step=0.1
)
dt = st.sidebar.number_input(
    "Pas de temps (dt en s)", min_value=0.1, value=to_float(Parameter.dt), step=0.1
)
mode_switch_delay = st.sidebar.number_input(
    "Délai changement mode (s)", min_value=0.0, value=to_float(Parameter.mode_switch_delay), step=0.1
)

st.sidebar.header("Paramètres convoyeur variable")
det_hold_time = st.sidebar.number_input(
    "Temps déclenchement détecteurs (s)", min_value=0.0, value=to_float(Parameter.det_hold_time), step=0.1
)
step_time_2 = st.sidebar.number_input(
    "Temps de pas variable (s)", min_value=0.1, value=to_float(Parameter.step_time_2), step=0.1
)
length_first = st.sidebar.number_input(
    "Longueur convoyeur 1 (cm)", min_value=0.1, value=to_float(Parameter.length_first), step=0.1
)
length_second = st.sidebar.number_input(
    "Longueur convoyeur 2 (cm)", min_value=0.1, value=to_float(Parameter.length_second), step=0.1
)
length_third = st.sidebar.number_input(
    "Longueur convoyeur 3 (cm)", min_value=0.1, value=to_float(Parameter.length_third), step=0.1
)

st.sidebar.header("Inspecteur")
inspect_min = st.sidebar.number_input(
    "Inspection min (s)", min_value=0.1, value=to_float(Parameter.inspect_min), step=1.0
)
inspect_max = st.sidebar.number_input(
    "Inspection max (s)", min_value=0.1, value=to_float(Parameter.inspect_max), step=1.0
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
show_animation = st.sidebar.checkbox("Afficher animation", value=True)
animation_interval_ms = st.sidebar.number_input(
    "Animation interval (ms)", min_value=10, value=50, step=10
)
animation_mode = st.sidebar.selectbox(
    "Mode animation",
    ["Auto", "Interactif", "Statique"],
    index=0,
)
show_static_preview = st.sidebar.checkbox("Aperçu statique", value=True)

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
    step_time_2=step_time_2,
    steps=steps,
    gr_conv=gr_conv,
    cont_out_capacity=cont_out_capacity,
    length=length_second,
    length_first=length_first,
    length_second=length_second,
    length_third=length_third,
    spacing=horizontal_spacing,
    horizontal_spacing=horizontal_spacing,
    vertical_spacing=vertical_spacing,
    speed=second_speed,
    second_speed=second_speed,
    dt=dt,
    env_time=env_time,
    sample_time=sample_time,
    plot=False,
    mode_switch_delay=mode_switch_delay,
    det_hold_time=det_hold_time,
)

st.subheader("Résumé")
total_time = float(result.get("total_time", 0.0))
step_time_total = float(result.get("step_time_total", 0.0))
cont_time_total = float(result.get("cont_time_total", 0.0))
busy_time = float(result.get("busy_time", 0.0))
blocked_time = float(result.get("grenailleuse_blocked_time", 0.0))
def pct(value, total):
    return np.round((value * 100.0 / total), 2) if total else 0.0
resume_rows = [
    {"Metric": "Inspectées", "Valeur": len(result["inspected_times"])},
    {"Metric": "Temps total (s)", "Valeur": np.round(total_time, 2)},
    {"Metric": "% temps pas a pas", "Valeur": pct(step_time_total, total_time)},
    {"Metric": "% temps continu", "Valeur": pct(cont_time_total, total_time)},
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

st.subheader("Occupation du convoyeur variable")
position_log = result.get("position_log", {})
times = position_log.get("t", [])
positions = position_log.get("positions", [])
if times and positions:
    var_counts = [len(p) for p in positions]
    fig_occ, ax_occ = plt.subplots(figsize=(6, 4))
    fig_occ.patch.set_facecolor("black")
    ax_occ.set_facecolor("black")
    ax_occ.plot(times, var_counts, linestyle="-", color="#00c8ff")
    ax_occ.set_xlabel("Temps", color="white")
    ax_occ.set_ylabel("Bouteilles", color="white")
    ax_occ.set_title("Occupation du convoyeur variable dans le temps", color="white")
    ax_occ.tick_params(colors="white")
    for spine in ax_occ.spines.values():
        spine.set_color("white")
    ax_occ.grid(True, color="#444444", alpha=0.6)
    st.pyplot(fig_occ)
else:
    st.info("Pas assez de données pour l'occupation du convoyeur variable.")

if show_animation:
    if times and positions:
        cont_positions = position_log.get("cont_positions", [])
        pre_positions = position_log.get("pre_positions", [])
        inspect_counts = position_log.get("inspect_count", [])
        step_log = result.get("step_position_log", {})

        show_step = bool(step_log.get("t"))
        cont_out_length = length_third
        box_size = 0.6
        buffer_x = cont_out_length + horizontal_spacing * 0.4
        inspector_x = cont_out_length + horizontal_spacing * 1.1

        if show_step:
            fig_anim, (ax_step, ax_pre, ax_var, ax_cont) = plt.subplots(
                4, 1, figsize=(10, 11.5), sharex=False, constrained_layout=True
            )
        else:
            fig_anim, (ax_pre, ax_var, ax_cont) = plt.subplots(
                3, 1, figsize=(10, 8.5), sharex=False, constrained_layout=True
            )
            ax_step = None

        if show_step:
            slot_count = steps
            slot_size = 1.0
            total_length = slot_count * slot_size
            ax_step.set_xlim(-0.5, total_length + 0.5)
            ax_step.set_ylim(-0.75, 0.75)
            ax_step.set_yticks([])
            ax_step.set_xlabel("Grenailleuse step conveyor")

            for i in range(slot_count):
                rect = plt.Rectangle(
                    (i * slot_size, -0.3),
                    slot_size,
                    0.6,
                    fill=False,
                    edgecolor="black",
                    linewidth=1.5,
                )
                ax_step.add_patch(rect)
            ax_step.vlines(0, -0.35, 0.35, color="tab:green", linewidth=2)
            ax_step.vlines(total_length, -0.35, 0.35, color="tab:red", linewidth=2)
            ax_step.text(0, 0.4, "Entry", ha="left", va="bottom", fontsize=9)
            ax_step.text(total_length, 0.4, "Exit", ha="right", va="bottom", fontsize=9)

        ax_pre.set_xlim(-vertical_spacing, length_first + vertical_spacing)
        ax_pre.set_ylim(-1, 1.5)
        ax_pre.set_yticks([])
        ax_pre.set_xlabel("Pre-variable conveyor position")
        ax_pre.hlines(0, 0, length_first, color="black", linewidth=2)
        ax_pre.vlines(0, -0.2, 0.2, color="tab:green", linewidth=2)
        ax_pre.vlines(length_first, -0.2, 0.2, color="tab:red", linewidth=2)
        ax_pre.text(0, 0.35, "Grenailleuse out", ha="left", va="bottom", fontsize=9)
        ax_pre.text(length_first, 0.35, "Variable in", ha="right", va="bottom", fontsize=9)

        ax_var.set_xlim(-horizontal_spacing, length_second + horizontal_spacing)
        ax_var.set_ylim(-1, 1.5)
        ax_var.set_yticks([])
        ax_var.set_xlabel("Variable conveyor position")
        ax_var.set_title("Variable + Continuous Conveyor Bottle Movement")

        ax_var.hlines(0, 0, length_second, color="black", linewidth=2)
        ax_var.vlines(0, -0.2, 0.2, color="tab:green", linewidth=2)
        ax_var.vlines(length_second, -0.2, 0.2, color="tab:red", linewidth=2)
        ax_var.text(0, 0.35, "Step G exit", ha="left", va="bottom", fontsize=9)
        ax_var.text(length_second, 0.35, "Variable end", ha="right", va="bottom", fontsize=9)

        ax_cont.set_xlim(-horizontal_spacing, cont_out_length + horizontal_spacing * 2.0)
        ax_cont.set_ylim(-1, 1.5)
        ax_cont.set_yticks([])
        ax_cont.set_xlabel("Continuous conveyor position")

        ax_cont.hlines(0, 0, cont_out_length, color="black", linewidth=2)
        ax_cont.hlines(0, cont_out_length, buffer_x, color="black", linewidth=1.0, linestyle="--")
        ax_cont.vlines(0, -0.2, 0.2, color="tab:green", linewidth=2)
        ax_cont.vlines(cont_out_length, -0.2, 0.2, color="tab:red", linewidth=2)
        ax_cont.text(0, 0.35, "Continuous start", ha="left", va="bottom", fontsize=9)
        ax_cont.text(cont_out_length, 0.35, "Det2 / Inspector input", ha="right", va="bottom", fontsize=9)

        scat_var = ax_var.scatter([], [], s=60, color="tab:blue")
        scat_cont = ax_cont.scatter([], [], s=60, color="tab:orange")
        scat_pre = ax_pre.scatter([], [], s=60, color="tab:purple")
        scat_step = ax_step.scatter([], [], s=80, color="tab:blue") if show_step else None
        buffer_box = plt.Rectangle(
            (buffer_x - box_size / 2, -box_size / 2),
            box_size,
            box_size,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
        )
        inspector_box = plt.Rectangle(
            (inspector_x - box_size / 2, -box_size / 2),
            box_size,
            box_size,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
        )
        ax_cont.add_patch(buffer_box)
        ax_cont.add_patch(inspector_box)
        ax_cont.text(buffer_x, 0.55, "Inspect buffer", ha="center", va="bottom", fontsize=9)
        ax_cont.text(inspector_x, 0.55, "Inspector", ha="center", va="bottom", fontsize=9)
        scat_buffer = ax_cont.scatter([], [], s=90, color="tab:green")
        scat_inspector = ax_cont.scatter([], [], s=90, color="tab:red")
        scat_handoff = ax_cont.scatter([], [], s=60, color="tab:orange")

        def init_anim():
            scat_var.set_offsets(np.empty((0, 2)))
            scat_cont.set_offsets(np.empty((0, 2)))
            scat_pre.set_offsets(np.empty((0, 2)))
            if show_step:
                scat_step.set_offsets(np.empty((0, 2)))
            scat_buffer.set_offsets(np.empty((0, 2)))
            scat_inspector.set_offsets(np.empty((0, 2)))
            scat_handoff.set_offsets(np.empty((0, 2)))
            return (scat_step, scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff) if show_step else (scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff)

        max_frames = 150
        step = max(1, len(times) // max_frames)
        frame_indices = list(range(0, len(times), step))
        if step > 1:
            st.caption(f"Animation échantillonnée (1 image sur {step}).")

        def update_anim(frame_idx):
            frame_positions = positions[frame_idx]
            offsets = (
                np.column_stack((frame_positions, np.zeros(len(frame_positions))))
                if frame_positions
                else np.empty((0, 2))
            )
            scat_var.set_offsets(offsets)
            frame_cont = cont_positions[frame_idx] if frame_idx < len(cont_positions) else []
            frame_cont = [min(p, cont_out_length) for p in frame_cont]
            cont_offsets = (
                np.column_stack((frame_cont, np.zeros(len(frame_cont))))
                if frame_cont
                else np.empty((0, 2))
            )
            scat_cont.set_offsets(cont_offsets)
            frame_pre = pre_positions[frame_idx] if frame_idx < len(pre_positions) else []
            pre_offsets = (
                np.column_stack((frame_pre, np.zeros(len(frame_pre))))
                if frame_pre
                else np.empty((0, 2))
            )
            scat_pre.set_offsets(pre_offsets)
            if show_step and step_log.get("slots"):
                step_idx = frame_idx if frame_idx < len(step_log["slots"]) else len(step_log["slots"]) - 1
                slots = step_log["slots"][step_idx]
                occupied = [i for i, v in enumerate(slots) if v is not None]
                step_offsets = (
                    np.column_stack((np.array(occupied) * slot_size + slot_size * 0.5, np.zeros(len(occupied))))
                    if occupied
                    else np.empty((0, 2))
                )
                scat_step.set_offsets(step_offsets)
            has_buffer = frame_idx < len(inspect_counts) and inspect_counts[frame_idx] > 0
            if has_buffer:
                scat_buffer.set_offsets(np.array([[buffer_x, 0.0]]))
            else:
                scat_buffer.set_offsets(np.empty((0, 2)))
            inspector_busy = monitor.get("inspector_busy", [])
            has_inspector = frame_idx < len(inspector_busy) and inspector_busy[frame_idx] > 0
            if has_inspector:
                scat_inspector.set_offsets(np.array([[inspector_x, 0.0]]))
            else:
                scat_inspector.set_offsets(np.empty((0, 2)))
            needs_handoff = has_buffer and (not frame_cont or max(frame_cont) < cont_out_length - 1e-6)
            if needs_handoff:
                scat_handoff.set_offsets(np.array([[cont_out_length, 0.0]]))
            else:
                scat_handoff.set_offsets(np.empty((0, 2)))
            return (scat_step, scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff) if show_step else (scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff)

        if show_static_preview and frame_indices:
            preview_idx = frame_indices[-1]
            update_anim(preview_idx)
            st.pyplot(fig_anim)

        anim = animation.FuncAnimation(
            fig_anim,
            update_anim,
            frames=frame_indices,
            init_func=init_anim,
            interval=animation_interval_ms,
            blit=False,
        )
        html = anim.to_jshtml()
        if show_step:
            height = 1250
        else:
            height = 900
        if animation_mode == "Statique":
            st.pyplot(fig_anim)
        elif animation_mode == "Interactif":
            components.html(html, height=height, width=1000, scrolling=True)
        else:
            if len(html) > 5_000_000:
                st.warning("Animation trop lourde pour l'affichage interactif. Affichage statique.")
                st.pyplot(fig_anim)
            else:
                components.html(html, height=height, width=1000, scrolling=True)
    else:
        st.info("Animation indisponible : aucune position enregistrée.")

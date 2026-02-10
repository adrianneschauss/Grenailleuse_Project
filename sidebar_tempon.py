import streamlit as st


def to_float(value):
    if isinstance(value, tuple):
        return float("".join(str(part) for part in value))
    return float(value)


def build_sidebar(Parameter):
    st.sidebar.header("Arrivée")
    mean_interval = st.sidebar.number_input(
        "Intervalle moyen (s)",
        min_value=0.1,
        value=to_float(Parameter.mean_interval),
        step=1.0,
        key="arrivee_mean_interval",
    )
    down_time = st.sidebar.slider(
        "Probabilité d'arrêt",
        min_value=0.0,
        max_value=1.0,
        value=to_float(Parameter.down_time),
        key="arrivee_down_time",
    )
    min_inter = st.sidebar.number_input(
        "Interruption min (s)",
        min_value=0.0,
        value=to_float(Parameter.min_iter),
        step=1.0,
        key="arrivee_min_inter",
    )
    max_inter = st.sidebar.number_input(
        "Interruption max (s)",
        min_value=0.0,
        value=to_float(Parameter.max_iter),
        step=1.0,
        key="arrivee_max_inter",
    )

    st.sidebar.header("Grenailleuse")
    step_time = st.sidebar.number_input(
        "Temps de pas (s)",
        min_value=0.1,
        value=to_float(Parameter.step_time),
        step=1.0,
        key="gren_step_time",
    )
    steps = st.sidebar.number_input(
        "Nombre d'étapes",
        min_value=1,
        value=int(to_float(Parameter.steps)),
        step=1,
        key="gren_steps",
    )
    gr_conv = st.sidebar.number_input(
        "Déchargement vers convoyeur (s)",
        min_value=0.0,
        value=to_float(Parameter.gr_conv),
        step=1.0,
        key="gren_gr_conv",
    )
    variable_speed = st.sidebar.checkbox(
        "Variation de Vitesse",
        value=bool(getattr(Parameter, "variable_speed", False)),
        key="gren_variable_speed",
    )
    #______________________________________
    st.sidebar.header("Tampon")
    vertical_spacing = st.sidebar.number_input(
        "Espacement vertical (cm)",
        min_value=0.1,
        value=to_float(Parameter.vertical_spacing),
        step=0.1,
        key="conv_vertical_spacing",
    )
    length_first = st.sidebar.number_input(
        "Longueur Tampon (Convoyeur 0) (cm)",
        min_value=0.1,
        value=to_float(Parameter.length_first),
        step=0.1,
        key="var_length_first",
    )
    speed_tempon = st.sidebar.number_input(
        "Vitesse tampon (cm/s)",
        min_value=0.1,
        value=to_float(getattr(Parameter, "speed_tempon", 0.1)),
        step=0.1,
        key="conv_speed_tempon",
    )
    
#______________________________________
    st.sidebar.header("Convoyeur horizontal variable")
    horizontal_spacing = st.sidebar.number_input(
        "Espacement horizontal (cm)",
        min_value=0.1,
        value=to_float(Parameter.horizontal_spacing),
        step=0.1,
        key="conv_horizontal_spacing",
    )
    length_second = st.sidebar.number_input(
        "Longueur Convoyeur (convoyeur 1) (cm)",
        min_value=0.1,
        value=to_float(Parameter.length_second),
        step=0.1,
        key="var_length_second",
    )
    first_speed = st.sidebar.number_input(
        "Vitesse convoyeur (cm/s) variable",
        min_value=0.1,
        value=to_float(Parameter.first_speed),
        step=0.1,
        key="conv_first_speed",
    )
    
    mode_switch_delay = st.sidebar.number_input(
        "Délai changement mode (s)",
        min_value=0.0,
        value=to_float(Parameter.mode_switch_delay),
        step=0.1,
        key="conv_mode_switch_delay",
    )
    det_hold_time = st.sidebar.number_input(
        "Temps déclenchement détecteurs (s)",
        min_value=0.0,
        value=to_float(Parameter.det_hold_time),
        step=0.1,
        key="var_det_hold_time",
    )
    step_time_2 = st.sidebar.number_input(
        "Temps de pas variable (s)",
        min_value=0.1,
        value=to_float(Parameter.step_time_2),
        step=0.1,
        key="var_step_time_2",
    )
#______________________________________
    st.sidebar.header("Convoyeur horizontal continu")
    length_third = st.sidebar.number_input(
        "Longueur convoyeur Continu (2) (cm)",
        min_value=0.1,
        value=to_float(Parameter.length_third),
        step=0.1,
        key="var_length_third",
    )
    second_speed = st.sidebar.number_input(
        "Vitesse convoyeur (cm/s) continu",
        min_value=0.1,
        value=to_float(Parameter.second_speed),
        step=0.1,
        key="conv_second_speed",
    )
    
    #______________________________________
    st.sidebar.header("Inspecteur")
    inspect_min = st.sidebar.number_input(
        "Inspection min (s)",
        min_value=0.1,
        value=to_float(Parameter.inspect_min),
        step=1.0,
        key="insp_min",
    )
    inspect_max = st.sidebar.number_input(
        "Inspection max (s)",
        min_value=0.1,
        value=to_float(Parameter.inspect_max),
        step=1.0,
        key="insp_max",
    )
    s = st.sidebar.slider(
        "Probabilité pause longue",
        min_value=0.0,
        max_value=1.0,
        value=float(Parameter.s),
        step=0.01,
        key="insp_s",
    )
    min_long = st.sidebar.slider(
        "Pause longue min (s)",
        min_value=0.0,
        max_value=200.0,
        value=float(Parameter.min),
        step=1.0,
        key="insp_min_long",
    )
    max_long = st.sidebar.slider(
        "Pause longue max (s)",
        min_value=0.0,
        max_value=200.0,
        value=float(Parameter.max),
        step=1.0,
        key="insp_max_long",
    )
    t_dis = st.sidebar.number_input(
        "Délai de chargement (s)",
        min_value=0.0,
        value=to_float(Parameter.t_dis2),
        step=1.0,
        key="insp_t_dis",
    )
    t_dis2 = st.sidebar.number_input(
        "Délai de déchargement (s)",
        min_value=0.0,
        value=to_float(Parameter.t_dis),
        step=1.0,
        key="insp_t_dis2",
    )

    st.sidebar.header("Lancement")
    env_time = st.sidebar.number_input(
        "Temps de simulation (s)",
        min_value=1.0,
        value=to_float(Parameter.env_time),
        step=10.0,
        key="launch_env_time",
    )
    cont_out_capacity = st.sidebar.number_input(
        "Capacité du tampon avant inspection",
        min_value=1,
        value=1,
        step=1,
        key="launch_cont_out_capacity",
    )
    sample_time = st.sidebar.number_input(
        "Temps d'échantillonnage (s)",
        min_value=0.1,
        value=1.0,
        step=0.1,
        key="launch_sample_time",
    )
    show_animation = st.sidebar.checkbox(
        "Afficher animation",
        value=True,
        key="launch_show_animation",
    )
    animation_interval_ms = st.sidebar.number_input(
        "Animation interval (ms)",
        min_value=10,
        value=50,
        step=10,
        key="launch_animation_interval_ms",
    )
    animation_mode = st.sidebar.selectbox(
        "Mode animation",
        ["Auto", "Interactif", "Statique"],
        index=0,
        key="launch_animation_mode",
    )
    show_static_preview = st.sidebar.checkbox(
        "Aperçu statique",
        value=True,
        key="launch_show_static_preview",
    )

    return {
        "mean_interval": mean_interval,
        "down_time": down_time,
        "min_inter": min_inter,
        "max_inter": max_inter,
        "step_time": step_time,
        "steps": steps,
        "gr_conv": gr_conv,
        "variable_speed": variable_speed,
        "horizontal_spacing": horizontal_spacing,
        "vertical_spacing": vertical_spacing,
        "first_speed": first_speed,
        "second_speed": second_speed,
        "speed_tempon": speed_tempon,
        "mode_switch_delay": mode_switch_delay,
        "det_hold_time": det_hold_time,
        "step_time_2": step_time_2,
        "length_first": length_first,
        "length_second": length_second,
        "length_third": length_third,
        "inspect_min": inspect_min,
        "inspect_max": inspect_max,
        "s": s,
        "min_long": min_long,
        "max_long": max_long,
        "t_dis": t_dis,
        "t_dis2": t_dis2,
        "env_time": env_time,
        "cont_out_capacity": cont_out_capacity,
        "sample_time": sample_time,
        "show_animation": show_animation,
        "animation_interval_ms": animation_interval_ms,
        "animation_mode": animation_mode,
        "show_static_preview": show_static_preview,
    }

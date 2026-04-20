"""Image-mapped animation driven by variable_tempon simulation arrays.

This script uses the exact state arrays from `demo_variable_conveyor_tempon` and
maps them onto `Animation_Image.png`:
- grenailleuse step slots
- pre-variable transfer (downward)
- variable conveyor
- continuous conveyor
- inspector buffer and inspector occupancy
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import site
import sys

_RUNTIME_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
_DEFAULT_MPLCONFIGDIR = _RUNTIME_DIR / ".mplconfig"
os.environ.setdefault("MPLCONFIGDIR", str(_DEFAULT_MPLCONFIGDIR))
_DEFAULT_MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Circle, Ellipse, Rectangle

import Parameter_horizontal
from demo_variable_conveyor_tempon import demo_composite_flow


BACKGROUND_PATH = _RUNTIME_DIR / "Animation_Image.png"

# Rendering
BOTTLE_W = 70
BOTTLE_H = 22
FRAME_INTERVAL_MS = 60

# Simulation sampling for animation logs.
SIM_ENV_TIME_S = 200
SIM_SAMPLE_TIME_S = 0.25
REALTIME_SCALE = 1.0  # 3.0 => animation runs 3x faster than simulation time
STOP_PCT_WINDOW_S = 60.0

# Mapping anchors.
# Grenailleuse exact span from user (image pixel coordinates):
# beginning (right) -> end (left)
GRENAILLEUSE_RIGHT_X = 1628.0
GRENAILLEUSE_LEFT_X = 167.0
GRENAILLEUSE_Y = 260.0

# Tempon/drop exact vertical span from user (image pixel coordinates):
# from grenailleuse end downward
TEMPON_X = 167.0
TEMPON_Y_START = 260.0
TEMPON_Y_END = 695.0
TEMPON_VISUAL_END_Y = 616.0

# Downstream mapping (exact bounds from user).
VAR_CONVEYOR_START_X = TEMPON_X
VAR_CONVEYOR_END_X = 1160.0 
CONT_CONVEYOR_START_X = 1160.0
CONT_CONVEYOR_END_X = 1460.0

# Inspector midpoint provided by user (image pixel coordinates).
INSPECTOR_MID_X = 1649
INSPECTOR_MID_Y = 697
SINK_MID_X = 1518
SINK_MID_Y = 697
POST_INSPECT_X = 1777
POST_INSPECT_Y = 697


@dataclass
class SimulationOverrides:
    min_inter: float
    max_inter: float
    down_time: float
    inspect_min: float
    inspect_max: float
    long_pause_min: float
    long_pause_max: float
    long_pause_prob: float
    sim_time: float
    frame_interval_ms: float
    realtime_scale: float


def _lin_map(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    if abs(in_max - in_min) < 1e-9:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return out_min + t * (out_max - out_min)


def _make_pool(ax, n: int, face: str, edge: str) -> list[Rectangle]:
    pool: list[Rectangle] = []
    for _ in range(n):
        patch = Rectangle(
            (0.0, 0.0),
            BOTTLE_W,
            BOTTLE_H,
            facecolor=face,
            edgecolor=edge,
            linewidth=1.2,
            alpha=0.9,
            visible=False,
        )
        ax.add_patch(patch)
        pool.append(patch)
    return pool


def _update_pool(pool: list[Rectangle], centers: list[tuple[float, float]]) -> None:
    for i, patch in enumerate(pool):
        if i < len(centers):
            x, y = centers[i]
            patch.set_xy((x - BOTTLE_W / 2.0, y - BOTTLE_H / 2.0))
            patch.set_visible(True)
        else:
            patch.set_visible(False)


def _safe_list_item(seq, idx: int):
    if not seq:
        return None
    if idx < len(seq):
        return seq[idx]
    return seq[-1]


def _value_at_time(t_query: float, t_series: list[float], values: list):
    if not t_series or not values:
        return 0
    idx = bisect_right(t_series, t_query) - 1
    if idx < 0:
        return values[0]
    if idx >= len(values):
        return values[-1]
    return values[idx]


def _intervals_from_history(
    bottle_history: dict,
    start_key: str,
    end_key: str,
) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    for hist in bottle_history.values():
        start_t = hist.get(start_key)
        end_t = hist.get(end_key)
        if start_t is None or end_t is None:
            continue
        start_f = float(start_t)
        end_f = float(end_t)
        if end_f > start_f:
            intervals.append((start_f, end_f))
    return intervals


def _in_any_interval(t_query: float, intervals: list[tuple[float, float]]) -> bool:
    for start_t, end_t in intervals:
        if start_t <= t_query < end_t:
            return True
    return False


def _ids_in_interval(
    t_query: float,
    bottle_history: dict,
    start_key: str,
    end_key: str,
) -> set[int]:
    ids: set[int] = set()
    for bottle_id, hist in bottle_history.items():
        start_t = hist.get(start_key)
        end_t = hist.get(end_key)
        if start_t is None or end_t is None:
            continue
        start_f = float(start_t)
        end_f = float(end_t)
        if start_f <= t_query < end_f:
            ids.add(int(bottle_id))
    return ids


def _find_ffmpeg_exe() -> str | None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        return ffmpeg_bin

    if os.name == "nt":
        windows_candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
            Path(os.environ.get("ProgramData", "")) / "chocolatey" / "bin" / "ffmpeg.exe",
            Path(os.environ.get("ProgramFiles", "")) / "ffmpeg" / "bin" / "ffmpeg.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "ffmpeg" / "bin" / "ffmpeg.exe",
        ]
        for candidate in windows_candidates:
            if candidate.exists():
                return str(candidate)
        winget_packages = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        if winget_packages.exists():
            for candidate in winget_packages.glob("**/ffmpeg.exe"):
                if candidate.exists():
                    return str(candidate)
    return None


def _build_render_times(start_t: float, end_t: float, step_s: float) -> list[float]:
    if end_t <= start_t:
        return [start_t]
    if step_s <= 1e-9:
        return [start_t, end_t]
    render_times: list[float] = []
    t_now = start_t
    while t_now < end_t - 1e-9:
        render_times.append(t_now)
        t_now += step_s
    render_times.append(end_t)
    return render_times


def _interpolate_item_series(
    t_query: float,
    t_series: list[float],
    item_series: list[list[dict]],
) -> list[dict]:
    if not t_series or not item_series:
        return []
    idx = bisect_right(t_series, t_query) - 1
    if idx < 0:
        idx = 0
    if idx >= len(t_series) - 1 or idx >= len(item_series) - 1:
        return item_series[min(idx, len(item_series) - 1)] or []
    t0 = float(t_series[idx])
    t1 = float(t_series[idx + 1])
    items0 = item_series[idx] or []
    items1 = item_series[idx + 1] or []
    if t1 <= t0 + 1e-9 or t_query <= t0 + 1e-9:
        return items0
    if t_query >= t1 - 1e-9:
        return items1
    alpha = (t_query - t0) / (t1 - t0)
    pos0 = {
        int(item["id"]): float(item.get("pos", 0.0))
        for item in items0
        if item.get("id") is not None
    }
    pos1 = {
        int(item["id"]): float(item.get("pos", 0.0))
        for item in items1
        if item.get("id") is not None
    }
    ordered_ids: list[int] = []
    seen: set[int] = set()
    for item in items0 + items1:
        bottle_id = item.get("id")
        if bottle_id is None:
            continue
        bottle_id = int(bottle_id)
        if bottle_id in seen:
            continue
        seen.add(bottle_id)
        ordered_ids.append(bottle_id)
    interp_items: list[dict] = []
    for bottle_id in ordered_ids:
        if bottle_id in pos0 and bottle_id in pos1:
            pos = pos0[bottle_id] + alpha * (pos1[bottle_id] - pos0[bottle_id])
        elif bottle_id in pos0:
            pos = pos0[bottle_id]
        else:
            # Do not introduce a bottle before it exists in the logged state.
            continue
        interp_items.append({"id": bottle_id, "pos": pos})
    return interp_items


def _prompt_pair(prompt: str, default_pair: tuple[float, float]) -> tuple[float, float]:
    default_text = f"{default_pair[0]:g},{default_pair[1]:g}"
    while True:
        raw = input(f"{prompt} [{default_text}] ").strip()
        if not raw:
            return default_pair
        parts = [part.strip() for part in raw.split(",")]
        if len(parts) != 2:
            print("Veuillez entrer deux nombres separes par une virgule, par exemple : 10,30")
            continue
        try:
            first = float(parts[0])
            second = float(parts[1])
        except ValueError:
            print("Veuillez entrer des nombres valides, par exemple : 10,30")
            continue
        if first < 0 or second < 0:
            print("Veuillez entrer des valeurs positives ou nulles.")
            continue
        if second < first:
            print("La deuxieme valeur doit etre superieure ou egale a la premiere.")
            continue
        return first, second


def _prompt_float(
    prompt: str,
    default_value: float,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    default_text = f"{default_value:g}"
    while True:
        raw = input(f"{prompt} [{default_text}] ").strip()
        if not raw:
            return default_value
        try:
            value = float(raw)
        except ValueError:
            print("Veuillez entrer un nombre valide.")
            continue
        if min_value is not None and value < min_value:
            print(f"Veuillez entrer une valeur superieure ou egale a {min_value:g}.")
            continue
        if max_value is not None and value > max_value:
            print(f"Veuillez entrer une valeur inferieure ou egale a {max_value:g}.")
            continue
        return value


def _prompt_quality(default_quality: str = "high") -> str:
    labels = {
        "ultra_low": "ultra basse",
        "low": "basse",
        "medium": "moyenne",
        "high": "elevee",
    }
    aliases = {
        "ultra low": "ultra_low",
        "ultra basse": "ultra_low",
        "ultrabasse": "ultra_low",
        "low": "low",
        "basse": "low",
        "medium": "medium",
        "moyenne": "medium",
        "high": "high",
        "haute": "high",
        "elevee": "high",
    }
    default_label = labels[default_quality]
    while True:
        raw = input(
            (
                "Quel niveau de qualite souhaitez-vous pour l'animation ? "
                "Choisissez ultra basse, basse, moyenne ou elevee "
                "(la qualite elevee correspond au reglage actuel) : "
                f"[{default_label}] "
            )
        ).strip().lower()
        if not raw:
            return default_quality
        if raw in aliases:
            return aliases[raw]
        print("Veuillez choisir ultra basse, basse, moyenne ou elevee.")


def _quality_to_frame_interval_ms(quality: str) -> float:
    mapping = {
        "ultra_low": 250.0,
        "low": 120.0,
        "medium": 90.0,
        "high": 60.0,
    }
    return mapping[quality]


def _prompt_realtime_scale(default_scale: float = REALTIME_SCALE) -> float:
    while True:
        raw = input(
            (
                "A quelle vitesse souhaitez-vous lire la simulation ? "
                "Donnez une valeur comme 1x, 2x ou 3x : "
                f"[{default_scale:g}x] "
            )
        ).strip().lower()
        if not raw:
            return float(default_scale)
        if raw.endswith("x"):
            raw = raw[:-1].strip()
        try:
            value = float(raw)
        except ValueError:
            print("Veuillez entrer une valeur comme 1x, 2x ou 3x.")
            continue
        if value <= 0:
            print("Veuillez entrer une valeur strictement positive.")
            continue
        return value


def collect_simulation_overrides() -> SimulationOverrides:
    print("Appuyez sur Entree pour conserver la valeur par defaut affichee entre crochets.")
    min_inter, max_inter = _prompt_pair(
        (
            "Quel temps supplementaire souhaitez-vous pour l'entree d'une bouteille "
            "dans la grenailleuse, sachant que le temps normal entre deux entrees "
            "est de 12 secondes ? Ce temps sera ajoute au temps normal. "
            "Donnez une paire comme 10,30 :"
        ),
        (float(Parameter_horizontal.min_iter), float(Parameter_horizontal.max_iter)),
    )
    down_time = _prompt_float(
        "Quelle probabilite souhaitez-vous pour qu'une bouteille entre dans la grenailleuse avec le temps normal plus le temps supplementaire ajoute ?",
        float(Parameter_horizontal.down_time),
        min_value=0.0,
        max_value=1.0,
    )
    inspect_min, inspect_max = _prompt_pair(
        (
            "Quels temps minimum et maximum souhaitez-vous pour l'inspection normale ? "
            "Donnez une paire comme 8,16 :"
        ),
        (float(Parameter_horizontal.inspect_min), float(Parameter_horizontal.inspect_max)),
    )
    long_pause_min, long_pause_max = _prompt_pair(
        (
            "Quels temps minimum et maximum souhaitez-vous pour la longue pause "
            "de l'inspection ? Cette plage remplacera le temps normal d'inspection "
            "pour les cas longs. Donnez une paire comme 30,40 :"
        ),
        (float(Parameter_horizontal.min), float(Parameter_horizontal.max)),
    )
    long_pause_prob = _prompt_float(
        "Quelle probabilite souhaitez-vous pour les longues pauses qui remplacent le temps normal ? Donnez un nombre entre 0 et 1, par exemple 0.05 :",
        float(Parameter_horizontal.s),
        min_value=0.0,
        max_value=1.0,
    )
    sim_time = _prompt_float(
        "Combien de secondes souhaitez-vous simuler ? Par exemple 3600 s correspondent a 60 minutes :",
        float(SIM_ENV_TIME_S),
        min_value=0.001,
    )
    quality = _prompt_quality("high")
    realtime_scale = _prompt_realtime_scale(REALTIME_SCALE)
    inspect_mean = 0.5 * (inspect_min + inspect_max)
    print(f"Temps moyen d'inspection normale retenu : {inspect_mean:.1f}s")
    return SimulationOverrides(
        min_inter=min_inter,
        max_inter=max_inter,
        down_time=down_time,
        inspect_min=inspect_min,
        inspect_max=inspect_max,
        long_pause_min=long_pause_min,
        long_pause_max=long_pause_max,
        long_pause_prob=long_pause_prob,
        sim_time=sim_time,
        frame_interval_ms=_quality_to_frame_interval_ms(quality),
        realtime_scale=realtime_scale,
    )


def run_animation(
    save_path: Path | None = None,
    fps: int | None = None,
    overrides: SimulationOverrides | None = None,
) -> None:
    if not BACKGROUND_PATH.exists():
        raise FileNotFoundError(f"Background image not found: {BACKGROUND_PATH.resolve()}")

    frame_interval_ms = float(
        overrides.frame_interval_ms if overrides is not None else FRAME_INTERVAL_MS
    )
    realtime_scale = float(
        overrides.realtime_scale if overrides is not None else REALTIME_SCALE
    )
    active_inspect_min = (
        float(overrides.inspect_min) if overrides is not None else float(Parameter_horizontal.inspect_min)
    )
    active_inspect_max = (
        float(overrides.inspect_max) if overrides is not None else float(Parameter_horizontal.inspect_max)
    )
    active_long_pause_min = (
        float(overrides.long_pause_min) if overrides is not None else float(Parameter_horizontal.min)
    )
    active_long_pause_max = (
        float(overrides.long_pause_max) if overrides is not None else float(Parameter_horizontal.max)
    )
    active_long_pause_prob = (
        float(overrides.long_pause_prob) if overrides is not None else float(Parameter_horizontal.s)
    )
    demo_kwargs = dict(
        variable_speed=True,
        animate=False,
        plot=False,
        env_time=SIM_ENV_TIME_S,
        sample_time=SIM_SAMPLE_TIME_S,
    )
    if overrides is not None:
        demo_kwargs.update(
            down_time=overrides.down_time,
            inspect_min=overrides.inspect_min,
            inspect_max=overrides.inspect_max,
            min_inter=overrides.min_inter,
            max_inter=overrides.max_inter,
            min_long=overrides.long_pause_min,
            max_long=overrides.long_pause_max,
            s=overrides.long_pause_prob,
            env_time=overrides.sim_time,
        )

    result = demo_composite_flow(**demo_kwargs)

    position_log = result["position_log"]
    step_log = result["step_position_log"]
    monitor = result["monitor"]
    bottle_history = result.get("bottle_history", {})
    inspected_times = sorted(result.get("inspected_times", []))
    blocked_time_total = float(result.get("grenailleuse_blocked_time", 0.0))
    blocked_intervals = list(result.get("grenailleuse_blocked_intervals", []))
    total_time = float(result.get("total_time", 0.0))

    times = position_log.get("t", [])
    step_times = step_log.get("t", [])
    pre_positions_series = position_log.get("pre_positions", [])
    pre_items_series = position_log.get("pre_items", [])
    pre_var_buffer_series = position_log.get("pre_var_buffer_items", [])
    var_items_series = position_log.get("position_items", [])
    var_positions_series = position_log.get("positions", [])
    cont_positions_series = position_log.get("cont_positions", [])
    cont_items_series = position_log.get("cont_items", [])
    inspect_counts = position_log.get("inspect_count", [])
    inspect_items_series = position_log.get("inspect_items", [])
    inspector_item_series = position_log.get("inspector_item", [])
    post_inspect_items_series = position_log.get("post_inspect_items", [])
    det1_series = position_log.get("det1", [])
    det2_series = position_log.get("det2", [])
    det3_series = position_log.get("det3", [])
    det4_series = position_log.get("det4", [])
    step_output_count = monitor.get("step_output_count", [])
    step_time_series = monitor.get("grenailleuse_step_time", [])
    monitor_t = monitor.get("t", [])
    sink_wait_intervals = _intervals_from_history(
        bottle_history,
        "sink_entry",
        "inspector_start",
    )
    post_inspect_intervals = _intervals_from_history(
        bottle_history,
        "post_inspect_entry",
        "post_inspect_exit",
    )

    if not times:
        raise RuntimeError("No position logs available from simulation run.")

    render_step_s = max(1e-3, frame_interval_ms * realtime_scale / 1000.0)
    render_times = _build_render_times(float(times[0]), float(times[-1]), render_step_s)

    bg = plt.imread(BACKGROUND_PATH)
    img_h, img_w = bg.shape[0], bg.shape[1]

    # Image-space anchors.
    y_gren = GRENAILLEUSE_Y
    y_conv = TEMPON_Y_END
    y_tempon_end = TEMPON_VISUAL_END_Y
    x_right = GRENAILLEUSE_RIGHT_X
    x_left = GRENAILLEUSE_LEFT_X
    # Conveyor x-ranges.
    l_var = float(Parameter_horizontal.length_second)
    l_cont = float(Parameter_horizontal.length_third)
    var_entry_hold_s = float(getattr(Parameter_horizontal, "t_prevar_exit_to_var_entry", 0.07))
    x_var_start = VAR_CONVEYOR_START_X
    x_var_end = VAR_CONVEYOR_END_X
    x_cont_start = CONT_CONVEYOR_START_X
    # Keep one bottle-length free after the conveyor for the sink/waiting position.
    x_cont_end = CONT_CONVEYOR_END_X - BOTTLE_W
    x_sink = CONT_CONVEYOR_END_X

    # Inspector / hold markers: inspector pin from user coordinates.
    x_inspector = float(INSPECTOR_MID_X)
    y_inspector = float(INSPECTOR_MID_Y)
    x_buffer = float(SINK_MID_X)
    y_buffer = float(SINK_MID_Y)

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.imshow(bg, extent=(0, img_w, img_h, 0))
    ax.set_xlim(0, img_w)
    ax.set_ylim(img_h, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    # Optional guide lanes for quick calibration.
    ax.plot([x_right, x_left], [y_gren, y_gren], color="#ffef5a", lw=1.2, alpha=0.55)
    ax.plot([x_left, x_left], [y_gren, y_tempon_end], color="#ffef5a", lw=1.2, alpha=0.55)
    ax.plot([x_var_start, x_var_end], [y_conv, y_conv], color="#ffef5a", lw=1.2, alpha=0.55)
    ax.plot([x_cont_start, x_cont_end], [y_conv, y_conv], color="#ffef5a", lw=1.2, alpha=0.55)
    ax.plot([x_cont_end, x_sink], [y_conv, y_conv], color="#ffef5a", lw=1.0, alpha=0.45, linestyle="--")
    # Marqueurs détecteurs det1..det4 (cercles vides).
    # det4: début variable, det3: fin variable, det2: fin continu, det1: tampon inspection.
    det4_zone_end_x = _lin_map(
        float(Parameter_horizontal.horizontal_spacing),
        0.0,
        l_var,
        x_var_start,
        x_var_end,
    )
    det4_zone_start_x = x_var_start
    det4_zone_center_x = 0.5 * (det4_zone_start_x + det4_zone_end_x)
    det4_zone_width = max(12.0, det4_zone_end_x - det4_zone_start_x- 10)

    sensor_x = [x_buffer, x_cont_end - 20.0, x_var_end - 10]
    sensor_y = [y_buffer, y_conv, y_conv]
    sensor_patches = []
    for sx, sy in zip(sensor_x, sensor_y):
        c = Circle(
            (sx, sy),
            radius=8.0,
            facecolor="none",
            edgecolor="black",
            linewidth=1.8,
            zorder=8,
        )
        ax.add_patch(c)
        sensor_patches.append(c)
    det4_patch = Ellipse(
        (det4_zone_center_x, y_conv),
        width=det4_zone_width,
        height=16.0,
        facecolor="none",
        edgecolor="black",
        linewidth=1.8,
        zorder=8,
    )
    ax.add_patch(det4_patch)
    sensor_patches.append(det4_patch)
    sensor_labels = ["Capteur 1", "Capteur 2", "Capteur 3", "Capteur 4"]
    sensor_label_x = [x_buffer, x_cont_end - 20.0, x_var_end - 10, det4_zone_end_x]
    sensor_label_y = [y_buffer, y_conv, y_conv, y_conv]
    for sx, sy, lab in zip(sensor_label_x, sensor_label_y, sensor_labels):
        ax.text(sx + 8.0, sy - 10.0, lab, color="black", fontsize=8, ha="left", va="bottom")

    # Patch pools sized by observed max occupancy.
    max_pre = max((len(v) for v in pre_positions_series), default=0)
    max_var = max((len(v) for v in var_positions_series), default=0)
    max_cont = max((len(v) for v in cont_positions_series), default=0)

    pre_pool = _make_pool(ax, max_pre, face="#9b59b6", edge="#4b2a58")
    handoff_pool = _make_pool(ax, 1, face="#7f8c8d", edge="#2c3e50")
    pre_var_buffer_pool = _make_pool(ax, 1, face="#8e44ad", edge="#4a235a")
    var_pool = _make_pool(ax, max_var, face="#2ea8ff", edge="#05395e")
    cont_pool = _make_pool(ax, max_cont, face="#ff9f43", edge="#8a4c10")

    # Grenailleuse slots (8 by model default).
    slot_count = int(Parameter_horizontal.steps)
    base_step_time = float(Parameter_horizontal.step_time)
    min_step_time = base_step_time * float(Parameter_horizontal.speed_ctrl_min_step_mult)
    max_step_time = base_step_time * float(Parameter_horizontal.speed_ctrl_max_step_mult)
    step_pool = _make_pool(ax, slot_count, face="#5dade2", edge="#1f4e79")

    buffer_patch = Rectangle(
        (0.0, 0.0),
        BOTTLE_W,
        BOTTLE_H,
        facecolor="#7bd389",
        edgecolor="#2e7d32",
        linewidth=1.2,
        alpha=0.95,
        visible=False,
    )
    inspector_patch = Rectangle(
        (0.0, 0.0),
        BOTTLE_W,
        BOTTLE_H,
        facecolor="#ef5350",
        edgecolor="#8e0000",
        linewidth=1.2,
        alpha=0.95,
        visible=False,
    )
    post_inspect_patch = Rectangle(
        (0.0, 0.0),
        BOTTLE_W,
        BOTTLE_H,
        facecolor="#1abc9c",
        edgecolor="#0b5345",
        linewidth=1.2,
        alpha=0.95,
        visible=False,
    )
    ax.add_patch(buffer_patch)
    ax.add_patch(inspector_patch)
    ax.add_patch(post_inspect_patch)

    title = ax.text(20, 32, "", color="white", fontsize=11, fontweight="bold")
    step_time_text = ax.text(
        x_right - 40.0,
        y_gren - 85.0,
        "Temps de pas = 0.0s",
        color="black",
        fontsize=10,
        ha="left",
        va="top",
        fontweight="bold",
        bbox={
            "facecolor": "white",
            "edgecolor": "black",
            "boxstyle": "round,pad=0.35",
            "alpha": 0.9,
        },
    )
    stop_pct_text = ax.text(
        x_right - 40.0,
        y_gren - 5.0,
        f"Arrêt % ({int(STOP_PCT_WINDOW_S)}s) = 0.0%",
        color="black",
        fontsize=10,
        ha="left",
        va="top",
        fontweight="bold",
        bbox={
            "facecolor": "white",
            "edgecolor": "black",
            "boxstyle": "round,pad=0.35",
            "alpha": 0.9,
        },
    )
    stop_kpi_text = ax.text(
        x_right - 40.0,
        y_gren + 55.0,
        "Arrêt KPI (simulation) = 0.0%",
        color="black",
        fontsize=10,
        ha="left",
        va="top",
        fontweight="bold",
        bbox={
            "facecolor": "white",
            "edgecolor": "black",
            "boxstyle": "round,pad=0.35",
            "alpha": 0.9,
        },
    )
    sim_stats_text = ax.text(
        img_w - 24.0,
        y_inspector + BOTTLE_H * 10.0,
        "Temps simulation = 0.0s\nBouteilles sorties = 0",
        color="black",
        fontsize=11,
        ha="right",
        va="top",
        fontweight="bold",
        bbox={
            "facecolor": "white",
            "edgecolor": "black",
            "boxstyle": "round,pad=0.35",
            "alpha": 0.9,
        },
    )
    inspector_timer_text = ax.text(
        x_inspector + 170.0,
        y_inspector + BOTTLE_H * 0.6,
        "Temps D'Inspection = 0.0s",
        color="black",
        fontsize=10,
        ha="left",
        va="top",
        fontweight="bold",
    )
    inspect_info_text = ax.text(
        x_inspector + 170.0,
        y_inspector + BOTTLE_H * 2.1,
        (
            f"Plage inspection: {active_inspect_min:.1f}s - "
            f"{active_inspect_max:.1f}s\n"
            f"Inspection longue (p={active_long_pause_prob:.2f}) : "
            f"min: {active_long_pause_min:.1f}s, "
            f"max: {active_long_pause_max:.1f}s"
        ),
        color="black",
        fontsize=9,
        ha="left",
        va="top",
        fontweight="bold",
        bbox={
            "facecolor": "white",
            "edgecolor": "black",
            "boxstyle": "round,pad=0.30",
            "alpha": 0.9,
        },
    )
    inspector_cycle_start_t = None
    last_completed_count = 0

    def update(frame: int):
        nonlocal inspector_cycle_start_t, last_completed_count
        t_now = _safe_list_item(render_times, frame) or 0.0
        pre_items = _interpolate_item_series(t_now, times, pre_items_series)
        pre_var_buffer_items = _value_at_time(t_now, times, pre_var_buffer_series) or []
        var_items = _interpolate_item_series(t_now, times, var_items_series)
        cont_items = _interpolate_item_series(t_now, times, cont_items_series)
        var_positions = [float(item.get("pos", 0.0)) for item in var_items]

        # Pre-variable conveyor: map 0..length_first onto +y at fixed x_left.
        # Reserve the first slot at TEMPON_Y_START for step-output handoff.
        handoff_gap = (y_tempon_end - TEMPON_Y_START) / 4.0
        pre_centers = [
            (
                TEMPON_X,
                _lin_map(
                    p,
                    0.0,
                    float(Parameter_horizontal.length_first),
                    TEMPON_Y_START + handoff_gap,
                    y_tempon_end,
                ),
            )
            for item in pre_items
            if (
                item.get("id") is None
                or t_now < float(
                    bottle_history.get(int(item["id"]), {}).get("pre_var_exit", float("inf"))
                )
            )
            for p in [float(item.get("pos", 0.0))]
        ]
        handoff_count_now = _value_at_time(t_now, monitor_t, step_output_count)
        handoff_centers = [(TEMPON_X, TEMPON_Y_START)] if handoff_count_now > 0 else []
        inferred_pre_var_transfer = False
        if not pre_var_buffer_items:
            for bottle_id, hist in bottle_history.items():
                pre_var_exit_t = hist.get("pre_var_exit")
                variable_entry_t = hist.get("variable_entry")
                if pre_var_exit_t is None or variable_entry_t is None:
                    continue
                if float(pre_var_exit_t) <= t_now < float(variable_entry_t):
                    inferred_pre_var_transfer = True
                    break
        pre_var_buffer_centers = (
            [(TEMPON_X, y_tempon_end + BOTTLE_H * 1.6)]
            if (pre_var_buffer_items or inferred_pre_var_transfer)
            else []
        )

        # Variable conveyor: map 0..length_second onto +x at y_conveyor.
        var_centers = []
        if var_items:
            for item in var_items:
                bottle_id = item.get("id")
                p = item.get("pos", 0.0)
                entry_t = None
                if bottle_id is not None:
                    entry_t = bottle_history.get(int(bottle_id), {}).get("variable_entry")
                if entry_t is not None and t_now < float(entry_t) + var_entry_hold_s:
                    var_centers.append((x_var_start, y_conv))
                else:
                    var_centers.append(
                        (
                            _lin_map(p, 0.0, l_var, x_var_start, x_var_end),
                            y_conv,
                        )
                    )

        # Continuous conveyor: map 0..length_third onto +x continuation.
        cont_centers = [
            (
                _lin_map(
                    min(max(float(item.get("pos", 0.0)), 0.0), l_cont),
                    0.0,
                    l_cont,
                    x_cont_start,
                    x_cont_end,
                ),
                y_conv,
            )
            for item in cont_items
        ]

        _update_pool(pre_pool, pre_centers)
        _update_pool(handoff_pool, handoff_centers)
        _update_pool(pre_var_buffer_pool, pre_var_buffer_centers)
        _update_pool(var_pool, var_centers)
        _update_pool(cont_pool, cont_centers)

        # Grenailleuse slots from step array.
        slots = _value_at_time(t_now, step_times, step_log.get("slots", []))
        occupied = []
        if slots is not None:
            occupied = [i for i, v in enumerate(slots) if v is not None]
        step_centers = []
        if slot_count <= 1:
            if occupied:
                step_centers.append((x_right, y_gren))
        else:
            for idx in occupied:
                x = _lin_map(float(idx), 0.0, float(slot_count - 1), x_right, x_left)
                step_centers.append((x, y_gren))
        _update_pool(step_pool, step_centers)

        inspect_items_now = _value_at_time(t_now, times, inspect_items_series) or []
        inspector_item_now = _value_at_time(t_now, times, inspector_item_series)
        post_inspect_items_now = _value_at_time(t_now, times, post_inspect_items_series) or []
        is_busy = inspector_item_now is not None
        inferred_sink_wait = _in_any_interval(t_now, sink_wait_intervals)
        cont_end_visible = any(
            float(item.get("pos", 0.0)) >= l_cont - 1e-6
            for item in cont_items
        )
        show_sink_slot = (bool(inspect_items_now) or inferred_sink_wait) and not cont_end_visible
        if show_sink_slot:
            buffer_patch.set_xy((x_buffer - BOTTLE_W / 2.0, y_buffer - BOTTLE_H / 2.0))
            buffer_patch.set_visible(True)
        else:
            buffer_patch.set_visible(False)

        completed_count = bisect_right(inspected_times, t_now)
        if completed_count > last_completed_count and is_busy:
            # Completion and next-start can happen back-to-back with no idle gap.
            # Reset cycle start to the latest completion timestamp.
            inspector_cycle_start_t = inspected_times[completed_count - 1]
        last_completed_count = completed_count
        step_time_now = _value_at_time(t_now, monitor_t, step_time_series)
        step_time_now = float(step_time_now)
        mult = (step_time_now / base_step_time) if base_step_time > 0 else 0.0
        step_time_text.set_text(
            f"Temps de pas = {step_time_now:.2f}s ({mult:.2f}x)\n"
            f"Plage: {min_step_time:.2f}s - {max_step_time:.2f}s"
        )
        t_start = t_now - STOP_PCT_WINDOW_S
        blocked_in_window = 0.0
        for b_start, b_end in blocked_intervals:
            overlap_start = max(t_start, float(b_start))
            overlap_end = min(t_now, float(b_end))
            if overlap_end > overlap_start:
                blocked_in_window += overlap_end - overlap_start
        window_len = max(1e-9, min(STOP_PCT_WINDOW_S, max(0.0, t_now)))
        stop_pct = 100.0 * blocked_in_window / window_len
        stop_pct_text.set_text(f"Arrêt % ({int(STOP_PCT_WINDOW_S)}s) = {stop_pct:.1f}%")
        if total_time > 0.0:
            stop_kpi = 100.0 * blocked_time_total / total_time
        else:
            stop_kpi = 0.0
        stop_kpi_text.set_text(f"Arrêt KPI (simulation) = {stop_kpi:.2f}%")
        det1_now = int(_value_at_time(t_now, times, det1_series) or 0)
        det2_now = int(_value_at_time(t_now, times, det2_series) or 0)
        det3_now = int(_value_at_time(t_now, times, det3_series) or 0)
        det4_now = int(_value_at_time(t_now, times, det4_series) or 0)
        has_var_bottle_in_det4_zone = any(
            (p >= 0.0) and (p <= float(Parameter_horizontal.horizontal_spacing))
            for p in var_positions
        )
        det4_vis = 1 if (det4_now == 1 and has_var_bottle_in_det4_zone) else 0
        det_vals = [det1_now, det2_now, det3_now, det4_vis]
        for patch, is_on in zip(sensor_patches, det_vals):
            patch.set_facecolor("#e74c3c" if is_on else "none")
        post_inspect_ids_now = {
            int(item["id"])
            for item in post_inspect_items_now
            if item.get("id") is not None
        }
        if not post_inspect_ids_now:
            post_inspect_ids_now = _ids_in_interval(
                t_now,
                bottle_history,
                "post_inspect_entry",
                "post_inspect_exit",
            )
        if inspector_item_now is not None:
            post_inspect_ids_now.discard(int(inspector_item_now))
        in_post_unload_delay = bool(post_inspect_ids_now)
        if in_post_unload_delay:
            post_inspect_patch.set_xy(
                (POST_INSPECT_X - BOTTLE_W / 2.0, POST_INSPECT_Y - BOTTLE_H / 2.0)
            )
            post_inspect_patch.set_visible(True)
        else:
            post_inspect_patch.set_visible(False)
        output_count_now = bisect_right(inspected_times, t_now)
        sim_stats_text.set_text(
            f"Temps simulation = {t_now:.1f}s\nBouteilles sorties = {output_count_now}"
        )
        if is_busy:
            if inspector_cycle_start_t is None:
                inspector_cycle_start_t = t_now
            inspector_patch.set_xy((x_inspector - BOTTLE_W / 2.0, y_inspector - BOTTLE_H / 2.0))
            inspector_patch.set_visible(True)
            elapsed = max(0.0, t_now - inspector_cycle_start_t)
            inspector_timer_text.set_text(f"Temps D'Inspection = {elapsed:.1f}s")
        else:
            inspector_patch.set_visible(False)
            inspector_cycle_start_t = None
            inspector_timer_text.set_text("Temps D'Inspection = 0.0s")

        title.set_text(f"Temps = {t_now:7.1f}s")

        return (
            pre_pool
            + handoff_pool
            + pre_var_buffer_pool
            + var_pool
            + cont_pool
            + step_pool
            + [
                buffer_patch,
                inspector_patch,
                post_inspect_patch,
                title,
                inspector_timer_text,
                inspect_info_text,
                step_time_text,
                stop_pct_text,
                stop_kpi_text,
                sim_stats_text,
                *sensor_patches,
            ]
        )

    anim = animation.FuncAnimation(
        fig,
        update,
        frames=len(render_times),
        interval=max(1, int(frame_interval_ms)),
        blit=False,
    )
    fig._anim = anim
    plt.tight_layout()
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fps_eff = (
            fps
            if fps is not None and fps > 0
            else (1000.0 / frame_interval_ms)
        )
        suffix = save_path.suffix.lower()
        if suffix == ".gif":
            writer = animation.PillowWriter(fps=fps_eff)
        else:
            ffmpeg_bin = _find_ffmpeg_exe()
            if ffmpeg_bin is None:
                fallback_errors = []
                try:
                    import imageio_ffmpeg

                    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
                except Exception as exc:
                    fallback_errors.append(f"imageio_ffmpeg import direct: {exc}")
                    try:
                        user_site = site.getusersitepackages()
                        if user_site and user_site not in sys.path:
                            sys.path.append(user_site)
                        import imageio_ffmpeg

                        ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
                    except Exception as user_exc:
                        fallback_errors.append(f"imageio_ffmpeg user site: {user_exc}")
                        raise RuntimeError(
                            "FFmpeg indisponible pour export MP4. "
                            "Utilise --save fichier.gif ou installe ffmpeg. "
                            + " | ".join(fallback_errors)
                        ) from user_exc
            plt.rcParams["animation.ffmpeg_path"] = ffmpeg_bin
            try:
                writer = animation.FFMpegWriter(fps=fps_eff)
            except Exception as exc:
                raise RuntimeError(
                    "FFmpeg indisponible pour export MP4. Utilise --save fichier.gif ou installe ffmpeg."
                ) from exc
        anim.save(str(save_path), writer=writer)
        print(f"Animation exportee: {save_path}")
        plt.close(fig)
        return
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Animation grenailleuse/convoyeurs sur image.")
    parser.add_argument("--save", type=Path, default=None, help="Chemin de sortie (.mp4 ou .gif)")
    parser.add_argument("--fps", type=int, default=None, help="FPS export (optionnel)")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Demande les parametres de simulation dans le terminal avant execution.",
    )
    args = parser.parse_args()
    interactive = bool(args.interactive or getattr(sys, "frozen", False))
    overrides = collect_simulation_overrides() if interactive else None
    run_animation(save_path=args.save, fps=args.fps, overrides=overrides)


if __name__ == "__main__":
    main()

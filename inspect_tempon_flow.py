import argparse
import csv
import json
from bisect import bisect_right
from pathlib import Path

import Parameter_horizontal
from demo_variable_conveyor_tempon import demo_composite_flow


GRENAILLEUSE_RIGHT_X = 1628.0
GRENAILLEUSE_LEFT_X = 167.0
GRENAILLEUSE_Y = 260.0

TEMPON_X = 167.0
TEMPON_Y_START = 260.0
TEMPON_Y_END = 695.0
TEMPON_VISUAL_END_Y = 616.0

VAR_CONVEYOR_START_X = TEMPON_X
VAR_CONVEYOR_END_X = 1160.0
CONT_CONVEYOR_START_X = 1160.0
CONT_CONVEYOR_END_X = 1460.0

INSPECTOR_MID_X = 1649.0
INSPECTOR_MID_Y = 697.0
SINK_MID_X = 1518.0
SINK_MID_Y = 697.0
POST_INSPECT_X = 1777.0
POST_INSPECT_Y = 697.0

BOTTLE_W = 70.0


def _lin_map(value, in_min, in_max, out_min, out_max):
    if abs(in_max - in_min) < 1e-9:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    t = max(0.0, min(1.0, t))
    return out_min + t * (out_max - out_min)


def _safe_list_item(seq, idx):
    if not seq:
        return None
    if idx < len(seq):
        return seq[idx]
    return seq[-1]


def _value_at_time(t_query, t_series, values):
    if not t_series or not values:
        return 0
    idx = bisect_right(t_series, t_query) - 1
    if idx < 0:
        return values[0]
    if idx >= len(values):
        return values[-1]
    return values[idx]


def _parse_times(raw_times, available_times):
    if raw_times:
        return [float(v) for v in raw_times]
    if not available_times:
        return []
    return list(available_times)


def run_simulation(env_time, sample_time):
    return demo_composite_flow(
        variable_speed=True,
        animate=False,
        plot=False,
        env_time=env_time,
        sample_time=sample_time,
    )


def inspect_flow(result, query_times):
    position_log = result["position_log"]
    step_log = result["step_position_log"]
    monitor = result["monitor"]
    inspected_times = sorted(result.get("inspected_times", []))

    times = position_log.get("t", [])
    step_times = step_log.get("t", [])
    monitor_t = monitor.get("t", [])

    l_first = float(Parameter_horizontal.length_first)
    l_var = float(Parameter_horizontal.length_second)
    l_cont = float(Parameter_horizontal.length_third)
    slot_count = int(Parameter_horizontal.steps)
    x_cont_end = CONT_CONVEYOR_END_X - BOTTLE_W
    handoff_gap = (TEMPON_VISUAL_END_Y - TEMPON_Y_START) / 4.0
    post_unload_delay_s = float(Parameter_horizontal.t_dis)

    out = []
    for t_query in _parse_times(query_times, times):
        frame = bisect_right(times, t_query) - 1
        if frame < 0:
            frame = 0
        t_now = _safe_list_item(times, frame) or 0.0

        pre_items = _safe_list_item(position_log.get("pre_items", []), frame) or []
        var_items = _safe_list_item(position_log.get("position_items", []), frame) or []
        cont_items = _safe_list_item(position_log.get("cont_items", []), frame) or []
        step_output_items = _safe_list_item(position_log.get("step_output_items", []), frame) or []
        pre_var_buffer_items = _safe_list_item(position_log.get("pre_var_buffer_items", []), frame) or []
        inspect_items = _safe_list_item(position_log.get("inspect_items", []), frame) or []
        post_inspect_items = _safe_list_item(position_log.get("post_inspect_items", []), frame) or []
        inspect_count = int(_safe_list_item(position_log.get("inspect_count", []), frame) or 0)

        pre_centers = [
            {
                "bottle_id": item["id"],
                "raw_pos": item["pos"],
                "plot_x": TEMPON_X,
                "plot_y": _lin_map(
                    item["pos"],
                    0.0,
                    l_first,
                    TEMPON_Y_START + handoff_gap,
                    TEMPON_VISUAL_END_Y,
                ),
            }
            for item in pre_items
        ]
        var_centers = [
            {
                "bottle_id": item["id"],
                "raw_pos": item["pos"],
                "plot_x": _lin_map(item["pos"], 0.0, l_var, VAR_CONVEYOR_START_X, VAR_CONVEYOR_END_X),
                "plot_y": TEMPON_Y_END,
            }
            for item in var_items
        ]
        cont_centers = [
            {
                "bottle_id": item["id"],
                "raw_pos": item["pos"],
                "plot_x": _lin_map(
                    min(max(item["pos"], 0.0), l_cont),
                    0.0,
                    l_cont,
                    CONT_CONVEYOR_START_X,
                    x_cont_end,
                ),
                "plot_y": TEMPON_Y_END,
            }
            for item in cont_items
        ]

        slots = _value_at_time(t_now, step_times, step_log.get("slots", []))
        step_positions = []
        if slots is not None:
            for idx, bottle_id in enumerate(slots):
                if bottle_id is None:
                    continue
                plot_x = GRENAILLEUSE_RIGHT_X
                if slot_count > 1:
                    plot_x = _lin_map(
                        float(idx),
                        0.0,
                        float(slot_count - 1),
                        GRENAILLEUSE_RIGHT_X,
                        GRENAILLEUSE_LEFT_X,
                    )
                step_positions.append(
                    {
                        "slot_index": idx,
                        "bottle_id": bottle_id,
                        "plot_x": plot_x,
                        "plot_y": GRENAILLEUSE_Y,
                    }
                )

        handoff_count = int(_value_at_time(t_now, monitor_t, monitor.get("step_output_count", [])) or 0)
        inspector_busy = int(_value_at_time(t_now, monitor_t, monitor.get("inspector_busy", [])) or 0)
        completed_count = bisect_right(inspected_times, t_now)
        in_post_inspect = any(t_done <= t_now < t_done + post_unload_delay_s for t_done in inspected_times)
        inspector_item = _safe_list_item(position_log.get("inspector_item", []), frame)

        out.append(
            {
                "query_time": t_query,
                "log_time": t_now,
                "grenailleuse": {
                    "slots": slots,
                    "occupied_positions": step_positions,
                },
                "step_output_handoff": {
                    "count": handoff_count,
                    "items": step_output_items,
                    "plot_center": [TEMPON_X, TEMPON_Y_START] if handoff_count > 0 else None,
                },
                "tempon_vertical": {
                    "raw_positions": [item["pos"] for item in pre_items],
                    "items": pre_items,
                    "plot_positions": pre_centers,
                },
                "pre_var_buffer": {
                    "count": len(pre_var_buffer_items),
                    "items": pre_var_buffer_items,
                    "plot_center": [TEMPON_X, TEMPON_Y_END - 24.0] if pre_var_buffer_items else None,
                },
                "variable_conveyor": {
                    "raw_positions": [item["pos"] for item in var_items],
                    "items": var_items,
                    "plot_positions": var_centers,
                    "step_mode": bool(_safe_list_item(position_log.get("step_mode", []), frame)),
                },
                "continuous_conveyor": {
                    "raw_positions": [item["pos"] for item in cont_items],
                    "items": cont_items,
                    "plot_positions": cont_centers,
                },
                "sink": {
                    "count": inspect_count,
                    "items": inspect_items,
                    "plot_center": [SINK_MID_X, SINK_MID_Y] if inspect_count > 0 or inspector_busy > 0 else None,
                },
                "inspector": {
                    "busy": inspector_busy,
                    "item": inspector_item,
                    "plot_center": [INSPECTOR_MID_X, INSPECTOR_MID_Y] if inspector_busy > 0 else None,
                },
                "post_inspect": {
                    "visible": in_post_inspect,
                    "completed_count": completed_count,
                    "items": post_inspect_items,
                    "plot_center": [POST_INSPECT_X, POST_INSPECT_Y] if in_post_inspect else None,
                },
                "detectors": {
                    "det1": int(_safe_list_item(position_log.get("det1", []), frame) or 0),
                    "det2": int(_safe_list_item(position_log.get("det2", []), frame) or 0),
                    "det3": int(_safe_list_item(position_log.get("det3", []), frame) or 0),
                    "det4": int(_safe_list_item(position_log.get("det4", []), frame) or 0),
                },
            }
        )
    return out


def build_bottle_tracks(result):
    tracks = []
    bottle_history = result.get("bottle_history", {})
    for bottle_id in sorted(bottle_history):
        stages = dict(bottle_history[bottle_id])
        tracks.append(
            {
                "bottle_id": int(bottle_id),
                "stages": stages,
            }
        )
    return tracks


def write_bottle_tracks_csv(csv_path, tracks):
    stage_names = [
        "grenailleuse_entry",
        "step_output_entry",
        "pre_var_entry",
        "pre_var_exit",
        "variable_entry",
        "variable_exit",
        "continuous_entry",
        "sink_entry",
        "inspector_start",
        "inspector_complete",
        "post_inspect_entry",
        "post_inspect_exit",
    ]
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bottle_id", *stage_names])
        for track in tracks:
            stages = track["stages"]
            writer.writerow([track["bottle_id"], *[stages.get(name, "") for name in stage_names]])


def main():
    parser = argparse.ArgumentParser(description="Inspect tempon animation state by time.")
    parser.add_argument("--env-time", type=float, default=420.0)
    parser.add_argument("--sample-time", type=float, default=1.0)
    parser.add_argument("--time", dest="times", action="append")
    parser.add_argument("--bottle-id", type=int)
    parser.add_argument("--all-bottles", action="store_true")
    parser.add_argument("--out-csv")
    parser.add_argument("--stages-only", action="store_true")
    args = parser.parse_args()

    result = run_simulation(args.env_time, args.sample_time)
    snapshots = inspect_flow(result, args.times)
    tracks = build_bottle_tracks(result)

    if args.out_csv:
        write_bottle_tracks_csv(args.out_csv, tracks)

    if args.bottle_id is not None:
        bottle_track = next(
            (track for track in tracks if track["bottle_id"] == args.bottle_id),
            None,
        )
        if args.stages_only or not args.times:
            print(json.dumps(bottle_track, indent=2))
            return
        output = {"snapshots": snapshots, "bottle_track": bottle_track}
    elif args.all_bottles:
        if args.stages_only:
            print(json.dumps(tracks, indent=2))
            return
        output = {"snapshots": snapshots, "bottle_tracks": tracks}
    else:
        output = {"snapshots": snapshots}

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

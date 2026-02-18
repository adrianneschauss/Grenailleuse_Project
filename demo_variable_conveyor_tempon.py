import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from matplotlib import animation
import Parameter_horizontal
from functions import (
    arrival_process,
    create_step_conveyor,
    load_step_conveyor,
    step_conveyor_advance,
    continuous_conveyor,
    _buffer_get,
    _buffer_has_space,
    _buffer_put,
    inspector_process,
    unload_delay,
    inspect_time
)

def demo_composite_flow(
    variable_speed = None,
    mean_interval=None,
    down_time=None,
    min_inter=None,
    max_inter=None,
    t_dis=None,
    t_dis2=None,
    inspect_min=None,
    inspect_max=None,
    max_long = None,
    min_long = None,
    s = None,
    step_time=None,
    step_time_2 = None, 
    steps=None,
    gr_conv=None,
    cont_out_capacity=None,
    length=None,
    length_first=None,
    length_second=None,
    length_third = None,
    spacing=None,
    horizontal_spacing=None,
    vertical_spacing = None,
    speed=None,
    speed_tempon = None,
    first_speed=None,
    second_speed=None,
    dt=None,
    env_time=None,
    sample_time=1.0,
    plot=True,
    animate=False,
    animation_interval_ms=50,
    mode_switch_delay=1.0,
    p_buffer_capacity=None,
    det_hold_time = None,
    speed_ctrl_control_dt=None,
    speed_ctrl_window_s=None,
    speed_ctrl_slow_band=None,
    speed_ctrl_fast_band=None,
    speed_ctrl_streak_required=None,
    speed_ctrl_slow_factor=None,
    speed_ctrl_fast_factor=None,
    speed_ctrl_min_step_mult=None,
    speed_ctrl_max_step_mult=None,
    speed_ctrl_w_step_out=None,
    speed_ctrl_w_pre_var=None,
    speed_ctrl_w_var=None,
    speed_ctrl_w_cont=None,
    speed_ctrl_w_inspect=None,
):
    env = simpy.Environment()
    if variable_speed is None:
        variable_speed = Parameter_horizontal.variable_speed
    if mean_interval is None:
        mean_interval = Parameter_horizontal.mean_interval
    if down_time is None:
        down_time = Parameter_horizontal.down_time
    if min_inter is None:
        min_inter = Parameter_horizontal.min_iter
    if max_inter is None:
        max_inter = Parameter_horizontal.max_iter
    if t_dis is None:
        t_dis = Parameter_horizontal.t_dis
    if t_dis2 is None:
        t_dis2 = Parameter_horizontal.t_dis2
    if inspect_min is None:
        inspect_min = Parameter_horizontal.inspect_min
    if inspect_max is None:
        inspect_max = Parameter_horizontal.inspect_max
    if max_long is None:
        max_long = Parameter_horizontal.max
    if min_long is None:
        min_long = Parameter_horizontal.min 
    if s is None:
        s = Parameter_horizontal.s
    if step_time is None:
        step_time = Parameter_horizontal.step_time
    if step_time_2 is None:
        step_time_2 = Parameter_horizontal.step_time_2
    if steps is None:
        steps = Parameter_horizontal.steps
    if gr_conv is None:
        gr_conv = Parameter_horizontal.gr_conv
    if cont_out_capacity is None:
        cont_out_capacity = 1
    if length_first is None:
        length_first = Parameter_horizontal.length_first
    if length_second is None:
        length_second = Parameter_horizontal.length_second
    if length_third is None:
        length_third = Parameter_horizontal.length_third
    if horizontal_spacing is None:
        horizontal_spacing = Parameter_horizontal.horizontal_spacing
    if vertical_spacing is None:
        vertical_spacing = Parameter_horizontal.vertical_spacing
    if speed_tempon is None:
        speed_tempon = Parameter_horizontal.speed_tempon
    if first_speed is None:
        first_speed = Parameter_horizontal.first_speed
    if second_speed is None:
        second_speed = Parameter_horizontal.second_speed
    if dt is None:
        dt = Parameter_horizontal.dt
    if env_time is None:
        env_time = Parameter_horizontal.env_time
    if det_hold_time is None:
        det_hold_time = Parameter_horizontal.det_hold_time
    if speed_ctrl_control_dt is None:
        speed_ctrl_control_dt = Parameter_horizontal.speed_ctrl_control_dt
    if speed_ctrl_window_s is None:
        speed_ctrl_window_s = Parameter_horizontal.speed_ctrl_window_s
    if speed_ctrl_slow_band is None:
        speed_ctrl_slow_band = Parameter_horizontal.speed_ctrl_slow_band
    if speed_ctrl_fast_band is None:
        speed_ctrl_fast_band = Parameter_horizontal.speed_ctrl_fast_band
    if speed_ctrl_streak_required is None:
        speed_ctrl_streak_required = Parameter_horizontal.speed_ctrl_streak_required
    if speed_ctrl_slow_factor is None:
        speed_ctrl_slow_factor = Parameter_horizontal.speed_ctrl_slow_factor
    if speed_ctrl_fast_factor is None:
        speed_ctrl_fast_factor = Parameter_horizontal.speed_ctrl_fast_factor
    if speed_ctrl_min_step_mult is None:
        speed_ctrl_min_step_mult = Parameter_horizontal.speed_ctrl_min_step_mult
    if speed_ctrl_max_step_mult is None:
        speed_ctrl_max_step_mult = Parameter_horizontal.speed_ctrl_max_step_mult
    if speed_ctrl_w_step_out is None:
        speed_ctrl_w_step_out = 0.450
    if speed_ctrl_w_pre_var is None:
        speed_ctrl_w_pre_var = 0.192 
    if speed_ctrl_w_var is None:
        speed_ctrl_w_var = 0.288
    if speed_ctrl_w_cont is None:
        speed_ctrl_w_cont = 0.018
    if speed_ctrl_w_inspect is None:
        speed_ctrl_w_inspect =  0.051

    w_sum = (
        float(speed_ctrl_w_step_out)
        + float(speed_ctrl_w_pre_var)
        + float(speed_ctrl_w_var)
        + float(speed_ctrl_w_cont)
        + float(speed_ctrl_w_inspect)
    )
    if w_sum <= 0.0:
        speed_ctrl_w_step_out = 0.450
        speed_ctrl_w_pre_var = 0.192 
        speed_ctrl_w_var = 0.288
        speed_ctrl_w_cont = 0.018
        speed_ctrl_w_inspect = 0.051
        w_sum = 1.0
    speed_ctrl_w_step_out = float(speed_ctrl_w_step_out) / w_sum
    speed_ctrl_w_pre_var = float(speed_ctrl_w_pre_var) / w_sum
    speed_ctrl_w_var = float(speed_ctrl_w_var) / w_sum
    speed_ctrl_w_cont = float(speed_ctrl_w_cont) / w_sum
    speed_ctrl_w_inspect = float(speed_ctrl_w_inspect) / w_sum
    
    
#--------------------------------------------------------------------
#--------------------------------------------------------------------
#--------------------------------------------------------------------
    if p_buffer_capacity is None:
        p_buffer_capacity = 9
    p_buffer = simpy.Store(env, capacity=p_buffer_capacity)
    pre_step_buffer = simpy.Store(env, capacity=1)
#____
# first step conveyor (grenailleuse)
    step_g = create_step_conveyor(env, "G_step", step_time=step_time, steps=steps, output_capacity=1)

    grenailleuse_exit_times = []
    second_conv_exit_times = [] 
    inspector = simpy.Resource(env, capacity=1)
    arrival_times = []
    env.process(
        arrival_process(
            env,
            p_buffer,
            step_g,
            mean_interval,
            down_time,
            min_inter,
            max_inter,
        )
    )

    def feed_pre_step():
        while True:
            yield _buffer_get(p_buffer)
            placed = False
            while not placed:
                if _buffer_has_space(pre_step_buffer):
                    yield _buffer_put(pre_step_buffer)
                    placed = True
                else:
                    yield env.timeout(0.01)

    env.process(feed_pre_step())
    env.process(load_step_conveyor(env, pre_step_buffer, step_g, arrival_times))
    grenailleuse_blocked_time = [0.0]
    env.process(step_conveyor_advance(env, step_g, gr_conv, grenailleuse_exit_times, grenailleuse_blocked_time)) 
    # downstream chain: pre-variable continuous conveyor -> variable conveyor -> continuous conveyor -> det2 hold -> det1 hold -> inspector
    # Keep only a handoff slot after the pre-variable conveyor.
    # The in-flight capacity is already enforced by continuous_conveyor(length_first, vertical_spacing).
    pre_var_in = simpy.Store(env, capacity=1)
    det1_hold = simpy.Store(env, capacity=1)
    cont_items_state = {"items": []}
    det_state = {"det1": 0, "det2": 0, "det3": 0, "det4": 0}
    position_log = {
        "t": [],
        "positions": [],
        "cont_positions": [],
        "pre_positions": [],
        "inspect_count": [],
        "step_mode": [],
        "det1": [],
        "det2": [],
        "det3": [],
        "det4": [],
    }
    step_position_log = {
        "t": [],
        "slots": [],
    }

    pre_position_state = {"positions": []}
    def pre_conveyor_logger(now, segment_id, items, segment_length=None):
        pre_position_state["positions"] = [item["pos"] for item in items]

    env.process(
        continuous_conveyor(
            env,
            length=length_first,
            speed=speed_tempon,
            dt=dt,
            input_store=step_g["output_store"],
            spacing=vertical_spacing,
            out_store=pre_var_in,
            position_logger=pre_conveyor_logger,
            segment_id="pre_var",
            segment_length=length_first,
        )
    )

    def position_logger(
        now,
        segment_id,
        items,
        segment_length=None,
        step_mode=None,
        det1=None,
        det2=None,
        det3=None,
        det4=None,
    ):
        position_log["t"].append(now)
        position_log["positions"].append([item["pos"] for item in items])
        position_log["cont_positions"].append(
            [item["pos"] for item in cont_items_state["items"]]
        )
        position_log["pre_positions"].append(pre_position_state["positions"])
        position_log["inspect_count"].append(len(det1_hold.items))
        position_log["step_mode"].append(step_mode)
        position_log["det1"].append(det1)
        position_log["det2"].append(det2)
        position_log["det3"].append(det3)
        position_log["det4"].append(det4)

    
    def detector_active(hold_store, now, hold_time):
        if not hold_store.items:
            return 0
        started = hold_store.items[0].get("hold_start", now)
        return 1 if now - started >= hold_time else 0

    def variable_conveyor_segment(
        env,
        length,
        speed,
        dt,
        input_store,
        spacing,
        state_ref,
        position_logger=None,
        segment_id=None,
        segment_length=None,
        mode_switch_delay= None,
        step_time=Parameter_horizontal.step_time,
    ):
        items = []
        max_items = int(length // spacing)
        if step_time is None:
            step_interval = spacing / speed if speed > 0 else dt
        else:
            step_interval = step_time
        step_acc = 0.0
        last_mode = None
        last_mode_change_time = 0.0
        det12_start = None
        det3_state = 0
        det4_state = 0
        while True:
            det2 = cont_end_state["active"]
            det1 = detector_active(det1_hold, env.now, det_hold_time)

            if det1 == 1 and det2 == 1:
                if det12_start is None:
                    det12_start = env.now
            else:
                det12_start = None

            if last_mode is None:
                last_mode = False
                last_mode_change_time = env.now

            step_mode = last_mode
            if not step_mode and det12_start is not None and env.now - det12_start >= det_hold_time:
                step_mode = True
            if step_mode:
                if (det1 == 1 and det2 == 0 and det3_state == 0 and det4_state == 0) or (
                    det1 == 0 and det2 == 0 and det3_state == 0 and det4_state == 0
                ):
                    step_mode = False

            if last_mode != step_mode:
                step_acc = 0.0
                last_mode = step_mode
                last_mode_change_time = env.now

            if (
                input_store.items
                and (not items or min(item["pos"] for item in items) >= spacing)
                and len(items) < max_items
            ):
                item = yield input_store.get()
                items.append(
                    {"payload": item, "pos": 0.0, "entry_start": env.now}
                )
            if step_mode:
                step_acc += dt
                if step_acc >= step_interval:
                    step_acc -= step_interval
                    # If the end is blocked (items already at the end),
                    # hold position to avoid compressing past spacing.
                    if not any(item["pos"] >= length - 1e-6 for item in items):
                        for item in items:
                            item["pos"] += spacing
                            if item["pos"] > length:
                                item["pos"] = length
            else:
                # In continuous mode, stop the entire conveyor if an item is at the end.
                if not any(item["pos"] >= length - 1e-6 for item in items):
                    for item in items:
                        item["pos"] += speed * dt
                        if item["pos"] > length:
                            item["pos"] = length
            det3_state = 0
            for item in items:
                if item["pos"] >= length - 1e-6:
                    if "end_start" not in item:
                        item["end_start"] = env.now
                    if env.now - item["end_start"] >= det_hold_time:
                        det3_state = 1
                        break
                else:
                    item.pop("end_start", None)
            det4_state = 0
            for item in items:
                if item["pos"] <= spacing:
                    if "start_hold_start" not in item:
                        item["start_hold_start"] = env.now
                    if env.now - item["start_hold_start"] >= det_hold_time:
                        det4_state = 1
                        break
                else:
                    item.pop("start_hold_start", None)
            state_ref["items"] = items
            det_state["det1"] = det1
            det_state["det2"] = det2
            det_state["det3"] = det3_state
            det_state["det4"] = det4_state

            if position_logger is not None:
                position_logger(
                    env.now,
                    segment_id,
                    items,
                    segment_length=segment_length,
                    step_mode=step_mode,
                    det1=det1,
                    det2=det2,
                    det3=det3_state,
                    det4=det4_state,
                )
            yield env.timeout(dt)

    cont_end_state = {"active": 0}
    var_items_state = {"items": []}

    def cont_end_detector():
        while True:
            cont_end_state["active"] = 0
            for item in cont_items_state["items"]:
                if item["pos"] >= length_third and item["end_start"] is not None:
                    if env.now - item["end_start"] >= det_hold_time:
                        cont_end_state["active"] = 1
                        break
            yield env.timeout(dt)




    def grenailleuse_speed_controller(
        control_dt=speed_ctrl_control_dt,
        window_s=speed_ctrl_window_s,
        slow_band=speed_ctrl_slow_band,
        fast_band=speed_ctrl_fast_band,
        streak_required=speed_ctrl_streak_required,
        slow_factor=speed_ctrl_slow_factor,
        fast_factor=speed_ctrl_fast_factor,
    ):
        from collections import deque
        window_len = max(1, int(window_s / control_dt))
        pressure_window = deque(maxlen=window_len)
        slow_streak = 0
        fast_streak = 0
        base_step = step_g["step_time"]
        min_step = base_step * speed_ctrl_min_step_mult
        max_step = base_step * speed_ctrl_max_step_mult
        pre_var_cap = max(1, pre_var_in.capacity)
        var_cap = max(1, int(length_second // horizontal_spacing))
        cont_cap = max(1, int(length_third // horizontal_spacing))
        inspect_cap = max(1, det1_hold.capacity)
        step_out_cap = max(1, step_g["output_store"].capacity)
        while True:
            step_out_fill = len(step_g["output_store"].items) / step_out_cap
            pre_var_fill = len(pre_var_in.items) / pre_var_cap
            var_fill = len(var_items_state["items"]) / var_cap
            cont_fill = len(cont_items_state["items"]) / cont_cap
            inspect_fill = len(det1_hold.items) / inspect_cap
            downstream_pressure = (
                speed_ctrl_w_step_out * step_out_fill
                + speed_ctrl_w_pre_var * pre_var_fill
                + speed_ctrl_w_var * var_fill
                + speed_ctrl_w_cont * cont_fill
                + speed_ctrl_w_inspect * inspect_fill
            )
            pressure_window.append(downstream_pressure)
            pressure_avg = sum(pressure_window) / len(pressure_window)
            upstream_backlog = bool(p_buffer.items or pre_step_buffer.items)
            if pressure_avg >= slow_band:
                slow_streak += 1
                fast_streak = 0
            elif pressure_avg <= fast_band and upstream_backlog:
                fast_streak += 1
                slow_streak = 0
            else:
                slow_streak = 0
                fast_streak = 0
            if slow_streak >= streak_required:
                step_g["step_time"] = min(step_g["step_time"] * slow_factor, max_step)
                slow_streak = 0
                fast_streak = 0
            elif fast_streak >= streak_required:
                step_g["step_time"] = max(step_g["step_time"] * fast_factor, min_step)
                slow_streak = 0
                fast_streak = 0
            yield env.timeout(control_dt)

    def continuous_conveyor_segment_with_state(
        env,
        length,
        speed,
        dt,
        source_state,
        spacing,
        end_store,
        end_hold_time,
        arrival_log=None,
        exit_times=None,
    ):
        items = []
        max_items = int(length // spacing) 
        cont_items_state["items"] = items
        while True:
            if (not items or items[0]["pos"] >= spacing) and len(items) < max_items:
                src_items = source_state["items"]
                for i, src in enumerate(src_items):
                    if src["pos"] >= length_second - 1e-6:
                        src_items.pop(i)
                        items.append({"payload": src["payload"], "pos": 0.0, "end_start": None})
                        break
            for item in items:
                item["pos"] += speed * dt
            remaining = []
            for item in items:
                if item["pos"] >= length:
                    if item["end_start"] is None:
                        item["end_start"] = env.now
                    if len(end_store.items) < end_store.capacity:
                        payload = item["payload"]
                        if not isinstance(payload, dict) or "id" not in payload:
                            payload = {"id": payload}
                        payload["hold_start"] = env.now
                        yield end_store.put(payload)
                        if arrival_log is not None:
                            arrival_log.append(env.now)
                        if exit_times is not None:
                            exit_times.append(env.now)
                    else:
                        remaining.append(item)
                else:
                    remaining.append(item)
            items = remaining
            cont_items_state["items"] = items
            yield env.timeout(dt)

    inspector_arrival_times = []
    env.process(
        variable_conveyor_segment(
            env,
            length=length_second,
            speed=first_speed,
            dt=dt,
            input_store=pre_var_in,
            spacing=horizontal_spacing,
            state_ref=var_items_state,
            position_logger=position_logger,
            segment_id="variable",
            segment_length=length_second,
            mode_switch_delay=mode_switch_delay,
            step_time=step_time_2,
        )
    )
    env.process(
        continuous_conveyor_segment_with_state(
            env,
            length=length_third,
            speed=second_speed,
            dt=dt,
            source_state=var_items_state,
            spacing=horizontal_spacing,
            end_store=det1_hold,
            end_hold_time=det_hold_time,
            arrival_log=inspector_arrival_times,
            exit_times=second_conv_exit_times,
        )
    )
    env.process(cont_end_detector())
    if variable_speed:
        env.process(grenailleuse_speed_controller())
    else:
        pass
    
    post_inspect = simpy.Store(env)

    post_inspect_delay = t_dis

    inspected_times = []
    busy_time = [0.0]
    env.process(
        inspector_process(
            env,
            inspector,
            det1_hold,
            lambda: inspect_time(inspect_min, inspect_max, s, max_long, min_long),
            inspected_times,
            busy_time,
            output_store=post_inspect,
        )
    )
    env.process(unload_delay(env, post_inspect, simpy.Store(env), post_inspect_delay))

    monitor = {
        "t": [],
        "cont_out": [],
        "inspect_buffer": [],
        "post_inspect": [],
        "inspector_busy": [],
        "grenailleuse_step_time": [],
        "grenailleuse_speed_hz": [],
    }

    def monitor_process():
        while True:
            monitor["t"].append(env.now)
            monitor["cont_out"].append(len(cont_items_state["items"]))
            monitor["inspect_buffer"].append(len(det1_hold.items))
            monitor["post_inspect"].append(len(post_inspect.items))
            monitor["inspector_busy"].append(inspector.count)
            step_time_now = float(step_g["step_time"])
            monitor["grenailleuse_step_time"].append(step_time_now)
            monitor["grenailleuse_speed_hz"].append(1.0 / step_time_now if step_time_now > 0 else 0.0)
            yield env.timeout(sample_time)

    env.process(monitor_process())
    def step_position_monitor():
        while True:
            step_position_log["t"].append(env.now)
            step_position_log["slots"].append(list(step_g["slots"]))
            yield env.timeout(sample_time)

    env.process(step_position_monitor())

    env.run(env_time)
    idle_time = busy_time[0]
    #print(f"Inspector busy time: {idle_time:.2f}s over {env.now:.2f}s total")
    step_time_total = 0.0
    cont_time_total = 0.0
    switches = 0
    if position_log["t"]:
        last_mode = position_log["step_mode"][0]
        for i in range(1, len(position_log["t"])):
            dt_sample = position_log["t"][i] - position_log["t"][i - 1]
            if position_log["step_mode"][i - 1]:
                step_time_total += dt_sample
            else:
                cont_time_total += dt_sample
            if position_log["step_mode"][i] != last_mode:
                switches += 1
                last_mode = position_log["step_mode"][i]
        #print(f"Mode totals: STEP={step_time_total:.2f}s CONT={cont_time_total:.2f}s switches={switches}")

    if animate:
        if position_log["t"]:
            inspector_arrival_times_sorted = sorted(inspector_arrival_times)
            arrival_counts = []
            arrival_idx = 0
            for t in position_log["t"]:
                while arrival_idx < len(inspector_arrival_times_sorted) and inspector_arrival_times_sorted[arrival_idx] <= t:
                    arrival_idx += 1
                arrival_counts.append(arrival_idx)

            show_step = bool(step_position_log["t"])
            show_pre = True
            if show_step:
                fig, (ax_step, ax_pre, ax_var, ax_cont) = plt.subplots(4, 1, figsize=(8, 9.0), sharex=False)
            else:
                fig, (ax_pre, ax_var, ax_cont) = plt.subplots(3, 1, figsize=(8, 7.0), sharex=False)
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

            box_size = 0.6
            buffer_x = length_third + horizontal_spacing * 0.4
            inspector_x = length_third + horizontal_spacing * 1.1
            ax_cont.set_xlim(-horizontal_spacing, length_third + horizontal_spacing * 2.0)
            ax_cont.set_ylim(-1, 1.5)
            ax_cont.set_yticks([])
            ax_cont.set_xlabel("Continuous conveyor position")

            ax_cont.hlines(0, 0, length_third, color="black", linewidth=2)
            ax_cont.hlines(0, length_third, buffer_x, color="black", linewidth=1.0, linestyle="--")
            ax_cont.vlines(0, -0.2, 0.2, color="tab:green", linewidth=2)
            ax_cont.vlines(length_third, -0.2, 0.2, color="tab:red", linewidth=2)
            ax_cont.text(0, 0.35, "Continuous start", ha="left", va="bottom", fontsize=9)
            ax_cont.text(length_third, 0.35, "Det2 / Inspector input", ha="right", va="bottom", fontsize=9)

            scat_var = ax_var.scatter([], [], s=60, color="tab:blue")
            scat_cont = ax_cont.scatter([], [], s=60, color="tab:orange")
            scat_step = ax_step.scatter([], [], s=80, color="tab:blue") if show_step else None
            scat_pre = ax_pre.scatter([], [], s=60, color="tab:purple")
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

            def init():
                scat_var.set_offsets(np.empty((0, 2)))
                scat_cont.set_offsets(np.empty((0, 2)))
                if show_step:
                    scat_step.set_offsets(np.empty((0, 2)))
                scat_pre.set_offsets(np.empty((0, 2)))
                scat_buffer.set_offsets(np.empty((0, 2)))
                scat_inspector.set_offsets(np.empty((0, 2)))
                scat_handoff.set_offsets(np.empty((0, 2)))
                return (scat_step, scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff) if show_step else (scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff)

            def update(frame):
                positions = position_log["positions"][frame]
                offsets = np.column_stack((positions, np.zeros(len(positions)))) if positions else np.empty((0, 2))
                scat_var.set_offsets(offsets)
                cont_positions = position_log["cont_positions"][frame]
                cont_positions = [min(p, length_third) for p in cont_positions]
                cont_offsets = (
                    np.column_stack((cont_positions, np.zeros(len(cont_positions))))
                    if cont_positions
                    else np.empty((0, 2))
                )
                scat_cont.set_offsets(cont_offsets)
                pre_positions = position_log["pre_positions"][frame]
                pre_offsets = (
                    np.column_stack((pre_positions, np.zeros(len(pre_positions))))
                    if pre_positions
                    else np.empty((0, 2))
                )
                scat_pre.set_offsets(pre_offsets)
                if show_step and step_position_log["t"]:
                    step_idx = frame if frame < len(step_position_log["t"]) else len(step_position_log["t"]) - 1
                    slots = step_position_log["slots"][step_idx]
                    occupied = [i for i, v in enumerate(slots) if v is not None]
                    step_offsets = (
                        np.column_stack((np.array(occupied) * slot_size + slot_size * 0.5, np.zeros(len(occupied))))
                        if occupied
                        else np.empty((0, 2))
                    )
                    scat_step.set_offsets(step_offsets)
                inspect_counts = position_log.get("inspect_count", [])
                has_buffer = frame < len(inspect_counts) and inspect_counts[frame] > 0
                if has_buffer:
                    scat_buffer.set_offsets(np.array([[buffer_x, 0.0]]))
                else:
                    scat_buffer.set_offsets(np.empty((0, 2)))
                inspector_busy = monitor.get("inspector_busy", [])
                has_inspector = frame < len(inspector_busy) and inspector_busy[frame] > 0
                if has_inspector:
                    scat_inspector.set_offsets(np.array([[inspector_x, 0.0]]))
                else:
                    scat_inspector.set_offsets(np.empty((0, 2)))
                needs_handoff = has_buffer and (not cont_positions or max(cont_positions) < length_third - 1e-6)
                if needs_handoff:
                    scat_handoff.set_offsets(np.array([[length_third, 0.0]]))
                else:
                    scat_handoff.set_offsets(np.empty((0, 2)))
                return (scat_step, scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff) if show_step else (scat_pre, scat_var, scat_cont, scat_buffer, scat_inspector, scat_handoff)

            anim = animation.FuncAnimation(
                fig,
                update,
                frames=len(position_log["t"]),
                init_func=init,
                interval=animation_interval_ms,
                blit=False,
            )
            fig._anim = anim
            plt.tight_layout()
            plt.show()

    if plot and inspected_times:
        inspected_times_sorted = sorted(inspected_times)
        counts = list(range(1, len(inspected_times_sorted) + 1))
        plt.plot(inspected_times_sorted, counts, marker="x", linestyle="-")
        plt.xlabel("Time")
        plt.ylabel("Cumulative inspected bottles")
        plt.title("Output Bottles Over Time")
        plt.tight_layout()
        plt.show()

    return {
        "inspected_times": inspected_times,
        "arrival_times": arrival_times,
        "grenailleuse_exit_times": grenailleuse_exit_times,
        "grenailleuse_blocked_time": grenailleuse_blocked_time[0],
        "conveyor_exit_times": second_conv_exit_times,
        "position_log": position_log,
        "step_position_log": step_position_log,
        "inspector_arrival_times": inspector_arrival_times,
        "monitor": monitor,
        "busy_time": busy_time[0],
        "total_time": env.now,
        "step_time_total": step_time_total,
        "cont_time_total": cont_time_total,
        "mode_switches": switches,
    }

if __name__ == "__main__":
    inst = demo_composite_flow(animate=True, plot=True)
    print(rf'the blocked time is about {inst["grenailleuse_blocked_time"]}')
    

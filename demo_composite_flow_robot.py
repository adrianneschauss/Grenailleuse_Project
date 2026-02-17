import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
import Parameter_horizontal
from functions import create_step_conveyor, arrival_process, _buffer_get, _buffer_has_space, _buffer_put, load_step_conveyor, robot_process, inspect_time, inspector_process, unload_delay, step_conveyor_advance, continuous_conveyor, continuous_conveyor_simple

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
    steps=None,
    gr_conv=None,
    cont_out_capacity=None,
    length=None,
    spacing=None,
    speed=None,
    dt=None,
    env_time=None,
    sample_time=1.0,
    det_hold_time=None,
    p_buffer_capacity=None,
    pre_step_buffer_capacity=None,
    plot=True,
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
    if steps is None:
        steps = Parameter_horizontal.steps
    if gr_conv is None:
        gr_conv = Parameter_horizontal.gr_conv
    if cont_out_capacity is None:
        cont_out_capacity = 1
    if length is None:
        length = Parameter_horizontal.length
    if spacing is None:
        spacing = Parameter_horizontal.spacing
    if speed is None:
        speed = Parameter_horizontal.speed
    if dt is None:
        dt = Parameter_horizontal.dt
    if env_time is None:
        env_time = Parameter_horizontal.env_time
    if det_hold_time is None:
        det_hold_time = Parameter_horizontal.det_hold_time
    if p_buffer_capacity is None:
        p_buffer_capacity = 9
    if pre_step_buffer_capacity is None:
        pre_step_buffer_capacity = 1

    p_buffer = simpy.Store(env, capacity=p_buffer_capacity)
    pre_step_buffer = simpy.Store(env, capacity=pre_step_buffer_capacity)
    step_g = create_step_conveyor(env, "G_step", step_time=step_time, steps=steps, output_capacity=1)
    
    cont_out = simpy.Store(env, capacity=cont_out_capacity)
    inspector = simpy.Resource(env, capacity=1)
    connector_robot = simpy.Resource(env, capacity=1)
    cont_outR = simpy.Store(env, capacity = 1)

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
    grenailleuse_exit_times = []
    conveyor_exit_times = []

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

    robot_times = []
    busyR_time = [0.0]
    
    env.process(robot_process(env, robot=connector_robot, input_store=step_g["output_store"], robot_time=5, moved_times=robot_times,
                               busy_time= busyR_time, output_store=cont_outR))

    cont_items_state = {"items": []}

    def cont_position_logger(now, segment_id, items, segment_length=None):
        cont_items_state["items"] = list(items)

    env.process(
        continuous_conveyor(
            env,
            length=length,
            speed=speed,
            dt=dt,
            input_store=cont_outR,
            spacing=spacing,
            out_store=cont_out,
            exit_times=conveyor_exit_times,
            position_logger=cont_position_logger,
        )
    )

    inspect_buffer = simpy.Store(env, capacity=1)
    post_inspect = simpy.Store(env)

    pre_inspect_delay = t_dis
    post_inspect_delay = t_dis2
    env.process(unload_delay(env, cont_out, inspect_buffer, pre_inspect_delay))
####################################################################################################
    inspected_times = []
    busy_time = [0.0]
    env.process(
        inspector_process(
            env,
            inspector,
            inspect_buffer,
            lambda: inspect_time(inspect_min, inspect_max, s, max_long, min_long),
            inspected_times,
            busy_time,
            output_store=post_inspect,
        )
    )
    env.process(unload_delay(env, post_inspect, simpy.Store(env), post_inspect_delay))
###########################################
    def _head_id(store):
        if not store.items:
            return None
        item = store.items[0]
        if isinstance(item, dict) and "id" in item:
            return item["id"]
        if isinstance(item, dict) and "payload" in item:
            payload = item["payload"]
            if isinstance(payload, dict) and "id" in payload:
                return payload["id"]
        return str(item)

    det_state = {"det1": 0, "det2": 0, "det3": 0}
    det_meta = {
        "cont_outR": {"id": None, "start": None},
        "cont_out": {"id": None, "start": None},
        "inspect_buffer": {"id": None, "start": None},
    }

    monitor = {
        "t": [],
        "cont_outR": [],
        "cont_out": [],
        "cont_items": [],
        "inspect_buffer": [],
        "post_inspect": [],
        "inspector_busy": [],
        "cont_outR_head": [],
        "cont_out_head": [],
        "inspect_buffer_head": [],
        "grenailleuse_step_time": [],
        "grenailleuse_speed_hz": [],
    }

    def _update_det(name, store):
        meta = det_meta[name]
        head_id = _head_id(store)
        if head_id is None:
            meta["id"] = None
            meta["start"] = None
            return 0
        if meta["id"] != head_id:
            meta["id"] = head_id
            meta["start"] = env.now
            return 0
        if meta["start"] is None:
            meta["start"] = env.now
            return 0
        return 1 if env.now - meta["start"] >= det_hold_time else 0

    def detector_process(control_dt=1.0):
        while True:
            det_state["det1"] = _update_det("cont_outR", cont_outR)
            det_state["det2"] = _update_det("cont_out", cont_out)
            det_state["det3"] = _update_det("inspect_buffer", inspect_buffer)
            yield env.timeout(control_dt)

    def grenailleuse_speed_controller(
        control_dt=Parameter_horizontal.speed_ctrl_control_dt,
        window_s=Parameter_horizontal.speed_ctrl_window_s,
        slow_band=Parameter_horizontal.speed_ctrl_slow_band,
        fast_band=Parameter_horizontal.speed_ctrl_fast_band,
        streak_required=Parameter_horizontal.speed_ctrl_streak_required,
        slow_factor=Parameter_horizontal.speed_ctrl_slow_factor,
        fast_factor=Parameter_horizontal.speed_ctrl_fast_factor,
    ):
        from collections import deque
        window_len = max(1, int(window_s / control_dt))
        pressure_window = deque(maxlen=window_len)
        slow_streak = 0
        fast_streak = 0
        base_step = step_g["step_time"]
        min_step = base_step * Parameter_horizontal.speed_ctrl_min_step_mult
        max_step = base_step * Parameter_horizontal.speed_ctrl_max_step_mult
        step_out_cap = max(1, step_g["output_store"].capacity)
        cont_outr_cap = max(1, cont_outR.capacity)
        cont_out_cap = max(1, cont_out.capacity)
        inspect_cap = max(1, inspect_buffer.capacity)
        while True:
            step_out_fill = len(step_g["output_store"].items) / step_out_cap
            robot_out_fill = len(cont_outR.items) / cont_outr_cap
            conv_out_fill = len(cont_out.items) / cont_out_cap
            inspect_fill = len(inspect_buffer.items) / inspect_cap
            downstream_pressure = (
                0.35 * step_out_fill
                + 0.30 * robot_out_fill
                + 0.20 * conv_out_fill
                + 0.15 * inspect_fill
            )
            pressure_window.append(downstream_pressure)
            pressure_avg = sum(pressure_window) / len(pressure_window)
            upstream_backlog = bool(p_buffer.items or pre_step_buffer.items)
            if pressure_avg >= slow_band:
                slow_streak += 1
                fast_streak = 0
            elif pressure_avg <= fast_band:
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

    def monitor_process():
        while True:
            monitor["t"].append(env.now)
            monitor["cont_outR"].append(len(cont_outR.items))
            monitor["cont_out"].append(len(cont_out.items))
            monitor["cont_items"].append(len(cont_items_state["items"]))
            monitor["inspect_buffer"].append(len(inspect_buffer.items))
            monitor["post_inspect"].append(len(post_inspect.items))
            monitor["inspector_busy"].append(inspector.count)
            monitor["cont_outR_head"].append(_head_id(cont_outR))
            monitor["cont_out_head"].append(_head_id(cont_out))
            monitor["inspect_buffer_head"].append(_head_id(inspect_buffer))
            step_time_now = float(step_g["step_time"])
            monitor["grenailleuse_step_time"].append(step_time_now)
            monitor["grenailleuse_speed_hz"].append(1.0 / step_time_now if step_time_now > 0 else 0.0)
            yield env.timeout(sample_time)

    env.process(monitor_process())
    env.process(detector_process(control_dt=sample_time))
    if variable_speed:
        env.process(grenailleuse_speed_controller())

    env.run(env_time)
    idle_time = busy_time[0]
    #print(f"Inspector busy time: {idle_time:.2f}s over {env.now:.2f}s total")
    #print(f"Grenailleuse blocked time: {grenailleuse_blocked_time[0]:.2f}s")

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
        "conveyor_exit_times": conveyor_exit_times,
        "monitor": monitor,
        "busy_time": busy_time[0],
        "total_time": env.now,
    }

if __name__ == "__main__":
    demo_composite_flow()

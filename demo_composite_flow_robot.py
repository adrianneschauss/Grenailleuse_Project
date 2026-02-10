import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from simpy_objects import Conveyor
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

    p_buffer = Conveyor(env, "P_buffer", conveyor_speed=1, init_load=0, max_load=10)
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
            arrival_times,
        )
    )
    grenailleuse_exit_times = []
    conveyor_exit_times = []
    env.process(load_step_conveyor(env, p_buffer, step_g))
    grenailleuse_blocked_time = [0.0]
    env.process(step_conveyor_advance(env, step_g, gr_conv, grenailleuse_exit_times, grenailleuse_blocked_time))

    robot_times = []
    busyR_time = [0.0]
    
    env.process(robot_process(env, robot=connector_robot, input_store=step_g["output_store"], robot_time=3, moved_times=robot_times,
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

    pre_inspect_delay = t_dis2
    post_inspect_delay = t_dis
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
        control_dt=1.0,
        window_s=30.0,
        slow_ratio=0.7,
        fast_ratio=0.2,
        streak_required=3,
        slow_factor=1.1,
        fast_factor=0.9,
    ):
        from collections import deque
        window_len = max(1, int(window_s / control_dt))
        slow_window = deque(maxlen=window_len)
        fast_window = deque(maxlen=window_len)
        slow_streak = 0
        fast_streak = 0
        base_step = step_g["step_time"]
        min_step = base_step * 0.5
        max_step = base_step * 2.0
        while True:
            d1 = det_state["det1"]
            d2 = det_state["det2"]
            d3 = det_state["det3"]
            slow_window.append(1 if (d1 and d2 and d3) else 0)
            fast_window.append(1 if (d1 and d2) else 0)
            slow_ratio_now = sum(slow_window) / len(slow_window)
            fast_ratio_now = sum(fast_window) / len(fast_window)
            slow_streak = slow_streak + 1 if slow_ratio_now >= slow_ratio else 0
            fast_streak = fast_streak + 1 if fast_ratio_now <= fast_ratio else 0
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
            yield env.timeout(sample_time)

    env.process(monitor_process())
    env.process(detector_process(control_dt=sample_time))
    if variable_speed:
        env.process(grenailleuse_speed_controller())

    env.run(env_time)
    idle_time = busy_time[0]
    print(f"Inspector busy time: {idle_time:.2f}s over {env.now:.2f}s total")
    print(f"Grenailleuse blocked time: {grenailleuse_blocked_time[0]:.2f}s")

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

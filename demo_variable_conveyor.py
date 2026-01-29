import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from matplotlib import animation
from simpy_objects import Conveyor
import Parameter_horizontal
from demo_composite_flow_robot import arrival_process, create_step_conveyor, load_step_conveyor, step_conveyor_advance, variable_conveyor, inspector_process, unload_delay

def demo_composite_flow(
    mean_interval=None,
    down_time=None,
    min_inter=None,
    max_inter=None,
    t_dis=None,
    t_dis2=None,
    inspect_min=None,
    inspect_max=None,
    step_time=None,
    steps=None,
    gr_conv=None,
    cont_out_capacity=None,
    length=None,
    length_first=None,
    length_second=None,
    spacing=None,
    horizontal_spacing=None,
    vertical_spacing = None,
    speed=None,
    first_speed=None,
    second_speed=None,
    dt=None,
    env_time=None,
    sample_time=1.0,
    plot=True,
    animate=False,
    animation_interval_ms=50,
    hold_at_det2=None,
    mode_switch_delay=1.0,
):
    env = simpy.Environment()

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
    if step_time is None:
        step_time = Parameter_horizontal.step_time
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
    if horizontal_spacing is None:
        horizontal_spacing = Parameter_horizontal.horizontal_spacing
    if vertical_spacing is None:
        vertical_spacing = Parameter_horizontal.vertical_spacing
    if first_speed is None:
        first_speed = Parameter_horizontal.first_speed
    if second_speed is None:
        second_speed = Parameter_horizontal.second_speed
    if dt is None:
        dt = Parameter_horizontal.dt
    if env_time is None:
        env_time = Parameter_horizontal.env_time
#--------------------------------------------------------------------
#--------------------------------------------------------------------
#--------------------------------------------------------------------
    p_buffer = Conveyor(env, "P_buffer", conveyor_speed=1, init_load=0, max_load=10)
#____
# first step conveyor (grenailleuse)
    step_g = create_step_conveyor(env, "G_step", step_time=step_time, steps=steps, output_capacity=1)

    grenailleuse_exit_times = []
    second_conv_exit_times = [] 
    inspector = simpy.Resource(env, capacity=1)

    def inspect_time():
        return random.uniform(inspect_min, inspect_max)

    arrival_times = []
    env.process(
        arrival_process(
            env,
            p_buffer,
            mean_interval,
            down_time,
            min_inter,
            max_inter,
            arrival_times,
        )
    )

    env.process(load_step_conveyor(env, p_buffer, step_g))
    env.process(step_conveyor_advance(env, step_g, gr_conv, grenailleuse_exit_times)) 
    #conveyor 1   
    inspect_buffer = simpy.Store(env, capacity=1)
    inspect_ready = simpy.Store(env, capacity=1)
    cont_out = simpy.Store(env, capacity=1)
    position_log = {
        "t": [],
        "positions": [],
        "inspect_count": [],
        "step_mode": [],
        "det1": [],
        "det2": [],
        "det3": [],
        "det4": [],
    }

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
        position_log["inspect_count"].append(len(inspect_buffer.items))
        position_log["step_mode"].append(step_mode)
        position_log["det1"].append(det1)
        position_log["det2"].append(det2)
        position_log["det3"].append(det3)
        position_log["det4"].append(det4)

    env.process(
        variable_conveyor(
            env,
            length=length_second,
            speed=second_speed,
            dt=dt,
            input_store=step_g["output_store"],
            spacing=horizontal_spacing,
            out_store=cont_out,
            inspect_buffer=inspect_buffer,
            inspector=inspector,
            discharge_time=gr_conv,
            exit_times=second_conv_exit_times,
            position_logger=position_logger,
            segment_id="variable",
            segment_length=length_second,
            mode_switch_delay=mode_switch_delay,
        )
    )
    post_inspect = simpy.Store(env)

    if hold_at_det2 is None:
        hold_at_det2 = Parameter_horizontal.hold_at_det2
    post_inspect_delay = t_dis
    inspector_arrival_times = []
    def mark_and_hold_to_ready(env, input_store, hold_store, ready_store, hold_time, arrival_log):
        # Move into det2 immediately, then keep it there until hold_time elapses.
        while True:
            item = yield input_store.get()
            item["ready_time"] = env.now + hold_time
            yield hold_store.put(item)

            while True:
                if hold_store.items and hold_store.items[0] is item:
                    wait = max(0.0, item["ready_time"] - env.now)
                    if wait > 0:
                        yield env.timeout(wait)
                    got = yield hold_store.get()
                    yield ready_store.put(got)
                    arrival_log.append(env.now)
                    break
                yield env.timeout(0.01)

    env.process(mark_and_hold_to_ready(env, cont_out, inspect_buffer, inspect_ready, hold_at_det2, inspector_arrival_times))

    inspected_times = []
    busy_time = [0.0]
    env.process(
        inspector_process(
            env,
            inspector,
            inspect_ready,
            inspect_time,
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
    }

    def monitor_process():
        while True:
            monitor["t"].append(env.now)
            monitor["cont_out"].append(len(cont_out.items))
            monitor["inspect_buffer"].append(len(inspect_buffer.items))
            monitor["post_inspect"].append(len(post_inspect.items))
            monitor["inspector_busy"].append(inspector.count)
            yield env.timeout(sample_time)

    env.process(monitor_process())

    env.run(env_time)
    idle_time = busy_time[0]
    print(f"Inspector busy time: {idle_time:.2f}s over {env.now:.2f}s total")

    if animate:
        if position_log["t"]:
            inspector_arrival_times_sorted = sorted(inspector_arrival_times)
            arrival_counts = []
            arrival_idx = 0
            for t in position_log["t"]:
                while arrival_idx < len(inspector_arrival_times_sorted) and inspector_arrival_times_sorted[arrival_idx] <= t:
                    arrival_idx += 1
                arrival_counts.append(arrival_idx)

            fig, ax = plt.subplots(figsize=(8, 2.5))
            ax.set_xlim(-horizontal_spacing, length_second + horizontal_spacing)
            ax.set_ylim(-1, 1.5)
            ax.set_yticks([])
            ax.set_xlabel("Conveyor position")
            ax.set_title("Variable Conveyor Bottle Movement")

            ax.hlines(0, 0, length_second, color="black", linewidth=2)
            ax.vlines(0, -0.2, 0.2, color="tab:green", linewidth=2)
            ax.vlines(length_second, -0.2, 0.2, color="tab:red", linewidth=2)
            ax.text(0, 0.35, "Step G exit", ha="left", va="bottom", fontsize=9)
            ax.text(length_second, 0.35, "Inspector", ha="right", va="bottom", fontsize=9)

            scat = ax.scatter([], [], s=60, color="tab:blue")
            inspect_text = ax.text(0.5, 1.05, "", transform=ax.transAxes, ha="center", fontsize=9)

            def init():
                scat.set_offsets(np.empty((0, 2)))
                inspect_text.set_text("")
                return scat, inspect_text

            def update(frame):
                positions = position_log["positions"][frame]
                offsets = np.column_stack((positions, np.zeros(len(positions)))) if positions else np.empty((0, 2))
                scat.set_offsets(offsets)
                mode = "STEP" if position_log["step_mode"][frame] else "CONT"
                det1 = position_log["det1"][frame]
                det2 = position_log["det2"][frame]
                det3 = position_log["det3"][frame]
                det4 = position_log["det4"][frame]
                inspect_text.set_text(
                    "Mode: "
                    f"{mode} | det1:{det1} det2:{det2} det3:{det3} det4:{det4}"
                    f" | Inspector queue: {position_log['inspect_count'][frame]}"
                    f" | Arrived: {arrival_counts[frame]}"
                )
                return scat, inspect_text

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
        "conveyor_exit_times": second_conv_exit_times,
        "position_log": position_log,
        "inspector_arrival_times": inspector_arrival_times,
        "monitor": monitor,
        "busy_time": busy_time[0],
        "total_time": env.now,
    }

if __name__ == "__main__":
    demo_composite_flow(animate=True, plot=False)

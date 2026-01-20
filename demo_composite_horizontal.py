import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from simpy_objects import Conveyor
import Parameter_with_distance
from demo_composite_flow_robot import arrival_process, create_step_conveyor, load_step_conveyor, step_conveyor_advance, continuous_conveyor, inspector_process, unload_delay

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
):
    env = simpy.Environment()

    if mean_interval is None:
        mean_interval = Parameter_with_distance.mean_interval
    if down_time is None:
        down_time = Parameter_with_distance.down_time
    if min_inter is None:
        min_inter = Parameter_with_distance.min_iter
    if max_inter is None:
        max_inter = Parameter_with_distance.max_iter
    if t_dis is None:
        t_dis = Parameter_with_distance.t_dis
    if t_dis2 is None:
        t_dis2 = Parameter_with_distance.t_dis2
    if inspect_min is None:
        inspect_min = Parameter_with_distance.inspect_min
    if inspect_max is None:
        inspect_max = Parameter_with_distance.inspect_max
    if step_time is None:
        step_time = Parameter_with_distance.step_time
    if steps is None:
        steps = Parameter_with_distance.steps
    if gr_conv is None:
        gr_conv = Parameter_with_distance.gr_conv
    if cont_out_capacity is None:
        cont_out_capacity = 1
    if length_first is None:
        length_first = Parameter_with_distance.length_first
    if length_second is None:
        length_second = Parameter_with_distance.length_second
    if horizontal_spacing is None:
        horizontal_spacing = Parameter_with_distance.horizontal_spacing
    if vertical_spacing is None:
        vertical_spacing = Parameter_with_distance.vertical_spacing
    if first_speed is None:
        first_speed = Parameter_with_distance.first_speed
    if second_speed is None:
        second_speed = Parameter_with_distance.second_speed
    if dt is None:
        dt = Parameter_with_distance.dt
    if env_time is None:
        env_time = Parameter_with_distance.env_time
#--------------------------------------------------------------------
#--------------------------------------------------------------------
#--------------------------------------------------------------------
    p_buffer = Conveyor(env, "P_buffer", conveyor_speed=1, init_load=0, max_load=10)
    step_g = create_step_conveyor(env, "G_step", step_time=step_time, steps=steps, output_capacity=1)
    grenailleuse_exit_times = []
    first_conv_exit_times = []
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
    cont_out_1 = simpy.Store(env, capacity = 1)
    env.process(continuous_conveyor(
                env, 
                length = length_first,
                speed = first_speed, 
                dt = dt,
                input_store = step_g["output_store"],
                spacing = vertical_spacing,
                out_store = cont_out_1,
                exit_times = first_conv_exit_times
            )
        )
    
    cont_out_2 = simpy.Store(env, capacity = 1)
    #conveyor 2
    env.process(
        continuous_conveyor(
            env,
            length=length_second,
            speed=second_speed,
            dt=dt,
            input_store=cont_out_1,
            spacing=horizontal_spacing,
            out_store=cont_out_2,
            exit_times=second_conv_exit_times,
        )
    )

    inspect_buffer = simpy.Store(env, capacity=1)
    post_inspect = simpy.Store(env)

    pre_inspect_delay = t_dis2
    post_inspect_delay = t_dis
    env.process(unload_delay(env, cont_out_2, inspect_buffer, pre_inspect_delay))

    inspected_times = []
    busy_time = [0.0]
    env.process(
        inspector_process(
            env,
            inspector,
            inspect_buffer,
            inspect_time,
            inspected_times,
            busy_time,
            output_store=post_inspect,
        )
    )
    env.process(unload_delay(env, post_inspect, simpy.Store(env), post_inspect_delay))

    monitor = {
        "t": [],
        "cont_out_1": [],
        "cont_out_2": [],
        "inspect_buffer": [],
        "post_inspect": [],
        "inspector_busy": [],
    }

    def monitor_process():
        while True:
            monitor["t"].append(env.now)
            monitor["cont_out_1"].append(len(cont_out_1.items))
            monitor["cont_out_2"].append(len(cont_out_2.items))
            monitor["inspect_buffer"].append(len(inspect_buffer.items))
            monitor["post_inspect"].append(len(post_inspect.items))
            monitor["inspector_busy"].append(inspector.count)
            yield env.timeout(sample_time)

    env.process(monitor_process())

    env.run(env_time)
    idle_time = busy_time[0]
    print(f"Inspector busy time: {idle_time:.2f}s over {env.now:.2f}s total")

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
        "conveyor_exit_times_1": first_conv_exit_times,
        "conveyor_exit_times_2": second_conv_exit_times,
        "monitor": monitor,
        "busy_time": busy_time[0],
        "total_time": env.now,
    }

if __name__ == "__main__":
    demo_composite_flow()

import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from simpy_objects import Conveyor
import Parameter_horizontal
from functions import create_step_conveyor, arrival_process, _buffer_get, _buffer_has_space, _buffer_put, load_step_conveyor, robot_process, inspect_time, inspector_process, unload_delay, step_conveyor_advance, continuous_conveyor, continuous_conveyor_simple

def demo_composite_flow(
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
    plot=True,
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

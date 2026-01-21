import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from simpy_objects import Conveyor
import Parameter

def create_step_conveyor(env, conveyor_id, step_time, steps, output_capacity=1):
    if steps < 1:
        raise ValueError("steps must be >= 1")
    return {
        "env": env,
        "conveyor_id": conveyor_id,
        "step_time": step_time,
        "steps": steps,
        "slots": [None] * steps, #represents the conveyor positions, either it is empty or it contains the bottle id
        "space": simpy.Container(env, init=steps, capacity=steps), #total capacity on the conveyor, when init= steps then all are emoty 
        #space.get(1) which is blocked if the conveyor is full 
        #when the bottle exits at the end space.put(1) frees a slot
        "step_lock": simpy.Resource(env, capacity=1),
        #enforces only one step move at a time
        "output_store": simpy.Store(env, capacity=output_capacity),
        #acts as a buffer at the end of the conveyor
        "next_id": 0,
        #an id for the bottles (step conveyor increments this ans stores the id in slot)
    }
#the main problem with the arrival process is that there is a criteria that already considers whether there is a bottle that exists or not which is unrealistic 
#checking whether there is a bottle that is at arrival and then sampling from a distriution doesnt really make much sense unless we assume that there will always be T_P_arrival> (t1 at which step_conveyor[0]==1 - t2 at which step_conveyor[0] == 0) 
# otherwise we are not actually sampling from said distribution, otherwise if we have T_P< (t1 at which step_conveyor[0]==1 - t2 at which step_conveyor[0] == 0)  then we would need a buffer before
def arrival_process(
    env,
    p_buffer,
    mean_interval=12,
    down_time=0.05,
    min_inter=10,
    max_inter=30,
    arrival_times=None,
):
    while True:
        if p_buffer.container.level < p_buffer.container.capacity:
            p = random.random()
            t = (
                mean_interval
                if p < (1 - down_time)
                else mean_interval + random.uniform(min_inter, max_inter)
            )
            yield env.timeout(t)
            yield p_buffer.container.put(1)
            if arrival_times is not None:
                arrival_times.append(env.now)
        else:
            yield env.timeout(0.1)


def load_step_conveyor(env, p_buffer, step_conveyor):
    while True:
        yield p_buffer.container.get(1)
        placed = False
        while not placed:
            if step_conveyor["slots"][0] is None:
                with step_conveyor["step_lock"].request() as req:
                    yield req
                    yield step_conveyor["space"].get(1)
                    #checks twice incase there was a process that occured in between
                    if step_conveyor["slots"][0] is None:
                        step_conveyor["next_id"] += 1
                        step_conveyor["slots"][0] = step_conveyor["next_id"]
                        placed = True
            if not placed:
                yield env.timeout(0.05) #identical to the clock rate of the sensor 


def step_conveyor_advance(env, step_conveyor, gr_conv=12, exit_times=None):
    while True:
        any_items = any(slot is not None for slot in step_conveyor["slots"])
        output_full = len(step_conveyor["output_store"].items) >= step_conveyor["output_store"].capacity
        if not any_items or output_full:
            yield env.timeout(step_conveyor["step_time"])
            print(rf'any_items{any_items} and output full {output_full}')
            #retries until there is space on the output store
            continue
        with step_conveyor["step_lock"].request() as req:
            yield req
            yield env.timeout(step_conveyor["step_time"])
            exiting = step_conveyor["slots"][-1]
            for i in range(step_conveyor["steps"] - 1, 0, -1):
                step_conveyor["slots"][i] = step_conveyor["slots"][i - 1]
            print(step_conveyor["slots"])
            step_conveyor["slots"][0] = None
            if exiting is not None:
                yield step_conveyor["output_store"].put(exiting)
                if exit_times is not None:
                    exit_times.append(env.now)
                yield step_conveyor["space"].put(1) #frees up a space
                yield env.timeout(gr_conv)


def continuous_conveyor_simple(
    env,
    length,
    speed,
    dt,
    input_store,
    spacing,
    out_store,
    exit_times=None,
    position_logger=None,
    segment_id=None,
    segment_length=None,
):
    items = []
    while True:
        if input_store.items and (not items or items[0]["pos"] >= spacing):
            item = yield input_store.get()
            items.append({"id": item, "pos": 0.0})
        for item in items:
            item["pos"] += speed * dt
        pos_list = [float(np.round(item["pos"], 2)) for item in items]
        print(pos_list)
        exited = [item for item in items if item["pos"] >= length]
        items = [item for item in items if item["pos"] < length]
        for item in exited:
            yield out_store.put(item)
            if exit_times is not None:
                exit_times.append(env.now)

        if position_logger is not None:
            position_logger(env.now, segment_id, items, segment_length=segment_length)

        yield env.timeout(dt)


def continuous_conveyor(
    env,
    length,
    speed,
    dt,
    input_store,
    spacing,
    out_store,
    exit_times=None,
    position_logger=None,
    segment_id=None,
    segment_length=None,
):
    items = []
    while True:
        if input_store.items and (not items or items[0]["pos"] >= spacing):
            item = yield input_store.get()
            items.append({"id": item, "pos": 0.0})
        output_full = out_store.capacity is not None and len(out_store.items) >= out_store.capacity
        gap = 0.0 if output_full else spacing
        if items:
            items[0]["pos"] = items[0]["pos"] + speed * dt
            if output_full:
                items[0]["pos"] = min(items[0]["pos"], length)
            for i in range(1, len(items)):
                max_pos = items[i - 1]["pos"] - gap
                items[i]["pos"] = min(items[i]["pos"] + speed * dt, max_pos)
        pos_list = [float(np.round(item["pos"], 2)) for item in items]
        print(pos_list)
        remaining = []
        for item in items:
            if item["pos"] >= length:
                output_full = out_store.capacity is not None and len(out_store.items) >= out_store.capacity
                if output_full:
                    item["pos"] = length
                    remaining.append(item)
                    continue
                yield out_store.put(item)
                if exit_times is not None:
                    exit_times.append(env.now)
            else:
                remaining.append(item)
        items = remaining

        if position_logger is not None:
            position_logger(env.now, segment_id, items, segment_length=segment_length)

        yield env.timeout(dt)


def inspector_process(
    env, inspector, input_store, inspect_time_fn, inspected_times, busy_time, output_store=None
):
    while True:
        item = yield input_store.get()
        with inspector.request() as req:
            yield req
            start = env.now
            yield env.timeout(inspect_time_fn())
            end = env.now
            busy_time[0] += end - start
        if output_store is not None:
            yield output_store.put(item)
        print(f"t={env.now:>6.2f} inspected item {item['id']}")
        inspected_times.append(env.now)

def robot_process(
    env, robot, input_store, robot_time, moved_times, busy_time, output_store
):
    while True:
        item = yield input_store.get()
        with robot.request() as req:
            yield req
            start = env.now
            yield env.timeout(robot_time)
            end = env.now
            busy_time[0] += end - start
        if output_store is not None:
            yield output_store.put(item)
            yield env.timeout(robot_time)
        print(f"t={env.now:>6.2f} robotted item {item}")
        moved_times.append(env.now)

        
def unload_delay(env, input_store, output_store, delay_time):
        while True:
            item = yield input_store.get()
            yield env.timeout(delay_time)
            yield output_store.put(item)

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
    spacing=None,
    speed=None,
    dt=None,
    env_time=None,
    sample_time=1.0,
    plot=True,
):
    env = simpy.Environment()

    if mean_interval is None:
        mean_interval = Parameter.mean_interval
    if down_time is None:
        down_time = Parameter.down_time
    if min_inter is None:
        min_inter = Parameter.min_iter
    if max_inter is None:
        max_inter = Parameter.max_iter
    if t_dis is None:
        t_dis = Parameter.t_dis
    if t_dis2 is None:
        t_dis2 = Parameter.t_dis2
    if inspect_min is None:
        inspect_min = Parameter.inspect_min
    if inspect_max is None:
        inspect_max = Parameter.inspect_max
    if step_time is None:
        step_time = Parameter.step_time
    if steps is None:
        steps = Parameter.steps
    if gr_conv is None:
        gr_conv = Parameter.gr_conv
    if cont_out_capacity is None:
        cont_out_capacity = 1
    if length is None:
        length = Parameter.length
    if spacing is None:
        spacing = Parameter.spacing
    if speed is None:
        speed = Parameter.speed
    if dt is None:
        dt = Parameter.dt
    if env_time is None:
        env_time = Parameter.env_time

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
    env.process(step_conveyor_advance(env, step_g, gr_conv, grenailleuse_exit_times))

    def inspect_time():
        return random.uniform(inspect_min, inspect_max)
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
        "conveyor_exit_times": conveyor_exit_times,
        "monitor": monitor,
        "busy_time": busy_time[0],
        "total_time": env.now,
    }

if __name__ == "__main__":
    demo_composite_flow()

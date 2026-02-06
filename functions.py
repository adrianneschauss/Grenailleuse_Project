import random
import numpy as np
import simpy
import matplotlib.pyplot as plt
from simpy_objects import Conveyor
import Parameter_horizontal

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
    step_conveyor=None,
    mean_interval=12,
    down_time=0.05,
    min_inter=10,
    max_inter=30,
    arrival_times=None,
):
    while True:
        if _buffer_has_space(p_buffer):
            p = random.random()
            t = (
                mean_interval
                if p < (1 - down_time)
                else mean_interval + random.uniform(min_inter, max_inter)
            )
            yield env.timeout(t)
            yield _buffer_put(p_buffer)
            if arrival_times is not None:
                arrival_times.append(env.now)
        else:
            yield env.timeout(0.1)


def load_step_conveyor(env, p_buffer, step_conveyor):
    while True:
        yield _buffer_get(p_buffer)
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


def _buffer_has_space(p_buffer):
    if hasattr(p_buffer, "container"):
        return p_buffer.container.level < p_buffer.container.capacity
    capacity = getattr(p_buffer, "capacity", None)
    if capacity is None:
        return True
    return len(p_buffer.items) < capacity


def _buffer_put(p_buffer):
    if hasattr(p_buffer, "container"):
        return p_buffer.container.put(1)
    return p_buffer.put(1)


def _buffer_get(p_buffer):
    if hasattr(p_buffer, "container"):
        return p_buffer.container.get(1)
    return p_buffer.get()


def step_conveyor_advance(env, step_conveyor, gr_conv, exit_times=None, blocked_time=None):
    while True:
        any_items = any(slot is not None for slot in step_conveyor["slots"])
        output_full = len(step_conveyor["output_store"].items) >= step_conveyor["output_store"].capacity
        if not any_items or output_full:
            if output_full and blocked_time is not None:
                blocked_time[0] += step_conveyor["step_time"]
            yield env.timeout(step_conveyor["step_time"])
 #           print(rf'any_items{any_items} and output full {output_full}')
            #retries until there is space on the output store
            continue
        with step_conveyor["step_lock"].request() as req:
            yield req
            exiting = step_conveyor["slots"][-1]
            for i in range(step_conveyor["steps"] - 1, 0, -1):
                step_conveyor["slots"][i] = step_conveyor["slots"][i - 1]
            
            step_conveyor["slots"][0] = None
            if exiting is not None:
                yield step_conveyor["output_store"].put(exiting)
                
                if exit_times is not None:
                    exit_times.append(env.now)
                yield step_conveyor["space"].put(1) #frees up a space
                yield env.timeout(gr_conv)
        yield env.timeout(step_conveyor["step_time"])


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
       
        exited = [item for item in items if item["pos"] >= length]
        items = [item for item in items if item["pos"] < length]
        for item in exited:
            yield out_store.put(item)
            if exit_times is not None:
                exit_times.append(env.now)

        if position_logger is not None:
            try:
                position_logger(
                    env.now,
                    segment_id,
                    items,
                    segment_length=segment_length,
                    step_mode=step_mode,
                    det1=det1,
                    det2=det2,
                    det3=det3,
                    det4=det4,
                )
            except TypeError:
                position_logger(env.now, segment_id, items, segment_length=segment_length)

        yield env.timeout(dt)


def variable_conveyor(
    env,
    length,
    speed,
    dt,
    input_store,
    spacing,
    out_store,
    inspect_buffer,
    inspector,
    discharge_time=0.0,
    exit_times=None,
    position_logger=None,
    segment_id=None,
    segment_length=None,
    mode_switch_delay=0.0,
):
    items = []
    step_interval = spacing / speed if speed > 0 else dt
    step_acc = 0.0
    last_mode = None
    det3_state = 0
    last_mode_change_time = 0.0

    while True:
        det4 = 1 if len(input_store.items) > 0 else 0
        det2 = 1 if len(inspect_buffer.items) > 0 else 0
        det1 = 1 if inspector.count > 0 else 0

        desired_step_mode = not (det1 == 0) or not (det2 == 0) or (det2 == 1 or det3_state == 1 or det1 == 1)
        step_mode = desired_step_mode
        if last_mode is True and desired_step_mode is False:
            if env.now - last_mode_change_time < mode_switch_delay:
                step_mode = True
        if last_mode is None or last_mode != step_mode:
            step_acc = 0.0
            last_mode = step_mode
            last_mode_change_time = env.now

        if input_store.items and (not items or items[0]["pos"] >= spacing):
            item = yield input_store.get()
            if discharge_time > 0:
                yield env.timeout(discharge_time)
            items.append({"id": item, "pos": 0.0})

        if step_mode:
            step_acc += dt
            if step_acc >= step_interval:
                step_acc -= step_interval
                for item in items:
                    item["pos"] += spacing
                    if item["pos"] > length:
                        item["pos"] = length
        else:
            for item in items:
                item["pos"] += speed * dt

        end_sensor = 1 if any(item["pos"] >= length - 1e-6 for item in items) else 0
        det3_state = end_sensor
        pos_list = [float(np.round(item["pos"], 2)) for item in items]
  #      print(pos_list, {"det1": det1, "det2": det2, "det3": end_sensor, "det4": det4})

        exited = [item for item in items if item["pos"] >= length]
        items = [item for item in items if item["pos"] < length]
        for item in exited:
            yield out_store.put(item)
            yield env.timeout(30)
            if exit_times is not None:
                exit_times.append(env.now)

        if position_logger is not None:
            try:
                position_logger(
                    env.now,
                    segment_id,
                    items,
                    segment_length=segment_length,
                    step_mode=step_mode,
                    det1=det1,
                    det2=det2,
                    det3=end_sensor,
                    det4=det4,
                )
            except TypeError:
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
    max_items = int(length // spacing)
    while True:
        if (
            input_store.items
            and (not items or items[0]["pos"] >= spacing)
            and len(items) < max_items
        ):
            item = yield input_store.get()
            items.append({"id": item, "pos": 0.0})
        output_full = out_store.capacity is not None and len(out_store.items) >= out_store.capacity
        gap = spacing
        if items:
            items[0]["pos"] = items[0]["pos"] + speed * dt
            if output_full:
                items[0]["pos"] = min(items[0]["pos"], length)
            items[0]["pos"] = max(0.0, items[0]["pos"])
            for i in range(1, len(items)):
                max_pos = items[i - 1]["pos"] - gap
                items[i]["pos"] = min(items[i]["pos"] + speed * dt, max_pos)
                if items[i]["pos"] < 0.0:
                    items[i]["pos"] = 0.0
        pos_list = [float(np.round(item["pos"], 2)) for item in items]
 
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
    env, inspector, input_store, inspect_time, inspected_times, busy_time, output_store=None
):
    while True:
        item = yield input_store.get()
        with inspector.request() as req:
            yield req
            start = env.now
            yield env.timeout(inspect_time())
            end = env.now
            busy_time[0] += end - start
        if output_store is not None:
            yield output_store.put(item)
 #       print(f"t={env.now:>6.2f} inspected item {item['id']}")
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
 #       print(f"t={env.now:>6.2f} robotted item {item}")
        moved_times.append(env.now)

        
def unload_delay(env, input_store, output_store, delay_time):
        while True:
            item = yield input_store.get()
            yield env.timeout(delay_time)
            yield output_store.put(item)
            
def inspect_time(inspect_min, inspect_max, s, max_long, min_long):
    p = random.random()
    if p> s:
        x= random.uniform(inspect_min, inspect_max)
    else: 
        x = random.uniform(min_long, max_long)
    return x

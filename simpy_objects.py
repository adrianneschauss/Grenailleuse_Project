import numpy as np
import simpy
from monitoring import monitor, patch_resource
from functools import partial, wraps

class Conveyor:
    def __init__(self, env, conveyor_id, conveyor_speed, init_load, max_load):
        self.env = env
        self.conveyor_id = conveyor_id
        self.conveyor_speed = conveyor_speed
        self.container = simpy.Container(env, init=init_load, capacity=max_load)

    def load(self, amount):
        """block until space exists"""
        travel_time = amount / self.conveyor_speed
        yield self.env.timeout(travel_time)                      # FIX: self.env
        put_event = self.container.put(amount)
        yield put_event
        return
from __future__ import annotations

import contextlib
import random
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

import numpy as np
from simpy import core
from tqdm import tqdm

# from .factories import state_factory, time_model_factory

if TYPE_CHECKING:
    from prodsim import request


VERBOSE = 1

@contextlib.contextmanager
def temp_seed(seed):
    np_state = np.random.get_state()
    p_state = random.getstate()
    np.random.seed(seed)
    random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(np_state)
        random.setstate(p_state)

@dataclass
class Environment(core.Environment):
    seed: int = 21
    pbar: Any = None
    last_update: int = field(init=False, default=0)

    def __init__(self, seed) -> None:
        super().__init__()
        self.seed: int = seed

    def run(self, time_range:int):
        with temp_seed(self.seed):
            if VERBOSE == 1:
                self.pbar = tqdm(total=time_range)

            self.run(time_range)
            if VERBOSE == 1:
                self.pbar.update(time_range - self.last_update)
                self.pbar.refresh()

    def request_process_of_resource(self, request: request.Request) -> None:
        if VERBOSE == 1:
            now = round(self.now)
            if now > self.last_update:
                self.pbar.update(now - self.last_update)
                self.last_update = now
        _controller = request.get_resource().get_controller()
        # self.process(_controller.request(request))
        _controller.request(request)

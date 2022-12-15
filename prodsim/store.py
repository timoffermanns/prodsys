from __future__ import annotations


from pydantic import BaseModel

from simpy.resources import store

from .data_structures import queue_data

from . import sim


class Queue(BaseModel, store.FilterStore):
    env: sim.Environment
    queue_data: queue_data.QueueData

    class Config:
        arbitrary_types_allowed = True

    def post_init(self):
        super().__init__(env=self.env, capacity=self.queue_data.capacity)



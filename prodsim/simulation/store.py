from __future__ import annotations


from simpy.resources import store

from prodsim.data_structures import queue_data

from prodsim.simulation import sim


class Queue(store.FilterStore):
    def __init__(self, env: sim.Environment, queue_data: queue_data.QueueData):
        self.env: sim.Environment = env
        self.queue_data: queue_data.QueueData = queue_data
        if queue_data.capacity == 0:
            capacity = float("inf")
        else:
            capacity = queue_data.capacity
        self._pending_put: int = 0
        super().__init__(env, capacity)

    def full(self) -> bool:
        return (self.capacity - self._pending_put - len(self.items)) <= 0
    
    def reserve(self) -> None:
        self._pending_put += 1
        if self._pending_put + len(self.items) > self.capacity:
            raise RuntimeError("Queue is full")
    
    def unreseve(self) -> None:
        self._pending_put -= 1





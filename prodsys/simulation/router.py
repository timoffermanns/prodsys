from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional
import numpy as np

from prodsys.simulation import process
from prodsys.simulation import resources


if TYPE_CHECKING:
    from prodsys.simulation import resources, process, product, sink
    from prodsys.factories import resource_factory, sink_factory
    from prodsys.util import gym_env


class Router:
    def __init__(
        self,
        resource_factory: resource_factory.ResourceFactory,
        sink_factory: sink_factory.SinkFactory,
        routing_heuristic: Callable[..., resources.Resource],
    ):
        self.resource_factory: resource_factory.ResourceFactory = resource_factory
        self.sink_factory: sink_factory.SinkFactory = sink_factory
        self.routing_heuristic: Callable[..., product.Location] = routing_heuristic

    @abstractmethod
    def get_next_resource(self, __process: process.Process) -> Optional[resources.Resource]:
        pass

    def get_sink(self, _product_type: str) -> sink.Sink:
        possible_sinks = self.sink_factory.get_sinks_with_product_type(_product_type)
        chosen_sink = self.routing_heuristic(possible_sinks)
        return chosen_sink  # type: ignore False
    
    def get_possible_resources(self, target_process: process.Process) -> List[resources.Resource]:
        possible_resources = self.resource_factory.get_resources_with_process(target_process)
        return possible_resources


class SimpleRouter(Router):
    def get_next_resource(self, target_process: process.Process) -> Optional[resources.Resource]:
        possible_resources = self.resource_factory.get_resources_with_process(target_process)
        left_resources = [resource for resource in possible_resources]

        for resource in possible_resources:
            if isinstance(resource, resources.ProductionResource):
                for input_queue in resource.input_queues:
                    if input_queue.full():  
                        left_resources = [r for r in left_resources if not r.data.ID==resource.data.ID]
                        break
        if not left_resources:
            return None
        return self.routing_heuristic(left_resources)


def get_resource_capabilities(resource: resources.Resource) -> List[str]:
    capabilities = []
    for resource_process in resource.processes:
        if isinstance(resource_process, process.CapabilityProcess):
            capabilities.append(resource_process.process_data.capability)
        
    return capabilities


class CapabilityRouter(Router):
    def get_next_resource_per_ID(self, target_process: process.Process) -> resources.Resource:
        possible_resources = self.resource_factory.get_resources_with_process(
            target_process
        )
        return self.routing_heuristic(possible_resources)

    def get_next_resource(self, target_process: process.Process) -> Optional[resources.Resource]:
        if isinstance(target_process, process.TransportProcess):
            return self.get_next_resource_per_ID(target_process)
        elif not isinstance(target_process, process.CapabilityProcess):
            raise ValueError(
                "CapabilityRouter can only be used with CapabilityProcess or TransportProcess"
            )
        possible_resources = []
        for resource in self.resource_factory.resources:
            resource_capabilities = get_resource_capabilities(resource)

            if (target_process.process_data.capability in resource_capabilities) and not any(q.full() for q in resource.input_queues):
                possible_resources.append(resource)
        if not possible_resources:
            return None
        return self.routing_heuristic(possible_resources)

def FIFO_routing_heuristic(possible_resources: List[resources.Resource]) -> resources.Resource:
    return possible_resources.pop(0)


def random_routing_heuristic(possible_resources: List[resources.Resource]) -> resources.Resource:
    possible_resources.sort(key=lambda x: x.data.ID)
    return np.random.choice(possible_resources)  # type: ignore


def shortest_queue_routing_heuristic(
    possible_resources: List[resources.Resource],
) -> resources.Resource:
    queue_list = []
    for resource in possible_resources:
        if not isinstance(resource, resources.ProductionResource):
            continue
        if resource.input_queues:
            for q in resource.input_queues:
                queue_list.append((q, resource))
    if queue_list:
        queue_list.sort(key=lambda x: len(x[0].items))
        min_length = len(queue_list[0][0].items)
        resource_list = [
            queue[1] for queue in queue_list if len(queue[0].items) <= min_length
        ]
        return np.random.choice(resource_list)
    return random_routing_heuristic(possible_resources=possible_resources)

def agent_routing_heuristic(gym_env: gym_env.ProductionRoutingEnv, possible_resources: List[resources.Resource]
                            ) -> resources.Resource:
    gym_env.load_possible_resources(possible_resources)
    gym_env.interrupt_simulation_event.succeed()
    return gym_env.get_chosen_resource()

    


ROUTING_HEURISTIC = {
    "shortest_queue": shortest_queue_routing_heuristic,
    "random": random_routing_heuristic,
    "FIFO": FIFO_routing_heuristic,
}

ROUTERS = {
    "SimpleRouter": SimpleRouter,
    "CapabilityRouter": CapabilityRouter,
}

from __future__ import annotations

import copy
from typing import Dict, List, Optional, Union, Tuple, TYPE_CHECKING

from pydantic import BaseModel, parse_obj_as

from prodsim import sim
from prodsim.util.util import get_class_from_str


from prodsim.data_structures.resource_data import (
    RESOURCE_DATA_UNION,
    ProductionResourceData,
)
from prodsim.factories import process_factory, state_factory, queue_factory

from prodsim import control, resources, process

if TYPE_CHECKING:
    from prodsim import state, store, adapter


CONTROLLER_DICT: Dict = {
    "SimpleController": control.ProductionController,
    "TransportController": control.TransportController,
}

CONTROL_POLICY_DICT: Dict = {
    "FIFO": control.FIFO_control_policy,
    "LIFO": control.LIFO_control_policy,
    "SPT": control.SPT_control_policy,
    "SPT_transport": control.SPT_transport_control_policy,
}


def register_states(
    resource: resources.Resourcex,
    states: List[state.STATE_UNION],
    _env: sim.Environment,
):
    for actual_state in states:
        copy_state = copy.deepcopy(actual_state)
        copy_state.env = _env
        resource.add_state(copy_state)


def register_production_states(
    resource: resources.Resourcex,
    states: List[state.ProductionState],
    _env: sim.Environment,
):
    for actual_state in states:
        copy_state = copy.deepcopy(actual_state)
        copy_state.env = _env
        resource.add_production_state(copy_state)


def register_production_states_for_processes(
    resource: resources.Resourcex,
    state_factory: state_factory.StateFactory,
    _env: sim.Environment,
):
    states: List[state.State] = []
    for process_instance in resource.processes:
        values = {
            "new_state": {
                "ID": process_instance.process_data.ID,
                "description": process_instance.process_data.description,
                "time_model_id": process_instance.process_data.time_model_id,
            }
        }
        if isinstance(process_instance, process.ProductionProcess):
            state_factory.create_states_from_configuration_data({"ProductionState": values})
        elif isinstance(process_instance, process.TransportProcess):
            state_factory.create_states_from_configuration_data({"TransportState": values})
        _state = state_factory.get_states(IDs=[process_instance.process_data.ID]).pop()
        states.append(_state)
    register_production_states(resource, states, _env)  # type: ignore


class ResourceFactory(BaseModel):
    env: sim.Environment
    process_factory: process_factory.ProcessFactory
    state_factory: state_factory.StateFactory
    queue_factory: queue_factory.QueueFactory

    resource_data: List[RESOURCE_DATA_UNION] = []
    resources: List[resources.RESOURCE_UNION] = []
    controllers: List[
        Union[control.ProductionController, control.TransportController]
    ] = []

    class Config:
        arbitrary_types_allowed = True

    def create_resources(self, adapter: adapter.Adapter):
        for resource_data in adapter.resource_data:
            self.add_resource(resource_data)

    def adjust_process_capacities(self, resource_data: RESOURCE_DATA_UNION):
        if resource_data.process_capacity:
            for process, capacity in zip(
                resource_data.processes, resource_data.process_capacity
            ):
                resource_data.processes += [process] * (capacity - 1)

    def get_queues_for_resource(
        self, resource_data: ProductionResourceData
    ) -> Tuple[List[store.Queue], List[store.Queue]]:
        input_queues = []
        output_queues = []
        if resource_data.input_queues:
            input_queues = self.queue_factory.get_queues(resource_data.input_queues)
        else:
            raise ValueError("No input queues for resource" + resource_data.ID)
        if resource_data.output_queues:
            output_queues = self.queue_factory.get_queues(resource_data.output_queues)
        else:
            raise ValueError("No output queues for resource" + resource_data.ID)

        return input_queues, output_queues

    def add_resource(self, resource_data: RESOURCE_DATA_UNION):
        values = {"env": self.env, "data": resource_data}
        processes = self.process_factory.get_processes_in_order(resource_data.processes)

        ids = [proc.process_data.ID for proc in processes]
        values.update({"processes": processes})

        self.adjust_process_capacities(resource_data)

        controller_class = get_class_from_str(
            name=resource_data.controller, cls_dict=CONTROLLER_DICT
        )
        control_policy = get_class_from_str(
            name=resource_data.control_policy, cls_dict=CONTROL_POLICY_DICT
        )
        controller: Union[
            control.ProductionController, control.TransportController
        ] = controller_class(control_policy=control_policy, env=self.env)
        self.controllers.append(controller)
        values.update({"controller": controller})

        if isinstance(resource_data, ProductionResourceData):
            input_queues, output_queues = self.get_queues_for_resource(resource_data)
            values.update(
                {"input_queues": input_queues, "output_queues": output_queues}
            )
        resource_object = parse_obj_as(resources.RESOURCE_UNION, values)
        # print(resource_object._env)
        controller.set_resource(resource_object)

        states = self.state_factory.get_states(resource_data.states)
        register_states(resource_object, states, self.env)
        register_production_states_for_processes(
            resource_object, self.state_factory, self.env
        )
        self.resources.append(resource_object)

    def start_resources(self):
        for _resource in self.resources:
            _resource.start_states()

        for controller in self.controllers:
            self.env.process(controller.control_loop())  # type: ignore

    def get_resource(self, ID):
        return [r for r in self.resources if r.data.ID == ID].pop()

    def get_controller_of_resource(
        self, _resource: resources.Resourcex
    ) -> Optional[Union[control.ProductionController, control.TransportController]]:
        for controller in self.controllers:
            if controller.resource == _resource:
                return controller

    def get_resources(self, IDs: List[str]) -> List[resources.Resourcex]:
        return [r for r in self.resources if r.data.ID in IDs]

    def get_resources_with_process(
        self, target_process: process.Process
    ) -> List[resources.Resourcex]:
        return [
            res
            for res in self.resources
            if target_process.process_data.ID in res.data.processes
        ]
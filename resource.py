from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

import simpy
import env
import base
from process import Process, ProcessFactory
import state
import copy


@dataclass
class Resource(ABC, simpy.Resource, base.IDEntity):
    env: env.Environment
    processes: List[Process]
    capacity: int = field(default=1)
    parts_made: int = field(default=0, init=False)
    req: simpy.Event = field(default=None, init=False)
    available: simpy.Event = field(default=None, init=False)
    states: List[state.State] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.req = simpy.Event(self.env)
        self.available = simpy.Event(self.env)

    @abstractmethod
    def change_state(self, input_state: state.State) -> None:
        pass

    def add_state(self, input_state: state.State) -> None:
        self.states.append(input_state)
        input_state.resource = self

    @abstractmethod
    def process_states(self) -> None:
        pass

    @abstractmethod
    def reactivate(self, input_state: state.State):
        pass

    @abstractmethod
    def interrupt_state(self):
        pass

    def get_active_states(self) -> List[state.State]:
        return self.states

    def request_repair(self):
        pass


class ConcreteResource(Resource):

    def __post_init__(self):
        self.req = simpy.Event(self.env)
        self.available = simpy.Event(self.env)

    def change_state(self, input_state: state.State) -> None:
        pass

    def add_state(self, input_state: state.State) -> None:
        self.states.append(input_state)
        input_state.resource = self

    def process_states(self) -> None:
        for state in self.states:
            process = self.env.process(state.process_state())
            state.process = process

    def reactivate(self):
        for state in self.states:
            state.activate()

    def interrupt_state(self):
        for actual_state in self.states:
            if type(actual_state) == state.ProductionState:
                print("start interrupt at state", actual_state.description)
                self.env.process(actual_state.interrupt_process())
                # actual_state.interrupt_process()

    def get_active_states(self) -> List[state.State]:
        pass

    def request_repair(self):
        pass


def register_states(resource: Resource, states: List[state.State], env: env.Environment):
    for actual_state in states:
        copy_state = copy.deepcopy(actual_state)
        copy_state.env = env
        resource.add_state(copy_state)


def register_production_states_for_processes(resource: Resource, state_factory: state.StateFactory, env: env.Environment):
    states: List[state.State] = []
    for process in resource.processes:
        values = {'ID': process.ID, 'description': process.description, 'time_model_id': process.time_model.ID}
        state_factory.add_states(cls=state.ProductionState, values=values)
        states.append(state_factory.get_states(IDs=[values['ID']]).pop())
    register_states(resource, states, env)


@dataclass
class ResourceFactory:
    data: dict
    env: env.Environment
    process_factory: ProcessFactory
    state_factory: state.StateFactory

    resources: List[Resource] = field(default_factory=list, init=False)

    def create_resources(self):
        resources = self.data['resources']
        for values in resources.values():
            print(values['description'], "____________")
            self.add_resource(values)

    def add_resource(self, values: dict):
        print("Resource values: ", values)
        states = self.state_factory.get_states(values['states'])
        print("Resource states: ",  [state.description for state in states])
        processes = self.process_factory.get_processes(values['processes'])
        print("Resource processes: ", processes)
        resource = ConcreteResource(ID=values['ID'],
                             description=values['description'],
                             env=self.env,
                             capacity=2,
                             processes=processes,
                             )
        register_states(resource, states, self.env)
        register_production_states_for_processes(resource, self.state_factory, self.env)
        self.resources.append(resource)

    def get_resource(self, ID):
        return [st for st in self.resources if st.ID == ID].pop()

    def get_resources(self, IDs: List[str]) -> List[Resource]:
        return [r for r in self.resources if r.ID in IDs]


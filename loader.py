from __future__ import annotations
import time

import simpy
from dataclasses import dataclass, field
from typing import List, Literal, Tuple, Union
from abc import ABC, abstractmethod
import logging
import json


def load_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    logging.info("data loaded")
    return data


@dataclass
class Loader(ABC):
    seed: int = field(init=False, default=0)
    time_model_data: dict = field(init=False, default_factory=dict)
    state_data: dict = field(init=False, default_factory=dict)
    process_data: dict = field(init=False, default_factory=dict)
    resource_data: dict = field(init=False, default_factory=dict)
    queue_data: dict = field(init=False, default_factory=dict)
    source_data: dict = field(init=False, default_factory=dict)
    sink_data: dict = field(init=False, default_factory=dict)
    material_data: dict = field(init=False, default_factory=dict)

    valid_configuration: bool = field(init=False, default=False)

    @abstractmethod
    def read_data(self, file_path: str):
        pass

    def get_num_machines(self) -> int:
        i = 0
        for resource in self.resource_data.values():
            if 'input_queues' in resource.keys():
                i += 1

        return i
    
    def get_num_transport_resources(self) -> int:
        return len(self.resource_data.keys()) - self.get_num_machines()

    def get_num_process_modules(self) -> dict:
        num_process_modules_dict = {}
        for resource in self.resource_data.values():
            if 'input_queues' in resource.keys():
                for process_module in resource['processes']: 
                    if not process_module in num_process_modules_dict.keys():
                        num_process_modules_dict[process_module] = 0
                    num_process_modules_dict[process_module] += 1
        return num_process_modules_dict

    def get_processes(self) -> list:
        return [process['ID'] for process in self.process_data['ProductionProcesses'].values()]


@dataclass
class JsonLoader(Loader):
    def read_data(self, file_path: str):
        data = load_json(file_path=file_path)
        self.seed = data["seed"]
        self.time_model_data = data["time_models"]
        self.state_data = data["states"]
        self.process_data = data["processes"]
        self.queue_data = data["queues"]
        self.resource_data = data["resources"]
        self.material_data = data["materials"]
        self.sink_data = data["sinks"]
        self.source_data = data["sources"]


@dataclass
class CustomLoader(Loader):
    def read_data(self, file_path: str, type: Literal["json", "xml"] = "json"):
        if type == "json":
            data = load_json(file_path=file_path)
        elif type == "xml":
            pass

        if "seed" in data:
            self.seed = data["seed"]
        if "time_models" in data:
            self.time_model_data = data["time_models"]
        if "states" in data:
            self.state_data = data["states"]
        if "processes" in data:
            self.process_data = data["processes"]
        if "queues" in data:
            self.queue_data = data["queues"]
        if "resources" in data:
            self.resource_data = data["resources"]
        if "materials" in data:
            self.material_data = data["materials"]
        if "sinks" in data:
            self.sink_data = data["sinks"]
        if "sources" in data:
            self.source_data = data["sources"]

    def set_seed(self, seed: int):
        self.seed = seed

    def add_entry_to_data(self, data, entry, label):
        length = len(data) + 1
        data.update({f"{label}_{length}": entry})

    def add_typed_entry_to_data(self, data, entry, type):
        if type not in data:
            length = 1
            data[type] = {}
        else:
            length = len(data[type]) + 1
        data[type].update({f"{type}_{length}": entry})

    def add_time_model(
        self,
        type: str,
        ID: str,
        description: str,
        parameters: List[float] = None,
        batch_size: int = None,
        distribution_function: str = None,
        history: List[float] = None,
        speed: float = None,
        reaction_time: float = None,
    ):
        time_model_data = {"ID": ID, "description": description}
        if type == "FunctionTimeModels":
            time_model_data.update(
                {
                    "parameters": parameters,
                    "batch_size": batch_size,
                    "distribution_function": distribution_function,
                }
            )
        elif type == "HistoryTimeModels":
            time_model_data.update({"history": history})
        elif type == "ManhattanDistanceTimeModel":
            time_model_data.update({"speed": speed, "reaction_time": reaction_time})
        self.add_typed_entry_to_data(
            data=self.time_model_data, entry=time_model_data, type=type
        )

    def add_state(self, type: str, ID: str, description: str, time_model_ID: str):
        state_data = {
            "ID": ID,
            "description": description,
            "time_model_id": time_model_ID,
        }
        self.add_typed_entry_to_data(data=self.state_data, entry=state_data, type=type)

    def add_process(self, type: str, ID: str, description: str, time_model_ID: str):
        process_data = {
            "ID": ID,
            "description": description,
            "time_model_id": time_model_ID,
        }
        self.add_typed_entry_to_data(
            data=self.process_data, entry=process_data, type=type
        )

    def add_queue(self, ID: str, description: str, capacity: int = None):
        queue_data = {"ID": ID, "description": description, "capacity": capacity}
        self.add_entry_to_data(self.queue_data, queue_data, label="Queue")

    def add_material(
        self,
        ID: str,
        description: str,
        processes: Union[List[str], str],
        transport_process: str,
    ):
        material_data = {
            "ID": ID,
            "description": description,
            "processes": processes,
            "transport_process": transport_process,
        }
        self.add_entry_to_data(self.material_data, material_data, label="Material")

    def add_resource(
        self,
        ID: str,
        description: str,
        controller: str,
        control_policy: str,
        location: List[int],
        capacity: int,
        processes: List[str],
        states: List[str],
        input_queues: List[str] = None,
        output_queues: List[str] = None,
    ):
        resource_data = {
            "ID": ID,
            "description": description,
            "controller": controller,
            "control_policy": control_policy,
            "location": location,
            "capacity": capacity,
            "processes": processes,
            "states": states,
        }
        if input_queues:
            resource_data.update({"input_queues": input_queues})
        if output_queues:
            resource_data.update({"output_queues": output_queues})
        self.add_entry_to_data(self.resource_data, resource_data, label="Resource")

    def add_resource_with_default_queue(
        self,
        ID: str,
        description: str,
        controller: str,
        control_policy: str,
        location: List[int],
        capacity: int,
        processes: List[str],
        states: List[str],
        queue_capacity: int,
    ):
        resource_data = {
            "ID": ID,
            "description": description,
            "controller": controller,
            "control_policy": control_policy,
            "location": location,
            "capacity": capacity,
            "processes": processes,
            "states": states,
            "input_queues": ["IQ" + ID],
            "output_queues": ["OQ" + ID],
        }
        self.add_queue(
            ID="IQ" + ID, description="Input queue of" + ID, capacity=queue_capacity
        )
        self.add_queue(
            ID="OQ" + ID, description="Output queue of" + ID, capacity=queue_capacity
        )
        self.add_entry_to_data(self.resource_data, resource_data, label="Resource")

    def add_source(
        self,
        ID: str,
        description: str,
        location: List[int],
        time_model_id: str,
        material_type: str,
        router: str,
        routing_heuristic: str,
        output_queues: List[str],
    ):
        source_data = {
            "ID": ID,
            "description": description,
            "location": location,
            "time_model_id": time_model_id,
            "material_type": material_type,
            "router": router,
            "routing_heuristic": routing_heuristic,
            "output_queues": output_queues,
        }
        self.add_entry_to_data(self.source_data, source_data, label="Source")

    def add_sink(
        self,
        ID: str,
        description: str,
        location: List[int],
        material_type: str,
        input_queues: List[str],
    ):
        sink_data = {
            "ID": ID,
            "description": description,
            "location": location,
            "material_type": material_type,
            "input_queues": input_queues,
        }
        self.add_entry_to_data(self.sink_data, sink_data, label="Sink")

    def to_json(self, file_path) -> None:
        save_dict = {}
        save_dict.update({"seed": self.seed})
        save_dict.update({"time_models": self.time_model_data})
        save_dict.update({"states": self.state_data})
        save_dict.update({"processes": self.process_data})
        save_dict.update({"queues": self.queue_data})
        save_dict.update({"resources": self.resource_data})
        save_dict.update({"materials": self.material_data})
        save_dict.update({"sinks": self.sink_data})
        save_dict.update({"sources": self.source_data})

        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(save_dict, json_file)

        logging.info(f"saved data to {file_path}")

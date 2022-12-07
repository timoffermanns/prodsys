from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from pydantic import parse_obj_as, BaseModel, Field

from . import time_model
from . import state
# from . import state


def load_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data



class Adapter(ABC, BaseModel):

    valid_configuration: bool = True
    reconfiguration_cost: float = 0

    time_model_data: List[time_model.TIME_MODEL_DATA] = []
    state_data: List[state.STATE_DATA_UNION] = []
    seed: int = 21


    @abstractmethod
    def read_data(self, file_path: str):
        pass

    @abstractmethod
    def write_data(self, file_path: str):
        pass



class JsonAdapter(Adapter):

    def read_data(self, file_path: str):
        data = load_json(file_path=file_path)
        self.create_time_model_data_object_from_configuration_data(data["time_models"])
        self.create_state_data_object_from_configuration_data(data["states"])


    def create_time_model_data_object_from_configuration_data(self, configuration_data: dict):
        for cls_name, items in configuration_data.items():
            for values in items.values():
                values.update({"type": cls_name})
                self.time_model_data.append(parse_obj_as(time_model.TIME_MODEL_DATA, values))


    def create_state_data_object_from_configuration_data(self, configuration_data: dict):
        for cls_name, items in configuration_data.items():
            for values in items.values():
                values.update({"type": cls_name})
                self.state_data.append(parse_obj_as(state.STATE_DATA_UNION, values))

    def write_data(self, file_path: str):
        pass



# @dataclass
# class CustomLoader(Adapter):
#     def read_data(self, file_path: str, type: Literal["json", "xml"] = "json"):
#         if type == "json":
#             data = load_json(file_path=file_path)
#         elif type == "xml":
#             pass

#         if "seed" in data:
#             self.seed = data["seed"]
#         if "time_models" in data:
#             self.time_model_data = data["time_models"]
#         if "states" in data:
#             self.state_data = data["states"]
#         if "processes" in data:
#             self.process_data = data["processes"]
#         if "queues" in data:
#             self.queue_data = data["queues"]
#         if "resources" in data:
#             self.resource_data = data["resources"]
#         if "materials" in data:
#             self.material_data = data["materials"]
#         if "sinks" in data:
#             self.sink_data = data["sinks"]
#         if "sources" in data:
#             self.source_data = data["sources"]

#     def set_seed(self, seed: int):
#         self.seed = seed

#     def add_entry_to_data_with_lowest_possible_index(self, data, entry, label):
#         counter = 1
#         while True:
#             key_string = f"{label}_{counter}"
#             if not key_string in data.keys():
#                 data.update({key_string: entry})
#                 break
#             counter += 1

#     def add_entry_to_data(self, data, entry, label):
#         length = len(data) + 1
#         key_string = f"{label}_{length}"
#         if not key_string in data.keys():
#             data.update({key_string: entry})
#         else: 
#             self.add_entry_to_data_with_lowest_possible_index(data, entry, label)

#     def add_typed_entry_to_data(self, data, entry, type):
#         if type not in data:
#             length = 1
#             data[type] = {}
#         else:
#             length = len(data[type]) + 1
#         data[type].update({f"{type}_{length}": entry})

#     def add_time_model(
#         self,
#         type: str,
#         ID: str,
#         description: str,
#         parameters: List[float] = None,
#         batch_size: int = None,
#         distribution_function: str = None,
#         history: List[float] = None,
#         speed: float = None,
#         reaction_time: float = None,
#     ):
#         time_model_data = {"ID": ID, "description": description}
#         if type == "FunctionTimeModels":
#             time_model_data.update(
#                 {
#                     "parameters": parameters,
#                     "batch_size": batch_size,
#                     "distribution_function": distribution_function,
#                 }
#             )
#         elif type == "HistoryTimeModels":
#             time_model_data.update({"history": history})
#         elif type == "ManhattanDistanceTimeModel":
#             time_model_data.update({"speed": speed, "reaction_time": reaction_time})
#         self.add_typed_entry_to_data(
#             data=self.time_model_data, entry=time_model_data, type=type
#         )

#     def add_state(self, type: str, ID: str, description: str, time_model_ID: str):
#         state_data = {
#             "ID": ID,
#             "description": description,
#             "time_model_id": time_model_ID,
#         }
#         self.add_typed_entry_to_data(data=self.state_data, entry=state_data, type=type)

#     def add_process(self, type: str, ID: str, description: str, time_model_ID: str):
#         process_data = {
#             "ID": ID,
#             "description": description,
#             "time_model_id": time_model_ID,
#         }
#         self.add_typed_entry_to_data(
#             data=self.process_data, entry=process_data, type=type
#         )

#     def add_queue(self, ID: str, description: str, capacity: int = None):
#         queue_data = {"ID": ID, "description": description, "capacity": capacity}
#         self.add_entry_to_data(self.queue_data, queue_data, label="Queue")

#     def add_material(
#         self,
#         ID: str,
#         description: str,
#         processes: Union[List[str], str],
#         transport_process: str,
#     ):
#         material_data = {
#             "ID": ID,
#             "description": description,
#             "processes": processes,
#             "transport_process": transport_process,
#         }
#         self.add_entry_to_data(self.material_data, material_data, label="Material")

#     def add_resource(
#         self,
#         ID: str,
#         description: str,
#         controller: str,
#         control_policy: str,
#         location: List[int],
#         capacity: int,
#         processes: List[str],
#         states: List[str],
#         input_queues: List[str] = None,
#         output_queues: List[str] = None,
#     ):           
#         resource_data = {
#             "ID": ID,
#             "description": description,
#             "controller": controller,
#             "control_policy": control_policy,
#             "location": location,
#             "capacity": capacity,
#             "processes": processes,
#             "states": states,
#         }
#         if input_queues:
#             resource_data.update({"input_queues": input_queues})
#         if output_queues:
#             resource_data.update({"output_queues": output_queues})
#         self.add_entry_to_data(self.resource_data, resource_data, label="Resource")

#     def add_default_queues(self, queue_capacity: int):
#         self.queue_data = {}
#         self.add_queue(ID="SourceQueue", description="Output queue for all sources", capacity=None)
#         self.add_queue(ID="SinkQueue", description="Input queue for all sinks", capacity=None)
#         for machine_ID in self.get_machines():
#             self.add_queue(
#                 ID="IQ" + machine_ID, description="Input queue of" + machine_ID, capacity=queue_capacity
#             )
#             self.resource_data[machine_ID]["input_queues"] = ["IQ" + machine_ID]
#             self.add_queue(
#                 ID="OQ" + machine_ID, description="Output queue of" + machine_ID, capacity=queue_capacity
#             )
#             self.resource_data[machine_ID]["output_queues"] = ["OQ" + machine_ID]


#     def add_resource_with_default_queue(
#         self,
#         ID: str,
#         description: str,
#         controller: str,
#         control_policy: str,
#         location: List[int],
#         capacity: int,
#         processes: List[str],
#         states: List[str],
#         queue_capacity: int,
#     ):
#         resource_data = {
#             "ID": ID,
#             "description": description,
#             "controller": controller,
#             "control_policy": control_policy,
#             "location": location,
#             "capacity": capacity,
#             "processes": processes,
#             "states": states,
#             "input_queues": ["IQ" + ID],
#             "output_queues": ["OQ" + ID],
#         }
#         self.add_queue(
#             ID="IQ" + ID, description="Input queue of " + ID, capacity=queue_capacity
#         )
#         self.add_queue(
#             ID="OQ" + ID, description="Output queue of " + ID, capacity=queue_capacity
#         )
#         self.add_entry_to_data(self.resource_data, resource_data, label="Resource")

#     def add_machine(self, control_policy: str, location: List[int], processes: List[str], states: List[str]):
#         machine_indices = self.get_machines()
#         for counter, machine_index in enumerate(machine_indices):
#             self.resource_data[machine_index]["ID"] = "M" + str(counter + 1)
#             self.resource_data[machine_index]["description"] = "Machine " + str(counter + 1)
#         new_machine_index = self.get_num_machines() + 1
#         self.add_resource_with_default_queue(
#             ID="M" + str(new_machine_index),
#             description="Machine " + str(new_machine_index),
#             controller="SimpleController",
#             control_policy=control_policy,
#             location=location,
#             capacity=1,
#             processes=processes,
#             states=states,
#             queue_capacity=100,
#         )

#     def add_transport_resource(self, control_policy: str, location: List[int], processes: List[str], states: List[str]):
#         tr_indices = self.get_transport_resources()
#         for counter, tr_index in enumerate(tr_indices):
#             self.resource_data[tr_index]["ID"] = "TR" + str(counter + 1)
#             self.resource_data[tr_index]["description"] = "Transport resource " + str(counter + 1)
#         new_tr_index = self.get_num_transport_resources() + 1
#         self.add_resource(
#             ID="TR" + str(new_tr_index),
#             description="Transport resource " + str(new_tr_index),
#             controller="TransportController",
#             control_policy=control_policy,
#             location=location,
#             capacity=1,
#             processes=processes,
#             states=states,
#         )

#     def add_source(
#         self,
#         ID: str,
#         description: str,
#         location: List[int],
#         time_model_id: str,
#         material_type: str,
#         router: str,
#         routing_heuristic: str,
#         output_queues: List[str],
#     ):
#         source_data = {
#             "ID": ID,
#             "description": description,
#             "location": location,
#             "time_model_id": time_model_id,
#             "material_type": material_type,
#             "router": router,
#             "routing_heuristic": routing_heuristic,
#             "output_queues": output_queues,
#         }
#         self.add_entry_to_data(self.source_data, source_data, label="Source")

#     def add_sink(
#         self,
#         ID: str,
#         description: str,
#         location: List[int],
#         material_type: str,
#         input_queues: List[str],
#     ):
#         sink_data = {
#             "ID": ID,
#             "description": description,
#             "location": location,
#             "material_type": material_type,
#             "input_queues": input_queues,
#         }
#         self.add_entry_to_data(self.sink_data, sink_data, label="Sink")

#     def to_dict(self) -> dict:
#         save_dict = {}
#         save_dict.update({"seed": self.seed})
#         save_dict.update({"time_models": self.time_model_data})
#         save_dict.update({"states": self.state_data})
#         save_dict.update({"processes": self.process_data})
#         save_dict.update({"queues": self.queue_data})
#         save_dict.update({"resources": self.resource_data})
#         save_dict.update({"materials": self.material_data})
#         save_dict.update({"sinks": self.sink_data})
#         save_dict.update({"sources": self.source_data})

#         save_dict = deepcopy(save_dict)
#         return save_dict

#     def to_json(self, file_path) -> None:
#         save_dict = {}
#         save_dict.update({"seed": self.seed})
#         save_dict.update({"time_models": self.time_model_data})
#         save_dict.update({"states": self.state_data})
#         save_dict.update({"processes": self.process_data})
#         save_dict.update({"queues": self.queue_data})
#         save_dict.update({"resources": self.resource_data})
#         save_dict.update({"materials": self.material_data})
#         save_dict.update({"sinks": self.sink_data})
#         save_dict.update({"sources": self.source_data})

#         with open(file_path, "w", encoding="utf-8") as json_file:
#             json.dump(save_dict, json_file)


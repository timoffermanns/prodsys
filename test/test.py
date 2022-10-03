# scenario_dict = {
#     "constraints": {
#         "max_reconfiguration_cost": 100000,
#         "max_num_machines": 5,
#         "max_num_processes_per_machine": 2,
#         "max_num_transport_resources": 3,
#     },
#     "options": {
#         "positions": ((0, 0), (0, 5), (5, 0), (5, 5), (10, 5), (5, 10)),
#         "machine_controllers": ["FIFO", "SPT", "LIFO"],
#         "transport_controllers": ["FIFO", "SPT_transport"],
#     },
#     "target": {
#         "quantity_material_1": 1300,
#     },
#     "costs": {"machine": 50000, "transport_resource": 20000, "process_module": 3000},
# }

# import json

# with open("data/scenario.json", "w") as wirter:
#     json.dump(scenario_dict, wirter)

machine_dict = {
    "1": {"ID": "M1", "c": 2},
    "2": {"ID": "M2", "c": 3},
    "4": {"ID": "M4", "c": 3},
    }

machines_1_keys = ["1", "2"]

b = {key: data for key, data in machine_dict.items() if key in machines_1_keys}

print(b)

del b["1"]
print(b)

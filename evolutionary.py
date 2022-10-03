from copy import copy
from dataclasses import dataclass
import json
from turtle import pos
from typing import List
from env import Environment
import loader
import print_util
from post_processing import PostProcessor

import random


def evaluate(options_dict, dict_results):
    # Do Simulation runs of all options and return dict_results
    pass


def crossover(ind1, ind2):
    crossover_type = random.choice(['machine', 'partial_machine', 'transport_resource'])
    if "machine " in crossover_type:
        machines_1_keys = ind1[0].get_machines()
        machines_2_keys = ind2[0].get_machines()
        if crossover_type == "partial_machine":
            min_length = max(len(machines_1_keys, machines_2_keys))
            machines_1_keys = machines_1_keys[:min_length]
            machines_2_keys = machines_2_keys[:min_length]

        machines_1_data = {key: data for key, data in ind1[0].resource_data.items() if key in machines_1_keys}
        machines_2_data = {key: data for key, data in ind2[0].resource_data.items() if key in machines_2_keys}

        for key in machines_1_keys:
            del ind1[0].resource_data[key]
        ind2[0].resource_data.update(machines_1_data)

        for key in machines_2_keys:
            del ind2[0].resource_data[key]
        ind1[0].resource_data.update(machines_2_data)

    if crossover_type == "transport_resource":
        tr1_keys = ind1[0].get_transport_resources()
        tr2_keys = ind2[0].get_transport_resources()


        tr1_data = {key: data for key, data in ind1[0].resource_data.items() if key in tr1_keys}
        tr2_data = {key: data for key, data in ind2[0].resource_data.items() if key in tr2_keys}

        for key in tr1_keys:
            del ind1[0].resource_data[key]
        ind2[0].resource_data.update(tr1_data)

        for key in tr2_keys:
            del ind2[0].resource_data[key]
        ind1[0].resource_data.update(tr2_data)

    return ind1, ind2


def mutation(scenario_dict, individual):
    mutation_operation = random.choice(
        [
            add_machine,
            add_transport_resource,
            add_process_module,
            remove_machine,
            remove_transport_resource,
            remove_process_module,
            move_machine,
            change_control_policy,
        ]
    )
    loader_object = individual[0]
    mutation_operation(loader_object, scenario_dict)


    return (individual,)


def add_machine(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    machine_index = loader_object.get_num_machines() + 1

    num_process_modules = random.choice(range(scenario_dict["constraints"]["max_num_processes_per_machine"])) + 1
    possible_processes = loader_object.get_processes()
    process_module_list = random.sample(possible_processes, num_process_modules)

    control_policy = random.choice(scenario_dict["options"]["machine_controllers"])
    location = random.choice(scenario_dict["options"]["positions"])

    loader_object.add_resource_with_default_queue(
        ID="M" + str(machine_index),
        description="Machine " + str(machine_index),
        controller="SimpleController",
        control_policy=control_policy,
        location=location,
        capacity=1,
        processes=process_module_list,
        states="BS1",
        queue_capacity=100,
    )


def add_transport_resource(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    transport_resource_index = loader_object.get_num_transport_resources() + 1
    control_policy = random.choice(scenario_dict["options"]["transport_controllers"])
    loader_object.add_resource(
        ID="TR" + str(transport_resource_index),
        description="Transport resource " + str(transport_resource_index),
        controller="TransportController",
        control_policy=control_policy,
        location=[0, 0],
        capacity=1,
        processes=["TP1"],
        states="BS2",
    )


def add_process_module(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    possible_machines = loader_object.get_machines()
    possible_processes = loader_object.get_processes()
    machine = random.choice(possible_machines)
    process_module_to_add = random.choice(possible_processes)
    loader_object.resource_data[machine]['processes'].append(process_module_to_add)


def remove_machine(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    possible_machines = loader_object.get_machines()
    if possible_machines:
        machine = random.choice(possible_machines)
        del loader_object.resource_data[machine]

def remove_transport_resource(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    transport_resources = loader_object.get_transport_resources()
    if transport_resources:
        transport_resource = random.choice(transport_resources)
        del loader_object.resource_data[transport_resource]


def remove_process_module(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    possible_machines = loader_object.get_machines()
    if possible_machines:
        machine = random.choice(possible_machines)
        process_modules = loader_object.resource_data[machine]['processes']
        if process_modules:
            process_module_to_delete = random.choice(process_modules)
            loader_object.resource_data[machine]['processes'].remove(process_module_to_delete)

def move_machine(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    possible_machines = loader_object.get_machines()
    machine = random.choice(possible_machines)
    current_location = loader_object.resource_data[machine]['location']

    new_location = random.choice(scenario_dict["options"]["positions"])

    # scenario_dict["options"]["positions"].remove(new_location)
    # scenario_dict["options"]["positions"].append(current_location)

    loader_object.resource_data[machine]['location'] = new_location

def change_control_policy(loader_object: loader.CustomLoader, scenario_dict: dict) -> None:
    resource = random.choice(list(loader_object.resource_data.keys()))
    if resource in loader_object.get_machines():
        possible_control_policies = copy(scenario_dict["options"]["machine_controllers"])
    else:
        possible_control_policies = copy(scenario_dict["options"]["transport_controllers"])
    
    possible_control_policies.remove(loader_object.resource_data[resource]["control_policy"])
    new_control_policy = random.choice(possible_control_policies)
    loader_object.resource_data[resource]["control_policy"] = new_control_policy

def calculate_reconfiguration_cost(
    scenario_dict: dict,
    configuration: loader.CustomLoader,
    baseline: loader.CustomLoader = None,
):
    num_machines = configuration.get_num_machines()
    num_transport_resources = configuration.get_num_transport_resources()
    num_process_modules = configuration.get_num_process_modules()
    if not baseline:
        num_machines_before = 4
        num_transport_resources_before = 1
        num_process_modules_before = {
            process: 0 for process in set(configuration.get_processes())
        }
    else:
        num_machines_before = baseline.get_num_machines()
        num_transport_resources_before = baseline.get_num_transport_resources()
        num_process_modules_before = baseline.get_num_process_modules()

    machine_cost = max(
        0, (num_machines - num_machines_before) * scenario_dict["costs"]["machine"]
    )
    transport_resource_cost = max(
        0,
        (num_transport_resources - num_transport_resources_before)
        * scenario_dict["costs"]["transport_resource"],
    )
    process_module_cost = 0
    possible_processes = baseline.get_processes()
    for process in set(possible_processes):
        if not process in num_process_modules.keys():
            num_process_modules[process] = 0
        process_module_cost += max(
            0,
            (num_process_modules[process] - num_process_modules_before[process])
            * scenario_dict["costs"]["process_module"],
        )

    return machine_cost + transport_resource_cost + process_module_cost


def random_configuration(
    scenario_dict: dict, base_scenario: str, reconfiguration=False
):

    loader_object = get_base_configuration(base_scenario)

    num_machines = (
        random.choice(range(scenario_dict["constraints"]["max_num_machines"])) + 1
    )
    num_transport_resources = (
        random.choice(
            range(scenario_dict["constraints"]["max_num_transport_resources"])
        )
        + 1
    )
    num_process_modules = [
        random.choice(
            range(scenario_dict["constraints"]["max_num_processes_per_machine"])
        )
        + 1
        for _ in range(num_machines)
    ]

    possible_processes = loader_object.get_processes()
    process_module_list = [
        random.sample(possible_processes, num_processes)
        for num_processes in num_process_modules
    ]

    capacity = 100

    loader_object.resource_data = {}
    loader_object.queue_data = {}

    for machine_index, processes in enumerate(process_module_list):
        control_policy = random.choice(scenario_dict["options"]["machine_controllers"])
        location = random.choice(scenario_dict["options"]["positions"])
        # scenario_dict["options"]["positions"].remove(location)

        loader_object.add_resource_with_default_queue(
            ID="M" + str(machine_index),
            description="Machine " + str(machine_index),
            controller="SimpleController",
            control_policy=control_policy,
            location=location,
            capacity=1,
            processes=processes,
            states="BS1",
            queue_capacity=capacity,
        )

    for transport_resource_index in range(num_transport_resources):
        control_policy = random.choice(
            scenario_dict["options"]["transport_controllers"]
        )
        loader_object.add_resource(
            ID="TR" + str(transport_resource_index),
            description="Transport resource " + str(transport_resource_index),
            controller="TransportController",
            control_policy=control_policy,
            location=[0, 0],
            capacity=1,
            processes=["TP1"],
            states="BS2",
        )

    return loader_object


def check_valid_configuration(configuration: loader.CustomLoader, base_configuration: loader.CustomLoader, scenario_dict: dict) -> bool:
    if configuration.get_num_machines() > scenario_dict["constraints"]["max_num_machines"]:
        return False
    
    if (configuration.get_num_transport_resources() > scenario_dict["constraints"]["max_num_transport_resources"]) or (configuration.get_num_transport_resources() == 0):
        return False
    
    for resource in configuration.resource_data.values():
        if len(resource["processes"]) > scenario_dict["constraints"]["max_num_processes_per_machine"]:
            return False
    
    reconfiguration_cost = calculate_reconfiguration_cost(scenario_dict=scenario_dict, configuration=configuration, baseline=base_configuration)
    configuration.reconfiguration_cost = reconfiguration_cost
    
    if reconfiguration_cost > scenario_dict["constraints"]["max_reconfiguration_cost"]:
        return False


    possibles_processes = set(base_configuration.get_processes())
    available_processes = set(configuration.get_num_process_modules().keys())

    if available_processes < possibles_processes:
        return False

    # TODO: add check with double positions!

    return True


def get_objective_values(environment: Environment, pp: PostProcessor) -> List[float]:
    reconfiguration_cost = environment.loader.reconfiguration_cost
    throughput_time = pp.get_aggregated_throughput_time_data()
    throughput = pp.get_aggregated_throughput_data()
    wip = pp.get_aggregated_wip_data()

    return [
        reconfiguration_cost,
        sum(throughput_time) / len(throughput_time),
        sum(throughput),
        sum(wip),
    ]

def get_base_configuration(filepath: str) -> loader.CustomLoader:
    loader_object = loader.CustomLoader()
    loader_object.read_data(filepath, "json")
    return loader_object


def evaluate(scenario_dict: dict, base_scenario: str, individual) -> List[float]:
    loader_object: loader.CustomLoader = individual[0]
    base_configuration = get_base_configuration(base_scenario)
    if not check_valid_configuration(loader_object, base_configuration, scenario_dict):
        # print("Invalid Configuration!")
        return [100000, 100000, -100000, 100000]

    e = Environment()
    e.loader = loader_object
    e.initialize_simulation()
    e.run(10000)

    e.data_collector.log_data_to_csv(filepath="data/data21.csv")
    p = PostProcessor(filepath="data/data21.csv")
    return get_objective_values(e, p)


if __name__ == "__main__":
    with open("data/scenario.json") as json_file:
        scenario_dict = json.load(json_file)
    loader_object = random_configuration(
        base_scenario="data/base_scenario.json", scenario_dict=scenario_dict
    )
    evaluate(loader_object)

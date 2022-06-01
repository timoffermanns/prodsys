"""
Mesa Data Collection Module
===========================

DataCollector is meant to provide a simple, standard way to collect data
generated by a Mesa model. It collects three types of data: model-level data,
agent-level data, and tables.

A DataCollector is instantiated with two dictionaries of reporter names and
associated variable names or functions for each, one for model-level data and
one for agent-level data; a third dictionary provides table names and columns.
Variable names are converted into functions which retrieve attributes of that
name.

When the collect() method is called, each model-level function is called, with
the model as the argument, and the results associated with the relevant
variable. Then the agent-level functions are called on each agent in the model
scheduler.

Additionally, other objects can write directly to tables by passing in an
appropriate dictionary object for a table row.

The DataCollector then stores the data it collects in dictionaries:
    * model_vars maps each reporter to a list of its values
    * tables maps each table to a dictionary, with each column as a key with a
      list as its value.
    * _agent_records maps each model step to a list of each agents id
      and its values.

Finally, DataCollector can create a pandas DataFrame from each collection.

The default DataCollector here makes several assumptions:
    * The model has a schedule object called 'schedule'
    * The schedule has an agent list called agents
    * For collecting agent-level variables, agents must have a unique_id

"""
from functools import partial
import pandas as pd
import types
from dataclasses import dataclass
import random

class DataCollector:
    """Class for collecting data generated by a Mesa model.

    A DataCollector is instantiated with dictionaries of names of model- and
    agent-level variables to collect, associated with attribute names or
    functions which actually collect them. When the collect(...) method is
    called, it collects these attributes and executes these functions one by
    one and stores the results.

    """

    model = None

    def __init__(self, reporters):
        """Instantiate a DataCollector with lists of model and agent reporters.
        Both model_reporters and agent_reporters accept a dictionary mapping a
        variable name to either an attribute name, or a method.
        For example, if there was only one model-level reporter for number of
        agents, it might look like:
            {"agent_count": lambda m: m.schedule.get_agent_count() }
        If there was only one agent-level reporter (e.g. the agent's energy),
        it might look like this:
            {"energy": "energy"}
        or like this:
            {"energy": lambda a: a.energy}

        The tables arg accepts a dictionary mapping names of tables to lists of
        columns. For example, if we want to allow agents to write their age
        when they are destroyed (to keep track of lifespans), it might look
        like:
            {"Lifespan": ["unique_id", "age"]}

        Args:
            reporters: Dictionary of reporter names and attributes/funcs

        Notes:
            If you want to pickle your model you must not use lambda functions.
            If your model includes a large number of agents, you should *only*
            use attribute names for the agent reporter, it will be much faster.

            Model reporters can take four types of arguments:
            lambda like above:
            {"agent_count": lambda m: m.schedule.get_agent_count() }
            method with @property decorators
            {"agent_count": schedule.get_agent_count()
            class attributes of model
            {"model_attribute": "model_attribute"}
            functions with parameters that have placed in a list
            {"Model_Function":[function, [param_1, param_2]]}

        """
        self.reporters = {}

        self.object_vars = {}

        if reporters is not None:
            for name, reporter in reporters.items():
                self._new_reporter(name, reporter)

    def _new_reporter(self, name, reporter):
        """Add a new reporter to collect.

        Args:
            name: Name of the variable to collect.
            reporter: Attribute string, or function object that returns the
                      variable when given a model instance.
        """
        if type(reporter) is str:
            reporter = partial(self._getattr, reporter)
        self.reporters[name] = reporter
        self.object_vars[name] = []

    def _reporter_decorator(self, reporter):
        return reporter()

    def collect(self, model):
        """Collect all the data for the given model object."""
        if self.reporters:

            for var, reporter in self.reporters.items():
                # Check if Lambda operator
                if isinstance(reporter, types.LambdaType):
                    self.object_vars[var].append(reporter(model))
                # Check if model attribute
                elif isinstance(reporter, partial):
                    self.object_vars[var].append(reporter(model))
                # Check if function with arguments
                elif isinstance(reporter, list):
                    self.object_vars[var].append(reporter[0](*reporter[1]))
                else:
                    self.object_vars[var].append(self._reporter_decorator(reporter))

    @staticmethod
    def _getattr(name, _object):
        """Turn around arguments of getattr to make it partially callable."""
        return getattr(_object, name, None)

    def get_vars_dataframe(self):
        """Create a pandas DataFrame from the model variables.

        The DataFrame has one column for each model variable, and the index is
        (implicitly) the model tick.

        """
        return pd.DataFrame(self.object_vars)



class Resource:

    def __init__(self):
        self.datacollector = None
        self.id = int(random.random()*100)
        self.states = ['UD', 'SD', 'PR']
        self.state = None
        self.time = 0
        self.available = None

    def add_data_collector(self, datacollector):
        self.datacollector = datacollector
        self.datacollector.collect(self)

    def step(self):
        self.state = random.choice(self.states)
        if self.state == 'PR':
            self.available = True
        else:
            self.available = False
        self.time += int(random.random()*20)
        print("Resource", self.id, "change to", self.state, "at", self.time)
        self.datacollector.collect(self)

    def step2(self):
        self.state = random.choice(self.states)
        if self.state == 'PR':
            self.available = True
        else:
            self.available = False
        self.time += int(random.random()*20)
        print("Resource", self.id, "change to", self.state, "at", self.time)
        self.datacollector.collect(self)



def get_id(resource: Resource):
    return resource.id


def get_state(resource: Resource):
    return resource.state

def get_time(resource: Resource):
    return resource.time

def get_available(resource: Resource):
    return resource.available


class Model:
    """A model with some number of agents."""

    def __init__(self, resources):
        self.resources = resources

    def step(self):
        for resource in self.resources:
            resource.step()

    def add_resource_data_collector(self, datacollector):
        resource_data_collector = DataCollector(reporters={"id": get_id, "time": get_time, "state": get_state})
        for resoure in self.resources:
            resoure.add_data_collector(datacollector)


r1 = Resource()
r2 = Resource()

d2 = DataCollector(reporters={"id": get_id, "time": get_time, "state": get_state, "available": get_available})
d1 = DataCollector(reporters={"id": get_id, "time": get_time, "available": get_available})

m = Model([r1, r2])
steps = 5

m.add_resource_data_collector(d2)
r2.add_data_collector(d1)


for _ in range(steps):
    m.step()

df2 = d2.get_vars_dataframe()
print("r1")
print(df2)

df = d1.get_vars_dataframe()
print("r2")
print(df)

import pandas as pd

df = pd.concat([df, df2])
print(df)
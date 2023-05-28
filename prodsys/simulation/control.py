from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pydantic import BaseModel, Field, validator, Extra
from typing import List, Generator, TYPE_CHECKING, Union

# from process import Process
from simpy import events

from prodsys.simulation import request, sim, state

if TYPE_CHECKING:
    from prodsys.simulation import product, process, state, resources, request, sink
    from prodsys.util import gym_env


class Controller(ABC, BaseModel):
    """
    A controller is responsible for controlling the processes of a resource. The controller is requested by materials requiring processes. The controller decides has a control policy that determines with which sequence requests are processed.

    Args:
        control_policy (Callable[[List[request.Request]], None]): The control policy that determines the sequence of requests to be processed.
        env (sim.Environment): The environment in which the controller is running.

    Attributes:
        resource (resources.Resource): The resource that is controlled by the controller.
        requested (events.Event): An event that is triggered when a request is made to the controller.
        requests (List[request.Request]): A list of requests that are made to the controller.
        running_processes (List[events.Event]): A list of (simpy) processes that are currently running on the resource.
    """

    control_policy: Callable[
        [
            List[request.Request],
        ],
        None,
    ]
    env: sim.Environment

    resource: resources.Resource = Field(init=False, default=None)
    requested: events.Event = Field(init=False, default=None)
    requests: List[request.Request] = Field(init=False, default_factory=list)
    running_processes: List[events.Process] = []

    @validator("requested", pre=True, always=True)
    def init_requested(cls, v, values):
        return events.Event(values["env"])

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    def set_resource(self, resource: resources.Resource) -> None:
        self.resource = resource
        self.env = resource.env

    def request(self, process_request: request.Request) -> None:
        """
        Request the controller consider the request in the future for processing.

        Args:
            process_request (request.Request): The request to be processed.
        """
        self.requests.append(process_request)
        if not self.requested.triggered:
            self.requested.succeed()

    @abstractmethod
    def control_loop(self) -> None:
        """
        The control loop is the main process of the controller. It has to run indefinetely.
        It should repeatedly check if requests are made or a process is finished and then start the next process.
        """
        pass

    @abstractmethod
    def get_next_product_for_process(
        self, resource: resources.Resource, process: process.Process
    ) -> List[events.Event]:
        """
        Get the next product for a process. The product is removed (get) from the queues.

        Args:
            resource (resources.Resource): The resource to take the product from.
            process (process.Process): The process that is requesting the product.

        Returns:
            List[events.Event]: The event that is triggered when the product is taken from the queue (multiple events for multiple products, e.g. for a batch process or an assembly).
        """
        pass


class ProductionController(Controller):
    resource: resources.ProductionResource = Field(init=False, default=None)

    def get_next_product_for_process(
        self, resource: resources.Resource, product: product.Product
    ) -> List[events.Event]:
        """
        Get the next product for a process. The product is removed (get) from the input queues of the resource.

        Args:
            resource (resources.Resource): The resource to take the product from.
            product (product.Product): The product that is requesting the product.

        Returns:
            List[events.Event]: The event that is triggered when the product is taken from the queue (multiple events for multiple products, e.g. for a batch process or an assembly).
        """
        events = []
        if isinstance(resource, resources.ProductionResource):
            for queue in resource.input_queues:
                events.append(
                    queue.get(filter=lambda item: item is product.product_data)
                )
            if not events:
                raise ValueError("No product in queue")
            return events
        else:
            raise ValueError("Resource is not a ProductionResource")

    def put_product_to_output_queue(
        self, resource: resources.Resource, products: List[product.Product]
    ) -> List[events.Event]:
        """
        Place a product to the output queue (put) of the resource.

        Args:
            resource (resources.Resource): The resource to place the product to.
            products (List[product.Product]): The products to be placed.

        Returns:
            List[events.Event]: The event that is triggered when the product is placed in the queue (multiple events for multiple products, e.g. for a batch process or an assembly).
        """
        events = []
        if isinstance(resource, resources.ProductionResource):
            for queue in resource.output_queues:
                for product in products:
                    events.append(queue.put(product.product_data))
        else:
            raise ValueError("Resource is not a ProductionResource")

        return events

    def control_loop(self) -> Generator:
        """
        The control loop is the main process of the controller. It has to run indefinetely.

        The logic is the control loop of a production resource is the following:

        1. Wait until a request is made or a process is finished.
        2. If a request is made, add it to the list of requests.
        3. If a process is finished, remove it from the list of running processes.
        4. If the resource is full or there are no requests, go to 1.
        5. Sort the queue according to the control policy.
        6. Start the next process. Go to 1.

        Yields:
            Generator: The generator yields when a request is made or a process is finished.
        """
        while True:
            yield events.AnyOf(
                env=self.env, events=self.running_processes + [self.requested]
            )
            if self.requested.triggered:
                self.requested = events.Event(self.env)
            for process in self.running_processes:
                if not process.is_alive:
                    self.running_processes.remove(process)
            if self.resource.full or not self.requests:
                continue
            self.control_policy(self.requests)
            running_process = self.env.process(self.start_process())
            self.running_processes.append(running_process)
            if not self.resource.full:
                self.requested.succeed()

    def start_process(self) -> Generator:
        """
        Start the next process with the following logic:

        1. Setup the resource for the process.
        2. Wait until the resource is free for the process.
        3. Retrieve the product from the queue.
        4. Run the process and wait until finished.
        5. Place the product in the output queue.

        Yields:
            Generator: The generator yields when the process is finished.
        """
        yield self.env.timeout(0)
        process_request = self.requests.pop(0)
        resource = process_request.get_resource()
        process = process_request.get_process()
        product = process_request.get_product()

        yield self.env.process(resource.setup(process))
        with resource.request() as req:
            yield req
            eventss = self.get_next_product_for_process(resource, product)
            yield events.AllOf(resource.env, eventss)
            possible_states = resource.get_processes(process)
            while True:
                production_state = resource.get_free_process(process)
                if production_state is not None:
                    break
                yield events.AnyOf(
                    self.env,
                    [
                        state.process
                        for state in possible_states
                        if state.process is not None and state.process.is_alive
                    ],
                )
            yield self.env.process(self.run_process(production_state, product))
            production_state.process = None
            eventss = self.put_product_to_output_queue(resource, [product])
            yield events.AllOf(resource.env, eventss)
            for next_product in [product]:
                if not resource.got_free.triggered:
                    resource.got_free.succeed()
                next_product.finished_process.succeed()

    def run_process(self, input_state: state.State, target_product: product.Product):
        """
        Run the process of a product. The process is started and the product is logged.

        Args:
            input_state (state.State): The production state of the process.
            target_product (product.Product): The product that is processed.
        """
        input_state.prepare_for_run()
        input_state.state_info.log_product(
            target_product, state.StateTypeEnum.production
        )
        target_product.product_info.log_start_process(
            target_product.next_resource,
            target_product,
            self.env.now,
            state.StateTypeEnum.production,
        )
        input_state.process = self.env.process(input_state.process_state())
        yield input_state.process


class TransportController(Controller):
    resource: resources.TransportResource = Field(init=False, default=None)
    requests: List[request.TransportResquest] = Field(default_factory=list)
    control_policy: Callable[
        [
            List[request.TransportResquest],
        ],
        None,
    ]

    def get_next_product_for_process(
        self, resource: product.Location, product: product.Product
    ):
        events = []
        if isinstance(resource, resources.ProductionResource) or isinstance(
            resource, source.Source
        ):
            for queue in resource.output_queues:
                events.append(queue.get(filter=lambda x: x is product.product_data))
            if not events:
                raise ValueError("No product in queue")
        else:
            raise ValueError(f"Resource {resource.data.ID} is not a ProductionResource")
        return events

    def put_product_to_input_queue(
        self, resource: product.Location, product: product.Product
    ) -> List[events.Event]:
        events = []
        if isinstance(resource, resources.ProductionResource) or isinstance(
            resource, sink.Sink
        ):
            for queue in resource.input_queues:
                events.append(queue.put(product.product_data))
        else:
            raise ValueError(
                f"Resource {resource.data.ID} is not a ProductionResource or Sink"
            )

        return events

    def control_loop(self) -> Generator:
        while True:
            yield events.AnyOf(
                env=self.env, events=self.running_processes + [self.requested]
            )
            if self.requested.triggered:
                self.requested = events.Event(self.env)
            for process in self.running_processes:
                if not process.is_alive:
                    self.running_processes.remove(process)
            if self.resource.full or not self.requests:
                continue
            self.control_policy(self.requests)
            running_process = self.env.process(self.start_process())
            self.running_processes.append(running_process)
            if not self.resource.full:
                self.requested.succeed()

    def start_process(self) -> Generator:
        yield self.env.timeout(0)
        process_request = self.requests.pop(0)

        resource = process_request.get_resource()
        process = process_request.get_process()
        product = process_request.get_product()
        origin = process_request.get_origin()
        target = process_request.get_target()

        yield self.env.process(resource.setup(process))
        with resource.request() as req:
            yield req
            if origin.get_location() != resource.get_location():
                possible_states = resource.get_processes(process)
                while True:
                    transport_state = resource.get_free_process(process)
                    if transport_state is not None:
                        break
                    yield events.AnyOf(
                        self.env,
                        [
                            state.process
                            for state in possible_states
                            if state.process is not None and state.process.is_alive
                        ],
                    )

                yield self.env.process(
                    self.run_process(transport_state, product, target=origin)
                )
                transport_state.process = None

            eventss = self.get_next_product_for_process(origin, product)
            yield events.AllOf(resource.env, eventss)
            possible_states = resource.get_processes(process)
            while True:
                transport_state = resource.get_free_process(process)
                if transport_state is not None:
                    break
                yield events.AnyOf(
                    self.env,
                    [
                        state.process
                        for state in possible_states
                        if state.process is not None and state.process.is_alive
                    ],
                )
            yield self.env.process(
                self.run_process(transport_state, product, target=target)
            )
            transport_state.process = None
            eventss = self.put_product_to_input_queue(target, product)
            yield events.AllOf(resource.env, eventss)
            if isinstance(target, resources.ProductionResource):
                target.unreserve_input_queues()
            product.finished_process.succeed()

    def run_process(
        self,
        input_state: state.State,
        product: product.Product,
        target: product.Location,
    ):
        """
        Run the process of a product. The process is started and the product is logged.

        Args:
            input_state (state.State): The transport state of the process.
            product (product.Product): The product that is transported.
            target (product.Location): The target of the transport.
        """
        target_location = target.get_location()
        input_state.prepare_for_run()
        input_state.state_info.log_product(product, state.StateTypeEnum.transport)
        input_state.state_info.log_target_location(
            target, state.StateTypeEnum.transport
        )
        product.product_info.log_start_process(
            product.next_resource,
            product,
            self.env.now,
            state.StateTypeEnum.transport,
        )
        input_state.process = self.env.process(
            input_state.process_state(target=target_location)  # type: ignore False
        )
        yield input_state.process


def FIFO_control_policy(requests: List[request.Request]) -> None:
    pass


def LIFO_control_policy(requests: List[request.Request]) -> None:
    requests.reverse()


def SPT_control_policy(requests: List[request.Request]) -> None:
    requests.sort(key=lambda x: x.process.get_expected_process_time())


def SPT_transport_control_policy(requests: List[request.TransportResquest]) -> None:
    requests.sort(
        key=lambda x: x.process.get_expected_process_time(
            x.origin.get_location(), x.target.get_location()
        )
    )


def agent_control_policy(
    gym_env: gym_env.ProductionControlEnv, requests: List[request.Request]
) -> None:
    gym_env.interrupt_simulation_event.succeed()


class BatchController(Controller):
    pass


from prodsys.simulation import resources, source, sink

Controller.update_forward_refs()
ProductionController.update_forward_refs()
TransportController.update_forward_refs()

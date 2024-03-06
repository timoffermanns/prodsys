from __future__ import annotations

from typing import List, Dict

from pydantic import BaseModel, Field


from prodsys.simulation import auxiliary, router, sim
from prodsys.models import product_data
from prodsys.factories import process_factory, auxiliary_factory
from prodsys.simulation import logger, proces_models, process


class ProductFactory(BaseModel):
    """
    Factory class that creates and stores `prodsys.simulation` product objects from `prodsys.models` product objects.

    Args:
        env (sim.Environment): prodsys simulation environment.
        process_factory (process_factory.ProcessFactory): Factory that creates process objects.
    """

    env: sim.Environment
    process_factory: process_factory.ProcessFactory
    auxiliary_factory: auxiliary_factory.AuxiliaryFactory
    products: List[product.Product] = []
    auxilaries: List[auxiliary.Auxiliary] = []
    finished_products: List[product.Product] = []
    event_logger: logger.EventLogger = Field(default=False, init=False)
    product_counter = 0

    class Config:
        arbitrary_types_allowed = True

    def create_product(
        self, product_data: product_data.ProductData, router: router.Router
    ) -> product.Product:
        """
        Creates a product object based on the given product data and router.

        Args:
            product_data (product_data.ProductData): Product data that is used to create the product object.
            router (router.Router): Router that is used to route the product object.

        Raises:
            ValueError: If the transport process is not found.

        Returns:
            product.Product: Created product object.
        """
        product_data = product_data.copy()
        product_data.ID = (
            str(product_data.product_type) + "_" + str(self.product_counter)
        )
        process_model = self.create_process_model(product_data)
        transport_processes = self.process_factory.get_process(
            product_data.transport_process
        )
        if not transport_processes or isinstance(
            transport_processes, process.ProductionProcess
        ):
            raise ValueError("Transport process not found.")
        
        if product_data.auxiliaries:
            auxiliaries = []
            for auxiliary in self.auxiliary_factory.auxiliaries:
                if auxiliary.auxiliary_data.ID in product_data.auxiliaries:
                    auxiliaries.append(self.auxiliary_factory.get_auxiliary(auxiliary.auxiliary_data.ID))
        product_object = product.Product(
            env=self.env,
            product_data=product_data,
            product_router=router,
            process_model=process_model,
            auxiliaries=auxiliaries,
            transport_process=transport_processes,
        )
        if self.event_logger:
            self.event_logger.observe_terminal_product_states(product_object)

        self.product_counter += 1
        self.products.append(product_object)
        return product_object

    def get_precendece_graph_from_id_adjacency_matrix(
        self, id_adjacency_matrix: Dict[str, List[str]]
    ) -> proces_models.PrecedenceGraphProcessModel:
        precedence_graph = proces_models.PrecedenceGraphProcessModel()
        id_predecessor_adjacency_matrix = (
            proces_models.get_predecessors_adjacency_matrix(id_adjacency_matrix)
        )
        for key in id_adjacency_matrix.keys():
            sucessor_ids = id_adjacency_matrix[key]
            predecessor_ids = id_predecessor_adjacency_matrix[key]
            process = self.process_factory.get_process(key)
            successors = [
                self.process_factory.get_process(successor_id)
                for successor_id in sucessor_ids
            ]
            predecessors = [
                self.process_factory.get_process(predecessor_id)
                for predecessor_id in predecessor_ids
            ]
            precedence_graph.add_node(process, successors, predecessors)
        return precedence_graph

    def create_process_model(
        self, product_data: product_data.ProductData
    ) -> proces_models.ProcessModel:
        """
        Creates a process model based on the given product data.

        Args:
            product_data (product_data.ProductData): Product data that is used to create the process model.

        Raises:
            ValueError: If the process model is not recognized.

        Returns:
            proces_models.ProcessModel: Created process model.
        """
        if isinstance(product_data.processes, list) and isinstance(
            product_data.processes[0], str
        ):
            process_list = self.process_factory.get_processes_in_order(
                product_data.processes
            )
            return proces_models.ListProcessModel(process_list=process_list)
        elif isinstance(product_data.processes, dict):
            return self.get_precendece_graph_from_id_adjacency_matrix(
                product_data.processes
            )
        elif isinstance(product_data.processes, list) and isinstance(
            product_data.processes[0], list
        ):
            id_adjacency_matrix = proces_models.get_adjacency_matrix_from_edges(
                product_data.processes
            )
            return self.get_precendece_graph_from_id_adjacency_matrix(
                id_adjacency_matrix
            )
        else:
            raise ValueError("Process model not recognized.")

    def get_product(self, ID: str) -> product.Product:
        """
        Returns the product object with the given ID.

        Args:
            ID (str): ID of the product object.

        Returns:
            product.Product: Product object with the given ID.
        """
        return [m for m in self.products if m.product_data.ID == ID].pop()

    def remove_product(self, product: product.Product):
        """
        Removes the given product object from the product factory list of current product objects.

        Args:
            product (product.Product): Product object that is removed.
        """
        self.products = [
            m for m in self.products if m.product_data.ID != product.product_data.ID
        ]

    def register_finished_product(self, product: product.Product):
        """
        Registers the given product object as a finished product object.

        Args:
            product (product.Product): Product object that is registered as a finished product object.
        """
        self.finished_products.append(product)
        self.remove_product(product)


from prodsys.simulation import product

product.Product.update_forward_refs()

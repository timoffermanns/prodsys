from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

from pydantic import BaseModel, parse_obj_as, Field


from prodsys.simulation import router, sim, source
from prodsys.data_structures import source_data, material_data


if TYPE_CHECKING:
    from prodsys.factories import (
        material_factory,
        resource_factory,
        queue_factory,
        time_model_factory,
        sink_factory,
    )
    from prodsys.adapters import adapter


class SourceFactory(BaseModel):
    env: sim.Environment
    material_factory: material_factory.MaterialFactory
    time_model_factory: time_model_factory.TimeModelFactory
    queue_factory: queue_factory.QueueFactory
    resource_factory: resource_factory.ResourceFactory
    sink_factory: sink_factory.SinkFactory

    material_data: List[material_data.MaterialData] = Field(
        default_factory=list, init=False
    )
    sources: List[source.Source] = Field(default_factory=list, init=False)

    class Config:
        arbitrary_types_allowed = True

    def create_sources(self, adapter: adapter.ProductionSystemAdapter):
        for values in adapter.source_data:
            for material_d in adapter.material_data:
                if material_d.material_type == values.material_type:
                    self.add_source(values, material_d)

    def get_router(self, router_type: str, routing_heuristic: str):
        return router.ROUTERS[router_type](
            self.resource_factory,
            self.sink_factory,
            router.ROUTING_HEURISTIC[routing_heuristic],
        )

    def add_source(
        self,
        source_data: source_data.SourceData,
        material_data_of_source: material_data.MaterialData,
    ):
        router = self.get_router(source_data.router, source_data.routing_heuristic)

        time_model = self.time_model_factory.get_time_model(source_data.time_model_id)

        source_object = source.Source(
            env=self.env,
            data=source_data,
            material_data=material_data_of_source,
            material_factory=self.material_factory,
            time_model=time_model,
            router=router,
        )
        self.add_queues_to_source(source_object, source_data.output_queues)
        self.sources.append(source_object)

    def add_queues_to_source(self, source: source.Source, values: List[str]):
        output_queues = self.queue_factory.get_queues(values)
        source.add_output_queues(output_queues)

    def start_sources(self):
        for _source in self.sources:
            _source.start_source()

    def get_source(self, ID) -> source.Source:
        return [s for s in self.sources if s.data.ID == ID].pop()

    def get_sources(self, IDs: List[str]) -> List[source.Source]:
        return [s for s in self.sources if s.data.ID in IDs]

    def get_sources_with_material_type(self, __material_type: str):
        return [s for s in self.sources if __material_type == s.data.material_type]


from prodsys.factories import (
    material_factory,
    resource_factory,
    queue_factory,
    time_model_factory,
    sink_factory,
)

SourceFactory.update_forward_refs()

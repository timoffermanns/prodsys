from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prodsys.simulation import material, process, resources


class Request:
    def __init__(
        self,
        process: process.PROCESS_UNION,
        material: material.Material,
        resource: resources.Resource,
    ):
        self.process = process
        self.material = material
        self.resource = resource

    def get_process(self) -> process.PROCESS_UNION:
        return self.process

    def get_material(self) -> material.Material:
        return self.material

    def get_resource(self) -> resources.Resource:
        return self.resource


class TransportResquest(Request):
    def __init__(
        self,
        process: process.TransportProcess,
        material: material.Material,
        resource: resources.TransportResource,
        origin: material.Location,
        target: material.Location,
    ):
        self.process: process.TransportProcess = process
        self.material: material.Material = material
        self.resource: resources.TransportResource = resource
        self.origin: material.Location = origin
        self.target: material.Location = target

    def get_process(self) -> process.TransportProcess:
        return self.process

    def get_resource(self) -> resources.TransportResource:
        return self.resource

    def get_origin(self) -> material.Location:
        return self.origin

    def get_target(self) -> material.Location:
        return self.target
from __future__ import annotations

from enum import Enum
from typing import Literal, Union, Optional

from prodsim.data_structures.core_asset import CoreAsset

class ProcessTypeEnum(str, Enum):
    ProductionProcesses = "ProductionProcesses"
    TransportProcesses = "TransportProcesses"
    CapabilityProcesses = "CapabilityProcesses"

class ProcessData(CoreAsset):
    time_model_id: str

class ProductionProcessData(ProcessData):
    type: Literal[ProcessTypeEnum.ProductionProcesses]


class CapabilityProcessData(ProcessData):
    type: Literal[ProcessTypeEnum.CapabilityProcesses]
    capability: str

class TransportProcessData(ProcessData):
    type: Literal[ProcessTypeEnum.TransportProcesses]

PROCESS_DATA_UNION = Union[
    ProductionProcessData, TransportProcessData, CapabilityProcessData
]

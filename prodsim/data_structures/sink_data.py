from __future__ import annotations

from typing import Literal, Union, List, Tuple, Optional

from pydantic import validator, conlist

from prodsim.data_structures.core_asset import CoreAsset


class SinkData(CoreAsset):
    location: conlist(float, min_items=2, max_items=2)
    material_type: str
    input_queues: List[str]

    class Config:
        schema_extra = {
            "example": {
                "ID": "SK1",
                "description": "Sink 1",
                "location": [50.0, 50.0],
                "material_type": "Material_1",
                "input_queues": ["SinkQueue"],
            }
        }

from __future__ import annotations

from typing import Literal, Union, List, Tuple, Optional

from pydantic import root_validator

from prodsim.data_structures.core_asset import CoreAsset


class MaterialData(CoreAsset):
    material_type: str
    processes: Union[List[str], str]
    transport_process: str

    @root_validator(pre=True)
    def check_processes(cls, values):
        if "material_type" in values and values["material_type"]:
            values["ID"] = values["material_type"]
        else:
            values["material_type"] = values["ID"]
        return values
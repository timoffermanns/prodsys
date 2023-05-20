from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from prodsys.data_structures.core_asset import CoreAsset


class StateTypeEnum(str, Enum):
    """
    Enum that represents the different kind of states.
    """

    BreakDownState = "BreakDownState"
    ProductionState = "ProductionState"
    TransportState = "TransportState"
    SetupState = "SetupState"
    ProcessBreakDownState = "ProcessBreakDownState"


class StateData(CoreAsset):
    """
    Class that represents a state.

    Args:
        ID (str): ID of the state.
        description (str): Description of the state.
        time_model_id (str): Time model ID of the state.
        type (StateTypeEnum): Type of the state.
    """

    time_model_id: str
    type: Literal[
        StateTypeEnum.BreakDownState,
        StateTypeEnum.ProductionState,
        StateTypeEnum.TransportState,
        StateTypeEnum.SetupState,
    ]

    class Config:
        schema_extra = {
            "example": {
                "summary": "State",
                "value": {
                    "ID": "state_1",
                    "description": "State data for state_1",
                    "time_model_id": "time_model_1",
                    "type": "ProductionState",
                },
            }
        }


class BreakDownStateData(StateData):
    """
    Class that represents a breakdown state.

    Args:
        ID (str): ID of the state.
        description (str): Description of the state.
        time_model_id (str): Time model ID of the state.
        type (StateTypeEnum): Type of the state.
        repair_time_model_id (str): Time model ID of the repair time.
    """

    type: Literal[StateTypeEnum.BreakDownState]
    repair_time_model_id: str

    class Config:
        schema_extra = {
            "example": {
                "summary": "Breakdown state",
                "value": {
                    "ID": "Breakdownstate_1",
                    "description": "Breakdown state machine 1",
                    "time_model_id": "function_time_model_5",
                    "type": "BreakDownState",
                    "repair_time_model_id": "function_time_model_8",
                },
            }
        }


class ProcessBreakDownStateData(StateData):
    """
    Class that represents a process breakdown state. It is a breakdown state that is connected to a process. Other processes can still be executed while the process breakdown state is activen.

    Args:
        ID (str): ID of the state.
        description (str): Description of the state.
        time_model_id (str): Time model ID of the state.
        type (StateTypeEnum): Type of the state.
        repair_time_model_id (str): Time model ID of the repair time.
    """

    type: Literal[StateTypeEnum.ProcessBreakDownState]
    repair_time_model_id: str
    process_id: str

    class Config:
        schema_extra = {
            "example": {
                "summary": "Process breakdown state",
                "value": {
                    "ID": "ProcessBreakDownState_1",
                    "description": "Process Breakdown state machine 1",
                    "time_model_id": "function_time_model_7",
                    "type": "ProcessBreakDownState",
                    "process_id": "P1",
                    "repair_time_model_id": "function_time_model_8",
                },
            }
        }


class ProductionStateData(StateData):
    """
    Class that represents a production state. By undergoing a production state, the material is processed and continues its process model.

    Args:
        ID (str): ID of the state.
        description (str): Description of the state.
        time_model_id (str): Time model ID of the state.
        type (StateTypeEnum): Type of the state.
    """

    type: Literal[StateTypeEnum.ProductionState]

    class Config:
        schema_extra = {
            "example": {
                "summary": "Production state",
                "value": {
                    "ID": "ProductionState_1",
                    "description": "Production state machine 1",
                    "time_model_id": "function_time_model_1",
                    "type": "ProductionState",
                },
            }
        }


class TransportStateData(StateData):
    """
    Class that represents a transport state. By undergoing a transport state, the material is transported and its position is changed.

    Args:
        ID (str): ID of the state.
        description (str): Description of the state.
        time_model_id (str): Time model ID of the state.
        type (StateTypeEnum): Type of the state.
    """

    type: Literal[StateTypeEnum.TransportState]

    class Config:
        schema_extra = {
            "example": {
                "summary": "Transport state",
                "value": {
                    "ID": "TransportState_1",
                    "description": "Transport state machine 1",
                    "time_model_id": "function_time_model_3",
                    "type": "TransportState",
                },
            }
        }


class SetupStateData(StateData):
    """
    Class that represents a setup state. By undergoing a setup state, the process is setup.

    Args:
        ID (str): ID of the state.
        description (str): Description of the state.
        time_model_id (str): Time model ID of the state.
        type (StateTypeEnum): Type of the state.
        origin_setup (str): ID of the origin setup.
        target_setup (str): ID of the target setup.
    """

    type: Literal[StateTypeEnum.SetupState]
    origin_setup: str
    target_setup: str

    class Config:
        schema_extra = {
            "example": {
                "summary": "Setup state",
                "value": {
                    "ID": "Setup_State_2",
                    "description": "Setup state machine 2",
                    "time_model_id": "function_time_model_2",
                    "type": "SetupState",
                    "origin_setup": "P2",
                    "target_setup": "P1",
                },
            }
        }


STATE_DATA_UNION = Union[
    BreakDownStateData,
    ProductionStateData,
    TransportStateData,
    SetupStateData,
    ProcessBreakDownStateData,
]

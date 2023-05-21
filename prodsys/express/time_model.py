from __future__ import annotations

from typing import List, Optional, Union
from uuid import uuid1

from pydantic.dataclasses import dataclass
from pydantic import validator, Field

from prodsys.data_structures import time_model_data
from prodsys.express import core

@dataclass
class SequentialTimeModel(core.ExpressObject):
    """
    Class that represents a time model that is based on a sequence of values.

    Args:
        sequence (List[float]): Sequence of time values.
        ID (str): ID of the time model.

    Examples:
        Sequential time model with 7 time values:
        >>> import prodsys.express as psx
        >>> psx.SequentialTimeModel(
        ...     sequence=[25.0, 13.0, 15.0, 16.0, 17.0, 20.0, 21.0],
        ... )
    """
    sequence: List[float]
    ID: Optional[str] = Field(default_factory=lambda: str(uuid1()))


    def to_data_object(self) -> time_model_data.SequentialTimeModelData:
        """
        Converts the object to a data object.

        Returns:
            time_model_data.SequentialTimeModelData: Data object of the express object.
        """
        return time_model_data.SequentialTimeModelData(
            sequence=self.sequence,
            ID=self.ID,
            description=""
        )

@dataclass
class FunctionTimeModel(core.ExpressObject):
    """
    Class that represents a time model that is based on a function and represents the timely values by their distribution function.

    Args:
        distribution_function (FunctionTimeModelEnum): Function that represents the time model, can either be 'normal', 'lognormal', 'exponential' or 'constant'.
        location (float): Location parameter of the distribution function.
        scale (float): Scale parameter of the distribution function.
        ID (str): ID of the time model.


    Examples:
        Normal distribution time model with 20 minutes mean and 5 minutes standard deviation:
        >>> import prodsys.express as psx
        >>> psx.FunctionTimeModel(
        ...     distribution_function="normal",
        ...     location=20.0,
        ...     scale=5.0,
        ... )
    """
    distribution_function: time_model_data.FunctionTimeModelEnum
    location: float
    scale: float = 0.0
    ID: Optional[str] = Field(default_factory=lambda: str(uuid1()))

    def to_data_object(self) -> time_model_data.FunctionTimeModelData:
        """
        Converts the express object to a data object.

        Returns:
            time_model_data.FunctionTimeModelData: Data object of the express object.
        """
        return time_model_data.FunctionTimeModelData(
            distribution_function=self.distribution_function,
            location=self.location,
            scale=self.scale,
            ID=self.ID,
            description=""
        )


@dataclass
class ManhattanDistanceTimeModel(core.ExpressObject):
    """
    Class that represents a time model that is based on the manhattan distance between two nodes and a constant velocity.

    Args:
        speed (float): Speed of the vehicle in meters per minute.
        reaction_time (float): Reaction time of the driver in minutes.

    Examples:
        Manhattan distance time model with 20 minutes mean and 5 minutes standard deviation:
        >>> import prodsys.express as psx
        >>> psx.ManhattanDistanceTimeModel(
        ...     speed=20.0,
        ...     reaction_time=5.0,
        ... )
    """
    speed: float
    reaction_time: float
    ID: Optional[str] = Field(default_factory=lambda: str(uuid1()))

    def to_data_object(self) -> time_model_data.ManhattanDistanceTimeModelData:
        """
        Converts the express object to a data object.

        Returns:
            time_model_data.ManhattanDistanceTimeModelData: Data object of the express object.
        """
        return time_model_data.ManhattanDistanceTimeModelData(
            speed=self.speed,
            reaction_time=self.reaction_time,
            ID=self.ID,
            description=""
        )

TIME_MODEL_UNION = Union[
    SequentialTimeModel,
    FunctionTimeModel,
    ManhattanDistanceTimeModel,
]
    




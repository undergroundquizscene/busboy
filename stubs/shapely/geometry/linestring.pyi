from enum import Enum
from typing import Union

from shapely.geometry.base import BaseGeometry
from shapely.geometry.multilinestring import MultiLineString

class LineString(BaseGeometry):
    def parallel_offset(
        self,
        distance: float,
        side: str = "right",
        resolution: int = 16,
        join_style: int = 1,
        mitre_limit: float = 5.0,
    ) -> Union[LineString, MultiLineString]: ...

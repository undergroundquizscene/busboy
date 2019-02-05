from typing import Sequence, Union

from shapely.geometry.base import BaseMultipartGeometry
from shapely.geometry.linestring import LineString

Linelike = Union[Sequence[Sequence[float]], LineString]

class MultiLineString(BaseMultipartGeometry):
    def __init__(self, lines: Sequence[Linelike]) -> None: ...

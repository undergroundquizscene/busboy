from typing import Sequence, Union

from shapely.geometry.linestring import LineString
from shapely.geometry.base import BaseMultipartGeometry

Linelike = Union[Sequence[Sequence[float]], LineString]

class MultiLineString(BaseMultipartGeometry):
    def __init__(self, lines: Sequence[Linelike]) -> None: ...

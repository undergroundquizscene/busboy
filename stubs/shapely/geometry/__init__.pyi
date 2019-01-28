from typing import Iterable, Optional, Sequence, Tuple, Union

from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.geometry.multilinestring import MultiLineString as MultiLineString
from shapely.geometry.linestring import LineString as LineString

Pointlike = Union[Point, Tuple[float, float]]

class Polygon(BaseGeometry): ...

class MultiPoint(BaseMultipartGeometry):
    def __init__(self, points: Optional[Sequence[Pointlike]] = None): ...

class Point(BaseGeometry): ...

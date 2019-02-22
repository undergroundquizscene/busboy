from typing import Any, Optional

from shapely.geometry import Polygon

class BaseGeometry(object):
    minimum_rotated_rectangle: Polygon
    def almost_equals(self, other: "BaseGeometry", decimal: int = 6) -> bool: ...
    def buffer(
        self,
        distance: float,
        resolution: int = 16,
        quadsegs: Optional[Any] = None,
        cap_style: int = 1,
        join_style: int = 1,
        mitre_limit: float = 0.5,
    ) -> "BaseGeometry": ...
    def contains(self, other: "BaseGeometry") -> bool: ...
    def distance(self, other: "BaseGeometry") -> float: ...
    def difference(self, other: "BaseGeometry") -> BaseGeometry: ...

class BaseMultipartGeometry(BaseGeometry): ...

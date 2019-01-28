from shapely.geometry.base import BaseGeometry
from typing import overload, Sequence, Optional


class Point(BaseGeometry):
    @overload
    def __init__(self, parts: Sequence[float]) -> None: ...
    @overload
    def __init__(self, *args: float) -> None: ...

from typing import Optional, Sequence, overload

from shapely.geometry.base import BaseGeometry

class Point(BaseGeometry):
    @overload
    def __init__(self, parts: Sequence[float]) -> None: ...
    @overload
    def __init__(self, *args: float) -> None: ...

from pandas import Series, DataFrame
from typing import Dict, Any

class GeoSeries(Series):
    crs: Dict[str, str]
    bounds: DataFrame
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def to_crs(self, crs: Dict[str, str]) -> "GeoSeries": ...
    def buffer(
        self, distance: float, resolution: float = 16, **kwargs: Any
    ) -> "GeoSeries": ...

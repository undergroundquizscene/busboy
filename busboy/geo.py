from typing import NewType, Tuple

import geopandas as gpd
from shapely.geometry import Point

Longitude = NewType("Longitude", float)
Latitude = NewType("Latitude", float)
MetreLongitude = NewType("MetreLongitude", float)
MetreLatitude = NewType("MetreLatitude", float)


degree_crs = {"init": "epsg:4326"}
metre_crs = {"init": "epsg:29902"}


def to_metres(t: Tuple[Longitude, Latitude]) -> Tuple[MetreLongitude, MetreLatitude]:
    s = gpd.GeoSeries(Point(t))
    s.crs = degree_crs
    m = s.to_crs(metre_crs)
    return m[0].coords[0]

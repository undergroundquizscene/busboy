from operator import itemgetter
from typing import Any, Dict, List, NewType, Optional, Tuple, TypeVar, Union

import geopandas as gpd
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from shapely.geometry import Point

from busboy.util import omap, swap

Longitude = Union["MetreLongitude", "RawLongitude", "DegreeLongitude"]
Latitude = Union["MetreLatitude", "RawLatitude", "DegreeLatitude"]
RawLatitude = NewType("RawLatitude", int)
RawLongitude = NewType("RawLongitude", int)
DegreeLongitude = NewType("DegreeLongitude", float)
DegreeLatitude = NewType("DegreeLatitude", float)
MetreLongitude = NewType("MetreLongitude", float)
MetreLatitude = NewType("MetreLatitude", float)
DegreeLonLat = Tuple[DegreeLongitude, DegreeLatitude]
DegreeLatLon = Tuple[DegreeLatitude, DegreeLongitude]
MetreLonLat = Tuple[MetreLongitude, MetreLatitude]
MetreLatLon = Tuple[MetreLatitude, MetreLongitude]
RawLonLat = Tuple[RawLongitude, RawLatitude]
RawLatLon = Tuple[RawLatitude, RawLongitude]
LonLat = Union[MetreLonLat, RawLonLat, DegreeLonLat]
LatLon = Union[MetreLatLon, RawLatLon, DegreeLatLon]
BoundingBox = Tuple[DegreeLongitude, DegreeLatitude, DegreeLongitude, DegreeLatitude]


degree_crs = {"init": "epsg:4326"}
metre_crs = {"init": "epsg:29902"}


def to_metres(
    t: Tuple[DegreeLongitude, DegreeLatitude]
) -> Tuple[MetreLongitude, MetreLatitude]:
    return metre_geoseries(t)[0].coords[0]


def metre_geoseries(t: Tuple[DegreeLongitude, DegreeLatitude]) -> gpd.GeoSeries:
    s = gpd.GeoSeries(Point(t))
    s.crs = degree_crs
    return s.to_crs(metre_crs)


def buffer(t: Tuple[DegreeLatitude, DegreeLongitude], d: float) -> BoundingBox:
    m = metre_geoseries(swap(t))
    buffer = m.buffer(d)
    return tuple(buffer.bounds.loc[0])


def nearby_road_segment(
    t: DegreeLatLon, distance: float
) -> Dict[Tuple[str, Optional[str]], List[LatLon]]:
    box = buffer(t, distance)
    box_string = ",".join([str(c) for c in box])
    xml = requests.get(
        "https://www.openstreetmap.org/api/0.6/map?bbox=-8.558006,51.892098,-8.557774,51.892242",
        params={"bbox": box_string},
    ).text
    soup = BeautifulSoup(xml, "xml")
    nodes = {n["id"]: n for n in soup.osm("node")}
    way_nodes = ((w, [nodes[nd["ref"]] for nd in w("nd")]) for w in soup.osm("way"))
    return {
        (w["id"], omap(itemgetter("v"), w.find(k="name"))): [
            (n["lat"], n["lon"]) for n in ns
        ]
        for (w, ns) in way_nodes
    }

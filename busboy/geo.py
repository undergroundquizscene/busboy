from operator import itemgetter
from typing import Any, Dict, List, NewType, Optional, Tuple, TypeVar

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from shapely.geometry import Point

from busboy.util import omap, swap

RawLatitude = NewType("RawLatitude", int)
RawLongitude = NewType("RawLongitude", int)
DegreeLongitude = NewType("DegreeLongitude", float)
DegreeLatitude = NewType("DegreeLatitude", float)
LonLat = Tuple[DegreeLongitude, DegreeLatitude]
LatLon = Tuple[DegreeLatitude, DegreeLongitude]
MetreLongitude = NewType("MetreLongitude", float)
MetreLatitude = NewType("MetreLatitude", float)
BoundingBox = Tuple[DegreeLongitude, DegreeLatitude, DegreeLongitude, DegreeLatitude]


degree_crs = {"init": "epsg:4326"}
metre_crs = {"init": "epsg:29902"}

import pandas as pd
import geopandas as gpd
import numpy as np
import geopy.distance as gpd
from collections import namedtuple

from typing import Tuple, Any

Latitude = float
Longitude = float
Coord = Tuple[Latitude, Longitude]

def stop_distance(r: Any, stop: Coord) -> float:
    return gpd.distance(stop, (r.latitude, r.longitude)).m

def stop_distances(df: pd.DataFrame, stop: Coord) -> pd.DataFrame:
    df2 = df.copy()
    df2["stop_distance"] = [stop_distance(r, stop) for r in df.itertuples()]
    return df2

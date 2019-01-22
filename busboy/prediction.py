from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, List, NewType, Tuple, cast

import geopandas as gpd
import geopy.distance as gpd
import numpy as np
import pandas as pd

import busboy.database as db
import busboy.model as m
import busboy.constants as c

Latitude = float
Longitude = float
Coord = Tuple[Latitude, Longitude]
DistanceVector = NewType("DistanceVector", Tuple[float, float])


def stop_distance(r: Any, stop: Coord) -> float:
    return gpd.distance(stop, (r.latitude, r.longitude)).m


def stop_distances(df: pd.DataFrame, stop: Coord) -> pd.DataFrame:
    df2 = df.copy()
    df2["stop_distance"] = [stop_distance(r, stop) for r in df.itertuples()]
    return df2


def stop_times_220(df: pd.DataFrame) -> pd.DataFrame:
    """Given the dataframe for a 220 trip, work out the times it reached each stop."""
    dfs = []
    for s in c.stops_on_220:
        if s is not None:
            ndf = stop_distances(df, (s.latitude, s.longitude))
            ndf = ndf[ndf["stop_distance"] < 100]
            include_stop(ndf, s)
            dfs.append(ndf)
    return pd.concat(dfs)


def closest_stops_220(df: pd.DataFrame) -> pd.DataFrame:
    """Given the dataframe for a 220 trip, work out the closest stop for the bus at each point."""
    df["closest_stop"] = [
        closest_stop(r.latitude, r.longitude, c.stops_on_220) for r in df.itertuples()
    ]
    return df


def closest_stop(latitude: float, longitude: float, stops: List[m.Stop]) -> m.Stop:
    return min(
        stops,
        key=lambda s: gpd.distance((s.latitude, s.longitude), (latitude, longitude)),
    )


def include_stop(df: pd.DataFrame, s: m.Stop) -> pd.DataFrame:
    df["stop_id"] = s.id
    df["stop_name"] = s.name
    return df


def new_stop_distance(e: db.DatabaseEntry, s: m.Stop) -> float:
    return gpd.distance((e.latitude, e.longitude), (s.latitude, s.longitude))


def new_stop_distances(es: List[db.DatabaseEntry], s: m.Stop) -> List[float]:
    return [new_stop_distance(e, s) for e in es]


def distance_vector(c1: Coord, c2: Coord) -> DistanceVector:
    """A naive cartesian distance vector between two lon-lat coordinates in metres."""
    mid = (c2[0], c1[1])
    abs_x = gpd.distance(c1, mid).m
    abs_y = gpd.distance(mid, c2).m
    if c2[0] >= c1[0]:
        x = abs_x
    else:
        x = -abs_x
    if c2[1] >= c1[1]:
        y = abs_y
    else:
        y = -abs_y
    return cast(DistanceVector, (x, y))


def unit_vector(vector):
    """The unit vector of a vector.

    From: https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python#13849249
    """
    return vector / np.linalg.norm(vector)


def angle_between(v1: DistanceVector, v2: DistanceVector) -> float:
    """The angle in radians between two vectors.

    From: https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python#13849249
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

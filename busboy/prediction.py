from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Any, Dict, Iterable, List, NewType, Tuple, cast

import geopy.distance as gpd
import numpy as np
import pandas as pd
import shapely.geometry as sg
from shapely.geometry import LineString

import busboy.constants as c
import busboy.database as db
import busboy.model as m
import busboy.util as u
from busboy.util import Just, Maybe, Nothing

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


@dataclass(frozen=True)
class RouteSection(object):
    s1: m.Stop
    s2: m.Stop
    polygon: sg.Polygon


def route_sections(stops: List[m.Stop], width: float) -> List[RouteSection]:
    lss = [
        (
            s1,
            s2,
            cast(
                LineString,
                sg.MultiPoint([s1.lat_lon, s2.lat_lon]).minimum_rotated_rectangle,
            ),
        )
        for s1, s2 in u.pairwise(stops)
    ]
    return [
        RouteSection(
            s1,
            s2,
            sg.MultiLineString(
                [
                    ls,
                    ls.parallel_offset(width, "left"),
                    ls.parallel_offset(width, "right"),
                ]
            ).minimum_rotated_rectangle,
        )
        for s1, s2, ls in lss
    ]


def assign_region(
    sections: List[RouteSection], stops: List[m.Stop], e: db.DatabaseEntry
) -> Tuple[db.DatabaseEntry, List[RouteSection]]:
    return (e, [s for s in sections if s.polygon.contains(e.point)])


def assign_regions(
    es: List[db.DatabaseEntry], stops: List[m.Stop]
) -> List[Tuple[db.DatabaseEntry, List[RouteSection]]]:
    rs = route_sections(stops, 0.001)
    return [assign_region(rs, stops, e) for e in es]


def most_recent_stops(
    ts: Iterable[Tuple[db.DatabaseEntry, List[RouteSection]]]
) -> Iterable[Tuple[db.DatabaseEntry, Maybe[m.Stop]]]:
    def choose_stop(rs: List[RouteSection]) -> Maybe[m.Stop]:
        if len(rs) == 0:
            return Nothing()
        elif len(rs) == 1:
            return Just(rs[0].s1)
        elif rs[0].s2 == rs[1].s1:
            return Just(rs[0].s2)
        else:
            return Just(rs[0].s1)

    return ((e, choose_stop(rs)) for e, rs in ts)

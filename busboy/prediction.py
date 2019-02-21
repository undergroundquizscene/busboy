from collections import defaultdict, namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial, singledispatch
from itertools import dropwhile
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    NewType,
    Optional,
    Set,
    Tuple,
    cast,
    overload,
)

import geopy.distance as gpd
import numpy as np
import pandas as pd
import shapely.geometry as sg
from shapely.geometry import LineString, Point

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m
import busboy.util as u
from busboy.geo import Latitude, Longitude, to_metre_point
from busboy.util import Just, Maybe, Nothing, first, pairwise

Coord = Tuple[Latitude, Longitude]
DistanceVector = NewType("DistanceVector", Tuple[float, float])


def pd_stop_distance(r: Any, stop: Coord) -> float:
    return gpd.distance(stop, (r.latitude, r.longitude)).m


def pd_stop_distances(df: pd.DataFrame, stop: Coord) -> pd.DataFrame:
    df2 = df.copy()
    df2["stop_distance"] = [pd_stop_distance(r, stop) for r in df.itertuples()]
    return df2


def stop_times_220(df: pd.DataFrame) -> pd.DataFrame:
    """Given the dataframe for a 220 trip, work out the times it reached each stop."""
    dfs = []
    for s in c.stops_on_220:
        if s is not None:
            ndf = pd_stop_distances(df, (s.latitude, s.longitude))
            ndf = ndf[ndf["stop_distance"] < 100]
            include_stop(ndf, s)
            dfs.append(ndf)
    return pd.concat(dfs)


def closest_stops_220(df: pd.DataFrame) -> pd.DataFrame:
    """Given the dataframe for a 220 trip, work out the closest stop for the bus at each point."""
    df["closest_stop"] = [
        closest_stop_gpd(r.latitude, r.longitude, c.stops_on_220)
        for r in df.itertuples()
    ]
    return df


def closest_stop_gpd(latitude: float, longitude: float, stops: List[m.Stop]) -> m.Stop:
    return min(
        stops,
        key=lambda s: gpd.distance((s.latitude, s.longitude), (latitude, longitude)),
    )


def include_stop(df: pd.DataFrame, s: m.Stop) -> pd.DataFrame:
    df["stop_id"] = s.id
    df["stop_name"] = s.name
    return df


def new_stop_distance(e: db.BusSnapshot, s: m.Stop) -> float:
    return gpd.distance((e.latitude, e.longitude), (s.latitude, s.longitude))


def new_stop_distances(es: List[db.BusSnapshot], s: m.Stop) -> List[float]:
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

    def contains(self, lon: Longitude, lat: Latitude) -> bool:
        return self.polygon.contains(Point(lat, lon))


def route_sections(stops: Iterable[m.Stop], width: float = 0.001) -> List[RouteSection]:
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
    sections: Iterable[RouteSection], e: db.BusSnapshot
) -> Tuple[db.BusSnapshot, List[RouteSection]]:
    return (e, [s for s in sections if s.polygon.contains(e.point)])


def assign_regions(
    rs: Iterable[RouteSection], es: Iterable[db.BusSnapshot]
) -> Generator[Tuple[db.BusSnapshot, List[RouteSection]], None, None]:
    return (assign_region(rs, e) for e in es)


def most_recent_stops(
    ts: Iterable[Tuple[db.BusSnapshot, List[RouteSection]]]
) -> Iterable[Tuple[db.BusSnapshot, Maybe[m.Stop]]]:
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


def possible_variants(
    snapshots: Iterable[db.BusSnapshot], timetables: Set[api.TimetableVariant]
) -> Iterable[Tuple[db.BusSnapshot, Set[Tuple[api.TimetableVariant, int]]]]:
    sections = {tv: route_sections(tv.stops) for tv in timetables}
    for snapshot in snapshots:
        positions = set()
        for tv, rs in sections.items():
            for i, section in enumerate(rs):
                if section.contains(snapshot.longitude, snapshot.latitude):
                    positions.add((tv, i))
        yield (snapshot, positions)


def check_variant_order(
    snapshots: List[Tuple[db.BusSnapshot, Set[Tuple[api.TimetableVariant, int]]]]
) -> Iterable[Tuple[db.BusSnapshot, Set[Tuple[api.TimetableVariant, int]]]]:
    for i, (snapshot, positions) in enumerate(snapshots):
        output_positions: Set[Tuple[api.TimetableVariant, int]] = set()
        for variant, position in positions:
            later_positions = map(lambda j: snapshots[j][1], range(i, len(snapshots)))
            first_change_positions = dict(
                first(
                    dropwhile(
                        lambda ps: len(ps) == 0 or (variant, position) in ps,
                        later_positions,
                    )
                ).get([])
            )
            if (
                variant in first_change_positions
                and first_change_positions[variant] > position
            ):
                output_positions.add((variant, position))
        yield (snapshot, output_positions)


def duplicate_positions(s1: db.BusSnapshot, s2: db.BusSnapshot) -> bool:
    return (s1.poll_time, s1.latitude, s1.longitude) == (
        s2.poll_time,
        s2.latitude,
        s2.longitude,
    )


def drop_duplicate_positions(
    snapshots: Iterable[db.BusSnapshot],
    duplicates: Callable[
        [db.BusSnapshot, db.BusSnapshot], bool
    ] = duplicate_positions,
) -> Iterator[db.BusSnapshot]:
    last = None
    for this in snapshots:
        if last is None or not duplicates(last, this):
            yield this
        last = this


def stop_times(
    snapshots: List[Tuple[db.BusSnapshot, Dict[api.TimetableVariant, Set[int]]]]
) -> Dict[api.TimetableVariant, Dict[int, List[Tuple[datetime, datetime]]]]:
    all_variants = {t for (_, vs) in snapshots for t in vs}
    lasts: Dict[api.TimetableVariant, Dict[int, datetime]] = defaultdict(dict)
    output: Dict[
        api.TimetableVariant, Dict[int, List[Tuple[datetime, datetime]]]
    ] = defaultdict(dict)
    for snapshot in snapshots:
        for variant in all_variants:
            these_positions = snapshot[1].get(variant)
            last_positions = lasts.get(variant)
            if these_positions is not None:
                if last_positions is not None:
                    positions_to_clear = []
                    for (position, time) in last_positions.items():
                        if position not in these_positions:
                            output[variant].setdefault(position + 1, []).append(
                                (time, snapshot[0].poll_time)
                            )
                            positions_to_clear.append(position)
                    for position in positions_to_clear:
                        del last_positions[position]
                for position in these_positions:
                    lasts[variant][position] = snapshot[0].poll_time
    return output


def travel_times(
    arrival_times: Dict[int, List[Tuple[datetime, datetime]]]
) -> Iterator[Tuple[Tuple[int, int], List[Tuple[timedelta, timedelta]]]]:
    """The travel times between adjacent stops.

    Each travel time is represented as a (min, max) pair.
    """
    for first, second in pairwise(sorted(arrival_times.items(), key=lambda t: t[0])):
        first_position, first_times = first
        second_position, second_times = second
        travel_times = [
            travel_window((start, end), next_time)
            for start, end in first_times
            for next_time in (min(second_times, key=lambda time: time[0] - end),)
        ]
        yield ((first_position, second_position), travel_times)


def travel_window(
    window1: Tuple[datetime, datetime], window2: Tuple[datetime, datetime]
) -> Tuple[timedelta, timedelta]:
    """The (min, max) travel times between two arrival windows.

    If I arrived at 1 between 2 and 3, and arrived at 2 between 4 and 6,
    the travel window is: (4 - 3, 6 - 2)
    """
    return (window2[0] - window1[1], window2[1] - window1[0])


def stop_times_proximity(
    snapshots: Iterable[db.BusSnapshot],
    stops: Iterable[m.Stop],
    distance_limit: float = 100,
) -> Iterator[Tuple[m.Stop, datetime]]:
    for snapshot in snapshots:
        for stop in stops:
            distance = stop_distance_geopandas(snapshot, stop)
            if distance < distance_limit:
                yield (stop, snapshot.poll_time)


def stop_distance_geopandas(snapshot: db.BusSnapshot, stop: m.Stop) -> float:
    snapshot_point = to_metre_point((snapshot.longitude, snapshot.latitude))
    stop_point = to_metre_point((stop.longitude, stop.latitude))
    return snapshot_point.distance(stop_point)

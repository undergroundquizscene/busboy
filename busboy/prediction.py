from __future__ import annotations

from collections import defaultdict, namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial, reduce, singledispatch
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
    Union,
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
from busboy.util import Just, Maybe, Nothing, drop, first, pairwise, tuplewise_padded

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


RouteSection = Union["RoadSection", "StopCircle"]


@dataclass(frozen=True)
class AbstractRouteSection(object):
    polygon: sg.Polygon

    def contains(self, lon: Longitude, lat: Latitude) -> bool:
        return self.polygon.contains(Point(lat, lon))


@dataclass(frozen=True)
class RoadSection(AbstractRouteSection):
    def difference(self, circle: StopCircle) -> Maybe[RoadSection]:
        new_polygon = self.polygon.difference(circle.polygon)
        if isinstance(new_polygon, sg.Polygon):
            return Just(RoadSection(new_polygon))
        else:
            return Nothing()


@dataclass(frozen=True)
class StopCircle(AbstractRouteSection):
    stop: m.Stop


def route_sections(
    stops: Iterable[m.Stop],
    rectangle_width: float = 0.001,
    circle_radius: float = 0.001,
) -> Iterator[RouteSection]:
    def make_circle(stop: m.Stop) -> StopCircle:
        return StopCircle(
            cast(sg.Polygon, sg.Point(stop.lat_lon).buffer(circle_radius)), stop
        )

    def shapes() -> Iterator[RouteSection]:
        for s1, s2 in pairwise(stops):
            yield make_circle(s1)
            yield RoadSection(
                widen_line(
                    cast(
                        LineString,
                        sg.MultiPoint(
                            [s1.lat_lon, s2.lat_lon]
                        ).minimum_rotated_rectangle,
                    ),
                    rectangle_width,
                )
            )
        yield make_circle(s2)

    for section1, section2, section3 in drop(
        1, (tuplewise_padded(3, (Just(x) for x in shapes()), pad_value=Nothing()))
    ):
        if isinstance(section2, Just):
            if isinstance(section2.value, RoadSection):
                if isinstance(section1, Just) and isinstance(
                    section1.value, StopCircle
                ):
                    section2 = section2.value.difference(section1.value)
                if isinstance(section3, Just) and isinstance(
                    section3.value, StopCircle
                ):
                    section2 = section2.bind(lambda s: s.difference(section3.value))
        if isinstance(section2, Just):
            yield section2.value


def widen_line(linestring: sg.LineString, width: float) -> sg.Polygon:
    linestrings = [
        linestring,
        linestring.parallel_offset(width, "left"),
        linestring.parallel_offset(width, "right"),
    ]
    return sg.MultiLineString(linestrings).minimum_rotated_rectangle


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
    sections = {tv: list(route_sections(tv.stops)) for tv in timetables}
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
                ).or_else([])
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
    duplicates: Callable[[db.BusSnapshot, db.BusSnapshot], bool] = duplicate_positions,
) -> Iterator[db.BusSnapshot]:
    last = None
    for this in snapshots:
        if last is None or not duplicates(last, this):
            yield this
        last = this


EntryWindow = Tuple[Maybe[datetime], Maybe[datetime]]
ExitWindow = Tuple[Maybe[datetime], Maybe[datetime]]
SectionTime = NewType("SectionTime", Tuple[int, EntryWindow, ExitWindow])


def section_times(
    snapshots: List[Tuple[db.BusSnapshot, Dict[api.TimetableVariant, Set[int]]]],
    sections: Dict[api.TimetableVariant, List[RouteSection]],
) -> Dict[api.TimetableVariant, List[SectionTime]]:
    """Calculates entry and exit times for each section in snapshots.

    Currently misses the last section seen in a route, and I’m not sure why.

    Arguments:
        snapshots: The bus snapshots, each with, for each timetable variant,
            the sections that snapshot falls in.
        sections: The sections in each timetable variant (in order).

    Returns:
        For each timetable variant, the route sections that were entered and
        exited in snapshots, in order of exit.
    """
    section_windows: Dict[api.TimetableVariant, List[SectionTime]] = defaultdict(list)
    sections_entered: Dict[Tuple[api.TimetableVariant, int], EntryWindow] = {}
    last_positions: Dict[api.TimetableVariant, Set[int]] = {}
    last_time: Maybe[datetime] = Nothing()
    for snapshot, positions in snapshots:
        update_positions = False
        for variant, these_positions in positions.items():
            if not these_positions:
                continue
            else:
                update_positions = True
            for position in these_positions.difference(
                last_positions.get(variant, set())
            ):
                window = (last_time, Just(snapshot.poll_time))
                sections_entered[(variant, position)] = window
            for position in last_positions.get(variant, set()).difference(
                these_positions
            ):
                exit_interval = last_time, Just(snapshot.poll_time)
                section_time = SectionTime(
                    (position, sections_entered[(variant, position)], exit_interval)
                )
                section_windows[variant].append(section_time)
        if update_positions:
            last_positions = positions
            last_time = Just(snapshot.poll_time)
    return section_windows


def journeys(
    section_times: Dict[api.TimetableVariant, List[SectionTime]]
) -> Dict[api.TimetableVariant, List[List[SectionTime]]]:
    """Splits a vehicle’s positions on a timetable into journeys from start to
    end.
    """
    Accumulator = NewType(
        "Accumulator", Tuple[int, List[SectionTime], List[List[SectionTime]]]
    )

    def f(acc: Accumulator, x: SectionTime) -> Accumulator:
        position, _, _ = x
        last_position, this_journey, journeys = acc
        if position < last_position:
            return Accumulator((position, [x], journeys + [this_journey]))
        else:
            return Accumulator((position, this_journey + [x], journeys))

    return {
        v: reduce(f, ts, Accumulator((0, [], [])))[2] for v, ts in section_times.items()
    }
    # journeys = []
    # this_journey: List[Tuple[int, EntryWindow, ExitWindow]] = []
    # last_position = 0
    # for position, entry, exit in times:
    #     if position < last_position:
    #         journeys.append(this_journey)
    #         this_journey = []
    #     this_journey.append((position, entry, exit))
    #     last_position = position
    # output[variant] = journeys


def pad_journeys(
    variant_journeys: Dict[api.TimetableVariant, List[List[SectionTime]]]
) -> Dict[api.TimetableVariant, List[List[SectionTime]]]:
    """Fill in missing sections in journeys."""
    output = {}
    for variant, journeys in variant_journeys.items():
        output_journeys = []
        for journey in journeys:
            output_journey: List[SectionTime] = []
            last_position = 0
            last_exit: ExitWindow = (Nothing(), Nothing())
            for time in journey:
                position, entry, exit = time
                for missing_position in range(last_position + 1, position):
                    output_journey.append(
                        SectionTime(
                            (
                                missing_position,
                                (last_exit[0], Nothing()),
                                (Nothing(), last_exit[1]),
                            )
                        )
                    )
                output_journey.append(time)
                last_position = position
                last_exit = exit
            output_journeys.append(output_journey)
        output[variant] = output_journeys
    return output


def stop_times(
    snapshots: List[Tuple[db.BusSnapshot, Dict[api.TimetableVariant, Set[int]]]],
    sections: Dict[api.TimetableVariant, List[RouteSection]],
) -> Dict[
    api.TimetableVariant, List[List[Tuple[Optional[datetime], Optional[datetime]]]]
]:
    section_windows: Dict[api.TimetableVariant, List[List[SectionTime]]] = pad_journeys(
        journeys(section_times(snapshots, sections))
    )
    output: Dict[
        api.TimetableVariant, List[List[Tuple[Optional[datetime], Optional[datetime]]]]
    ] = {}
    last_exit: Optional[ExitWindow] = None
    last_position = 0
    for variant, windows in section_windows.items():
        variant_sections = sections[variant]
        for position, entry, exit in windows:
            # advance (with recording) variant_sections to match position
            if last_position > position:
                trips = output.setdefault(variant, [[]])
                for section in variant_sections[last_position:-1]:
                    if isinstance(section, StopCircle):
                        trips[-1].append(
                            (last_exit[0] if last_exit is not None else last_exit, None)
                        )
                trips.append([])
                last_position = 0
            for section in variant_sections[last_position:position]:
                if isinstance(section, StopCircle):
                    output.setdefault(variant, [[]])[-1].append(
                        (last_exit[0] if last_exit is not None else last_exit, entry[1])
                    )
            section = sections[variant][position]
            if isinstance(section, StopCircle):
                output.setdefault(variant, [[]])[-1].append((entry[1], exit[0]))
            last_exit = exit
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

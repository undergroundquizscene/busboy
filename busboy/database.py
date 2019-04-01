from __future__ import annotations

import datetime as dt
import json
from dataclasses import InitVar, dataclass, field, fields
from datetime import date, datetime
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union, cast

import geopandas as gpd
import pandas as pd
import psycopg2 as pp2
import shapely.geometry as sg
from psycopg2.extensions import connection, cursor

import busboy.apis as api
import busboy.geo as g
import busboy.model as m
from busboy.apis import Timetable, TimetableVariant
from busboy.constants import stops_by_route
from busboy.geo import DegreeLatitude, DegreeLongitude
from busboy.model import Passage, Route, RouteId, Stop, StopId, TripId
from busboy.util import Either, Just, Left, Maybe, Nothing, Right


def default_connection() -> connection:
    return pp2.connect("dbname=busboy user=Noel")


def test_connection() -> connection:
    return pp2.connect(dbname="busboy-test", user="Noel")


def snapshots(
    connection: Optional[connection] = None,
    r: Optional[m.RouteId] = None,
    d: Optional[date] = None,
    date_span: Optional[Tuple[date, date]] = None,
) -> List[BusSnapshot]:
    """Gets entries from the database, optionally filtering by route or date."""
    if connection is None:
        connection = default_connection()
    with connection.cursor() as cu:
        query = b"select * from passage_responses"
        conditions: List[bytes] = []
        if r is not None:
            conditions.append(cu.mogrify(" route_id = %s", (r.raw,)))
        if d is not None or date_span is not None:
            if date_span is not None:
                dt1, dt2 = day_span(list(date_span))
            elif d is not None:
                dt1, dt2 = day_span([d])

            conditions.append(
                cu.mogrify(" last_modified between %s and %s", (dt1, dt2))
            )
        if conditions != []:
            query += b" where" + b" and".join(conditions)
        cu.execute(query)
        return [BusSnapshot.from_db_row(row) for row in cu.fetchall()]


def snapshots_df(
    connection: Optional[connection] = None,
    route: Optional[m.RouteId] = None,
    day: Optional[date] = None,
    date_span: Optional[Tuple[date, date]] = None,
) -> pd.DataFrame:
    df = snapshots(connection, route, day, date_span)
    return pd.DataFrame(map(lambda s: s.as_dict(), df))


def poll_times_df(connection: Maybe[connection] = Nothing(),) -> pd.DataFrame:
    with connection.or_else_lazy(default_connection) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "select distinct poll_time from passage_responses order by poll_time asc"
            )
            return pd.DataFrame(cursor.fetchall(), columns=["poll_time"])


def data_gdf(
    connection: Optional[connection] = None,
    r: Optional[m.RouteId] = None,
    d: Optional[date] = None,
) -> pd.DataFrame:
    snapshots = snapshots(connection, r, d)
    df = pd.DataFrame([snapshot.as_dict() for snapshot in snapshots])
    df["Snapshot"] = snapshots
    df["Coordinates"] = list(zip(df["longitude"], df["latitude"]))
    df["Coordinates"] = df["Coordinates"].apply(sg.Point)
    df = df.set_index("last_modified")
    return gpd.GeoDataFrame(df, geometry="Coordinates")


def store_route(r: Route, conn: Optional[connection] = None) -> Optional[Exception]:
    if conn is None:
        conn = default_connection()
    with conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    insert into routes (
                        id, name, direction, number, category
                    ) values (
                        %s, %s, %s,
                        %s, %s)
                    """,
                    [r.id.raw, r.name, r.direction, r.number, r.category],
                )
                return None
            except Exception as e:
                return e


def store_stop(r: Stop, conn: Optional[connection] = None) -> None:
    if conn is None:
        conn = default_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into stops (
                    id, name, latitude, longitude, number
                ) values (
                    %s, %s, %s, %s, %s)
                """,
                [r.id, r.name, r.latitude, r.longitude, r.number],
            )


def store_trip(
    p: Passage, poll_time: dt.datetime, connection: Optional[connection] = None
) -> Optional[Exception]:
    if connection is None:
        try:
            connection = default_connection()
        except Exception as e:
            return e
    with connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into passage_responses(
                        last_modified, trip_id, route_id, vehicle_id, pattern_id,
                        latitude, longitude, bearing, is_accessible, has_bike_rack,
                        direction, congestion_level, accuracy_level, status, category,
                        poll_time
                    ) values (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        p.last_modified,
                        p.trip,
                        p.route,
                        p.vehicle,
                        p.pattern,
                        p.latitude,
                        p.longitude,
                        p.bearing,
                        p.is_accessible,
                        p.has_bike_rack,
                        p.direction,
                        p.congestion,
                        p.accuracy,
                        p.status,
                        p.category,
                        poll_time,
                    ],
                )
                return None
        except Exception as e:
            return e


def store_timetables() -> None:
    sbn = stops_by_name()
    rbn = routes_by_name()
    conn = default_connection()
    for route in stops_by_route:
        for timetable in api.timetables(route, sbn):
            store_timetable(timetable, rbn[route].id, conn)


def store_timetable(
    timetable: Timetable, route: RouteId, conn: Optional[connection] = None
) -> None:
    if conn is None:
        conn = default_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into timetables (caption) values (%s) returning id
                """,
                [timetable.caption],
            )
            row = cast(Tuple[Any, ...], cursor.fetchone())
            timetable_id = row[0]
            cursor.execute(
                """
                insert into route_timetables (route, timetable)
                values (%s, %s)
                """,
                [route.raw, timetable_id],
            )
            for variant in timetable.variants:
                cursor.execute(
                    """
                    insert into timetable_variants (route_name, timetable_id)
                    values (%s, %s) returning id
                    """,
                    [variant.route.strip(), timetable_id],
                )
                variant_id = cast(Tuple[Any, ...], cursor.fetchone())[0]
                for position, stop in enumerate(variant.stops):
                    cursor.execute(
                        """
                        insert into variant_stops (position, variant, stop)
                        values (%s, %s, %s)
                        """,
                        [position, variant_id, stop.id.raw],
                    )


def timetables(
    route: RouteId, connection: Maybe[connection] = Nothing()
) -> Iterator[Either[str, Timetable]]:
    """Gets the timetables for a specific route from the database."""
    with connection.or_else_lazy(default_connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                select timetable from route_timetables
                where route = %s
                """,
                [route.raw],
            )
            for (timetable_id,) in cursor.fetchall():
                yield timetable(timetable_id, Just(conn))


def timetable(
    timetable_id: int, connection: Maybe[connection] = Nothing()
) -> Either[str, Timetable]:
    with connection.or_else_lazy(default_connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                select caption from timetables
                where id = %s
                """,
                [timetable_id],
            )
            result = cursor.fetchone()
            if result is None:
                return Left(f"Timetable {timetable_id} not in database")
            caption = result[0]
            cursor.execute(
                """
                select id from timetable_variants
                where timetable_id = %s
                """,
                [timetable_id],
            )
            variants = (
                timetable_variant(id, Just(conn)) for (id,) in cursor.fetchall()
            )
            return Right(
                Timetable(caption, {v.value for v in variants if isinstance(v, Right)})
            )


def timetable_variant(
    variant_id: int, connection: Maybe[connection] = Nothing()
) -> Either[str, TimetableVariant]:
    with connection.or_else_lazy(default_connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                select route_name from timetable_variants
                where id = %s
                """,
                [variant_id],
            )
            variant_row = cursor.fetchone()
            if variant_row is None:
                return Left(f"Variant {variant_id} not in database")
            route_name = variant_row[0]
            cursor.execute(
                """
                select stop from variant_stops
                where variant = %s
                order by position asc
                """,
                [variant_id],
            )
            stop_ids = (stop for (stop,) in cursor.fetchall())
            stops = tuple(stop_by_id(conn, StopId(s)) for s in stop_ids)
            if all(map(lambda s: isinstance(s, Just), stops)):
                just_stops = cast(Tuple[Just[Stop], ...], stops)
                return Right(
                    TimetableVariant(route_name, tuple(s.value for s in just_stops))
                )
            else:
                return Left("Error in database, stop in variant_stops but not in stops")


def test_database() -> None:
    with test_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into messages
                values (%s)
                """,
                ["hello!"],
            )


def routes() -> List[Route]:
    j = json.load(
        open(
            "/Users/Noel/Developer/Projects/Busboy/resources/example-responses/routes.json"
        )
    )
    rs = j["routeTdi"]
    return [Route.from_json(r) for k, r in rs.items() if k != "foo"]


def routes_by_name() -> Dict[str, Route]:
    return {r.name: r for r in routes()}


def routes_by_id() -> Dict[m.RouteId, Route]:
    return {r.id: r for r in routes()}


def trip_points(connection: connection, t: TripId) -> TripPoints:
    with connection as co:
        with co.cursor() as cu:
            cu.execute(
                """
                select latitude, longitude, last_modified from passage_responses
                where trip_id = %s
                """,
                [t.raw],
            )
            tps = [TripPoint(r[0], r[1], r[2]) for r in cu.fetchall()]
            return TripPoints(t, tps)


@dataclass
class TripPoints(object):
    id: m.TripId
    points: List[TripPoint]

    def to_json(self) -> Dict[str, Any]:
        return {"id": self.id.raw, "points": [p.to_json() for p in self.points]}


@dataclass
class TripPoint(object):
    latitude: int
    longitude: int
    time: datetime

    def to_json(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "time": self.time.isoformat(),
        }


@dataclass(frozen=True)
class BusSnapshot(object):
    last_modified: datetime
    trip: m.TripId
    route: m.RouteId
    vehicle: m.VehicleId
    pattern: m.PatternId
    latitude: g.DegreeLatitude
    longitude: g.DegreeLongitude
    bearing: int
    is_accessible: bool
    has_bike_rack: bool
    direction: int
    congestion_level: int
    accuracy_level: int
    status: int
    category: int
    poll_time: datetime
    point: sg.Point

    @staticmethod
    def from_db_row(row: Tuple[Any, ...]) -> BusSnapshot:
        latitude = g.DegreeLatitude(cast(int, row[9]) / 3_600_000)
        longitude = g.DegreeLongitude(cast(int, row[10]) / 3_600_000)
        return BusSnapshot(
            route=m.RouteId(cast(str, row[0])),
            direction=cast(int, row[1]),
            vehicle=m.VehicleId(cast(str, row[2])),
            last_modified=cast(datetime, row[3]),
            trip=m.TripId(cast(str, row[4])),
            congestion_level=cast(int, row[5]),
            accuracy_level=cast(int, row[6]),
            status=cast(int, row[7]),
            is_accessible=cast(bool, row[8]),
            latitude=latitude,
            longitude=longitude,
            bearing=cast(int, row[11]),
            pattern=m.PatternId(cast(str, row[12])),
            has_bike_rack=cast(bool, row[13]),
            category=cast(int, row[14]),
            poll_time=cast(datetime, row[15]),
            point=sg.Point(latitude, longitude),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {f.name: self.__dict__[f.name] for f in fields(self)}

    @staticmethod
    def from_passage(passage: Passage, time: datetime) -> BusSnapshot:
        longitude = passage.longitude.map(lambda l: l / 3_600_000)
        latitude = passage.latitude.map(lambda l: l / 3_600_000)
        point = longitude.bind(lambda lon: latitude.map(lambda lat: sg.Point(lat, lon)))
        return BusSnapshot(
            last_modified=passage.last_modified.or_else(None),
            trip=passage.trip.or_else(None),
            route=passage.route.or_else(None),
            vehicle=passage.vehicle.or_else(None),
            pattern=passage.pattern.or_else(None),
            latitude=latitude.or_else(None),
            longitude=longitude.or_else(None),
            bearing=passage.bearing.or_else(None),
            is_accessible=passage.is_accessible.or_else(None),
            has_bike_rack=passage.has_bike_rack.or_else(None),
            direction=passage.direction.or_else(None),
            congestion_level=passage.congestion.or_else(None),
            accuracy_level=passage.accuracy.or_else(None),
            status=passage.status.or_else(None),
            category=passage.category.or_else(None),
            poll_time=time,
            point=point.or_else(None),
        )


def trips_on_day(c: connection, d: date, r: Optional[str] = None) -> Set[TripId]:
    with c.cursor() as cu:
        midnight = dt.time()
        day = dt.timedelta(days=1)
        dt1 = datetime.combine(d, midnight)
        dt2 = datetime.combine(d + day, midnight)
        query = cu.mogrify(
            """
            select trip_id from passage_responses
            where last_modified between %s and %s
            """,
            (dt1, dt2),
        )
        if r is not None:
            query += cu.mogrify(" and route_id = %s", (r,))
        cu.execute(query)
        return {TripId(row[0]) for row in cu.fetchall()}


def day_span(dates: List[date]) -> Tuple[datetime, datetime]:
    """Creates a datetime span from a list of dates.

    Input list must not be empty.
    """
    midnight = dt.time()
    day = dt.timedelta(days=1)
    dt1 = datetime.combine(dates[0], midnight)
    dt2 = datetime.combine(dates[-1] + day, midnight)
    return dt1, dt2


def stops_by_route_name(c: connection, route: str) -> List[m.Stop]:
    with c.cursor() as cu:
        cu.execute(
            """
            select s.id, s.name, s.latitude, s.longitude, s.number from
            stops as s,
            route_stops as rs,
            routes as r
            where s.id = rs.stop and rs.route = r.id
            and r.name = %s
            """,
            [route],
        )
        return [Stop.from_db_row(r) for r in cu.fetchall()]


def stop_by_name(name: str) -> Optional[Stop]:
    with open("resources/example-responses/busStopPoints.json") as f:
        j = json.load(f)
        for k, bs in j["bus_stops"].items():
            if bs["name"] == name:
                return Stop.from_json(bs)
        return None


def stop_by_id(c: connection, s: m.StopId) -> Maybe[Stop]:
    with c.cursor() as cu:
        cu.execute(
            """
            select * from stops
            where id = %s
            """,
            [s.raw],
        )
        return Maybe.of(cu.fetchone()).map(Stop.from_db_row)


def stops(c: Optional[connection] = None) -> List[Stop]:
    """Retrieves a list of all stops from the database."""
    if c is None:
        c = default_connection()
    with c.cursor() as cu:
        cu.execute("select * from stops")
        return [Stop.from_db_row(r) for r in cu.fetchall()]


def stops_by_name(c: Optional[connection] = None) -> Dict[str, Stop]:
    return {s.name: s for s in stops(c)}

import psycopg2 as pp2
from psycopg2.extensions import cursor, connection
from typing import Optional, List, Dict, Any, Set, Tuple, cast, Union
import json
from dataclasses import dataclass, InitVar, field, fields
from datetime import date, datetime
import datetime as dt
import pandas as pd
import geopandas as gpd
import shapely.geometry as sg
import json

from busboy.model import Route, Stop, Passage, TripId, IncompleteRoute
import busboy.model as m


def default_connection() -> connection:
    return pp2.connect("dbname=busboy user=Noel")


def test_connection() -> connection:
    return pp2.connect(dbname="busboy-test", user="Noel")


def trip_data(
    connection: Optional[connection] = None,
    r: Optional[m.RouteId] = None,
    d: Optional[date] = None,
) -> List["TripEntry"]:
    if connection is None:
        connection = default_connection()
    with connection.cursor() as cu:
        query = b"select * from passage_responses"
        conditions: List[bytes] = []
        if r is not None:
            conditions.append(cu.mogrify(" route_id = %s", (r.raw,)))
        if d is not None:
            dt1, dt2 = day_span(d)
            conditions.append(
                cu.mogrify(" last_modified between %s and %s", (dt1, dt2))
            )
        if conditions != []:
            query += b" where" + b" and".join(conditions)
        cu.execute(query)
        return [TripEntry.from_db_row(row) for row in cu.fetchall()]


def data_gdf(
    connection: Optional[connection] = None,
    r: Optional[m.RouteId] = None,
    d: Optional[date] = None,
) -> pd.DataFrame:
    ts = trip_data(connection, r, d)
    df = pd.DataFrame([t.as_dict() for t in ts])
    df["Coordinates"] = list(zip(df["longitude"], df["latitude"]))
    df["Coordinates"] = df["Coordinates"].apply(sg.Point)
    df = df.set_index("last_modified")
    return gpd.GeoDataFrame(df, geometry="Coordinates")


def store_route(r: Route, conn: Optional[connection] = None) -> None:
    if conn is None:
        conn = default_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into routes (
                    id, name, direction, number, category
                ) values (
                    %s, %s, %s,
                    %s, %s)
                """,
                [r.id, r.name, r.direction, r.number, r.category],
            )


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
    p: Passage, connection: Optional[connection] = None
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
                        direction, congestion_level, accuracy_level, status, category
                    ) values (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s)
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
                    ],
                )
                return None
        except Exception as e:
            return e


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


def routes() -> List[Union[Route, IncompleteRoute]]:
    j = json.load(
        open(
            "/Users/Noel/Developer/Projects/Busboy/resources/example-responses/routes.json"
        )
    )
    rs = j["routeTdi"]
    return [Route.from_json(r) for k, r in rs.items() if k != "foo"]


def routes_by_name() -> Dict[str, Route]:
    rs = routes()
    return {r.name: r for r in rs}


def routes_by_id() -> Dict[str, Route]:
    rs = routes()
    return {r.id: r for r in rs}


def trip_points(connection: connection, t: TripId) -> "TripPoints":
    with connection as co:
        with co.cursor() as cu:
            cu.execute(
                """
                select latitude, longitude, last_modified from passage_responses
                where trip_id = %s
                """,
                [t],
            )
            tps = [TripPoint(r[0], r[1], r[2]) for r in cu.fetchall()]
            return TripPoints(t.raw, tps)


@dataclass
class TripPoints(object):
    id: str
    points: List["TripPoint"]

    def to_json(self) -> Dict[str, Any]:
        return {"id": self.id, "points": [p.to_json() for p in self.points]}


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
class TripEntry(object):
    last_modified: datetime
    trip: m.TripId
    route: m.RouteId
    vehicle_id: str
    pattern_id: str
    latitude: float
    longitude: float
    bearing: int
    is_accessible: bool
    has_bike_rack: bool
    direction: int
    congestion_level: int
    accuracy_level: int
    status: int
    category: int

    @staticmethod
    def from_db_row(row: Tuple[Any, ...]) -> "TripEntry":
        return TripEntry(
            route=m.RouteId(cast(str, row[0])),
            direction=cast(int, row[1]),
            vehicle_id=cast(str, row[2]),
            last_modified=cast(datetime, row[3]),
            trip=m.TripId(cast(str, row[4])),
            congestion_level=cast(int, row[5]),
            accuracy_level=cast(int, row[6]),
            status=cast(int, row[7]),
            is_accessible=cast(bool, row[8]),
            latitude=cast(int, row[9]) / 3600000,
            longitude=cast(int, row[10]) / 3600000,
            bearing=cast(int, row[11]),
            pattern_id=cast(str, row[12]),
            has_bike_rack=cast(bool, row[13]),
            category=cast(int, row[14]),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {f.name: self.__dict__[f.name] for f in fields(self)}


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


def day_span(d: date) -> Tuple[datetime, datetime]:
    midnight = dt.time()
    day = dt.timedelta(days=1)
    dt1 = datetime.combine(d, midnight)
    dt2 = datetime.combine(d + day, midnight)
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
        return [Stop(r[0], r[1], r[2], r[3], r[4]) for r in cu.fetchall()]


def stop_by_name(name: str) -> Optional[Stop]:
    with open("resources/example-responses/busStopPoints.json") as f:
        j = json.load(f)
        for k, bs in j["bus_stops"].items():
            if bs["name"] == name:
                return Stop.from_json(bs)
        return None


def stops(c: Optional[connection] = None) -> List[Stop]:
    """Retrieves a list of all stops from the database."""
    if c is None:
        c = default_connection()
    with c.cursor() as cu:
        cu.execute("select * from stops")
        return [
            Stop(id=r[0], name=r[1], number=r[2], latitude=r[3], longitude=r[4])
            for r in cu.fetchall()
        ]

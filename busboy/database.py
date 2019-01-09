import psycopg2
from typing import Optional, List, Dict, Any
import json
from dataclasses import dataclass
from datetime import date, datetime
import datetime as dt

from busboy.model import Route, Stop, Passage, TripId

def default_connection():
    return psycopg2.connect('dbname=busboy user=Noel')

def test_connection():
    return psycopg2.connect(
        dbname='busboy-test',
        user='Noel')

def store_route(r: Route, conn=None) -> None:
    if conn is None:
        conn = default_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                insert into routes (
                    id, name, direction, number, category
                ) values (
                    %s, %s, %s,
                    %s, %s)
                ''',
                [r.id, r.name, r.direction, r.number, r.category])

def store_stop(r: Stop, conn=None) -> None:
    if conn is None:
        conn = default_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                insert into stops (
                    id, name, latitude, longitude, number
                ) values (
                    %s, %s, %s, %s, %s)
                ''',
                [r.id, r.name, r.latitude, r.longitude, r.number])

def store_trip(p: Passage, connection=None) -> Optional[Exception]:
    if connection is None:
        try:
            connection = default_connection()
        except Exception as e:
            return e
    with connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    insert into passage_responses(
                        last_modified, trip_id, route_id, vehicle_id, pattern_id,
                        latitude, longitude, bearing, is_accessible, has_bike_rack,
                        direction, congestion_level, accuracy_level, status, category
                    ) values (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s)
                    ''',
                    [p.last_modified, p.trip, p.route, p.vehicle, p.pattern,
                    p.latitude, p.longitude, p.bearing, p.is_accessible, p.has_bike_rack,
                    p.direction, p.congestion, p.accuracy, p.status, p.category])
        except Exception as e:
            return e


def test_database() -> None:
    with test_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                insert into messages
                values (%s)
                ''',
                ["hello!"])

def routes() -> List[Route]:
    j = json.load(open("/Users/Noel/Developer/Projects/Busboy/resources/example-responses/routes.json"))
    rs = j["routeTdi"]
    return [Route.from_json(r) for k, r in rs.items() if k != "foo"]

def routes_by_name() -> Dict[str, Route]:
    rs = routes()
    return {r.name: r for r in rs}

def routes_by_id() -> Dict[str, Route]:
    rs = routes()
    return {r.id: r for r in rs}

def trip_points(connection, t: TripId) -> "TripPoints":
    with connection as co:
        with co.cursor() as cu:
            cu.execute("""
                select latitude, longitude, last_modified from passage_responses
                where trip_id = %s
                """,
                t)
            tps = [TripPoint(r[0], r[1], r[2]) for r in cu.fetchall()]
            return TripPoints(t.value, tps)

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
            "time": self.time.isoformat()
        }

def trips_on_day(connection, d: date, r: Optional[str] = None) -> List[TripId]:
    with connection.cursor() as cu:
        midnight = dt.time()
        day = dt.timedelta(days=1)
        dt1 = datetime.combine(d, midnight)
        dt2 = datetime.combine(d + day, midnight)
        query = cu.mogrify("""
            select distinct trip_id from passage_responses
            where last_modified between %s and %s
            """,
            (dt1, dt2)
        )
        if r is not None:
            query += cu.mogrify(" and route_id = %s", (r,))
        cu.execute(query)
        return [TripId(row[0]) for row in cu.fetchall()]

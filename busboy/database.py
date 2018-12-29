import psycopg2
from typing import Optional

from busboy.model import Route, Stop, Passage

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

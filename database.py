import psycopg2
from model import Route, Stop

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

def test_database() -> None:
    with test_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                insert into messages
                values (%s)
                ''',
                ["hello!"])

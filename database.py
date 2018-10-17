import psycopg2
from model import Route

def default_connection():
    return psycopg2.connect('dbname=busboy user=Noel')

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

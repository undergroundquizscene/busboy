import typing as t
import psycopg2.extensions as x

def connect(s: str = ..., dbname: str = ..., user: str = ...) -> x.connection: ...

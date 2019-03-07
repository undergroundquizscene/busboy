from __future__ import annotations

import datetime as dt
import time
from concurrent.futures import Executor, Future, ThreadPoolExecutor, as_completed
from threading import Event, Timer
from time import strftime
from typing import Callable, Dict, Generator, Iterable, List, NoReturn, Optional, Tuple

import psycopg2 as pp2
from psycopg2.extensions import connection

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m
import busboy.util as u
from busboy.util import Either, Just, Left, Right, partition
from busboy.util.typevars import *


def loop(stops: Iterable[str] = c.cycle_stops, interval: float = 20) -> None:
    stop_ids = [m.StopId(s) for s in stops]
    with ThreadPoolExecutor(max_workers=300) as pool:
        while True:
            try:

                def inner(s: RecordingState) -> RecordingState:
                    new_state, errors = new_loop(pool, stop_ids, s)
                    others, key_errors = map(
                        list,
                        partition(lambda e: isinstance(e, pp2.IntegrityError), errors),
                    )
                    print(
                        f"Got {len(key_errors)} key errors and {len(others)} other errors:"
                    )
                    for e in others:
                        print(e)
                    return new_state

                d: RecordingState = {}
                loop_something(inner, d, interval)
            except Exception as e:
                print(f"Got error {e}")


def loop_something(f: Callable[[A], A], a: A, interval: float) -> None:
    iterations: Generator[A, None, NoReturn] = u.iterate(f, a)
    try:
        for t in u.interval(interval):
            print(f"Looping at time {t}")
            _ = next(iterations)
    except KeyboardInterrupt:
        print("\nExiting…")


RecordingState = Dict[m.PassageId, m.Passage]


def new_loop(
    pool: ThreadPoolExecutor, stops: Iterable[m.StopId], state: RecordingState
) -> Tuple[RecordingState, List[Exception]]:
    time = dt.datetime.now()
    connection = db.default_connection()
    futures: Dict[
        Future[Either[Exception, m.StopPassageResponse]], m.StopId
    ] = call_stops(pool, stops)
    next_state: RecordingState = {}
    errors: List[Exception] = []
    for i, f in enumerate(as_completed(futures), 1):
        stop = futures[f]
        spr = f.result()
        if isinstance(spr, Left):
            errors.append(spr.value)
        elif isinstance(spr, Right):
            current = dict(current_state(spr.value))
            new_state = updated_state(state, current)
            errors.extend(store_state(new_state, time, connection))
            next_state.update(current)
    return next_state, errors


def call_stops(
    pool: ThreadPoolExecutor, stops: Iterable[m.StopId]
) -> Dict[Future[Either[Exception, m.StopPassageResponse]], m.StopId]:
    return {pool.submit(api.stop_passage, stop): stop for stop in stops}


def current_state(
    spr: m.StopPassageResponse
) -> Generator[Tuple[m.PassageId, m.Passage], None, None]:
    for p in spr.passages:
        if isinstance(p.id, Just):
            yield (p.id.value, p)


def updated_state(last: RecordingState, current: RecordingState) -> RecordingState:
    """Those passages which differ between current and last, or are not in last."""
    return {i: p for i, p in current.items() if (i not in last or last[i] != p)}


def store_state(
    s: RecordingState, poll_time: dt.datetime, c: connection
) -> List[Exception]:
    errors = []
    for id, passage in s.items():
        e = db.store_trip(passage, poll_time, c)
        if e is not None:
            errors.append(e)
    return errors

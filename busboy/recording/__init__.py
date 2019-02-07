from __future__ import annotations

import datetime as dt
import time
from concurrent.futures import Executor, Future, ThreadPoolExecutor, as_completed
from threading import Event, Timer
from time import strftime
from typing import Callable, Dict, Generator, Iterable, List, NoReturn, Optional, Tuple

import psycopg2 as pp2

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m
import busboy.util as u
from busboy.util import Just
from busboy.util.typevars import *


def loop(stops: Iterable[str] = c.cycle_stops, interval: float = 2) -> None:
    stop_ids = [m.StopId(s) for s in stops]
    with ThreadPoolExecutor(max_workers=300) as pool:
        d: RecordingState = {}
        loop_something(lambda state: new_loop(pool, stop_ids, state), d, interval)


def loop_something(f: Callable[[A], A], a: A, interval: float) -> None:
    iterations: Generator[A, None, NoReturn] = u.iterate(f, a)
    try:
        for t in u.interval(interval):
            _ = next(iterations)
    except KeyboardInterrupt:
        print("\nExiting…")


RecordingState = Dict[m.PassageId, m.Passage]


def new_loop(
    pool: ThreadPoolExecutor, stops: Iterable[m.StopId], state: RecordingState
) -> RecordingState:
    futures: Dict[Future[m.StopPassageResponse], m.StopId] = call_stops(pool, stops)
    next_state: RecordingState = {}
    for i, f in enumerate(as_completed(futures), 1):
        stop = futures[f]
        spr = f.result()
        current = dict(current_state(spr))
        new_state = updated_state(state, current)
        store_new_info(new_state, stop, i)
        next_state.update(current)
    return next_state


def call_stops(
    pool: ThreadPoolExecutor, stops: Iterable[m.StopId]
) -> Dict[Future[m.StopPassageResponse], m.StopId]:
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


def store_new_info(state: RecordingState, stop: m.StopId, index: int) -> None:
    if index == 1:
        print("-" * 10 + " New poll " + "-" * 10)
    print(f"{len(state)} passages to update at {stop} (stop {index}):")
    for id, passage in state.items():
        print(f"  - {id}")


def make_requests(stop: m.StopId) -> List[Optional[Exception]]:
    spr = api.stop_passage(stop)
    c = db.default_connection()
    errors = [db.store_trip(p, connection=c) for p in spr.passages]
    c.close()
    return errors

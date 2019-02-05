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
from busboy.util.typevars import *


def loop(stops: Iterable[str] = c.cycle_stops, interval: float = 15) -> None:
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
    for f in as_completed(futures):
        s = futures[f]
        all_state, new_state = updated_state(state, f.result())
        store_new_info(new_state)
        next_state.update(all_state)
    return next_state


def call_stops(
    pool: ThreadPoolExecutor, stops: Iterable[m.StopId]
) -> Dict[Future[m.StopPassageResponse], m.StopId]:
    return {pool.submit(api.stop_passage, stop): stop for stop in stops}


def updated_state(
    s: RecordingState, spr: m.StopPassageResponse
) -> Tuple[RecordingState, RecordingState]:
    """Those passages which differ between spr and s, or are not in s."""
    new = {i: p for p in spr.passages for i in p.id if (i not in s or s[i] != p)}
    all = s.copy()
    all.update(new)
    return (all, new)


def store_new_info(state: RecordingState) -> None:
    print(f"{len(state)} passages were updated.")


def make_requests(stop: m.StopId) -> List[Optional[Exception]]:
    spr = api.stop_passage(stop)
    c = db.default_connection()
    errors = [db.store_trip(p, connection=c) for p in spr.passages]
    c.close()
    return errors

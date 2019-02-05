from concurrent.futures import Executor, as_completed, ThreadPoolExecutor
from threading import Event, Timer
from time import strftime
from typing import Iterable, List, Optional

import psycopg2 as pp2

import busboy.apis as api
import busboy.database as db
import busboy.model as m
import busboy.constants as c


def changes(
    old: m.StopPassageResponse, new: m.StopPassageResponse
) -> m.StopPassageResponse:
    """Filters out passages which haven’t changed."""
    pass


def loop(stops: Iterable[str] = c.cycle_stops) -> None:
    with ThreadPoolExecutor(max_workers=300) as pool:
        terminate = Event()
        cycle(stops, 15, pool, terminate)
        try:
            terminate.wait()
        except KeyboardInterrupt:
            print("\nExiting…")
            terminate.set()


def cycle(
    stops: Iterable[str], frequency: float, pool: Executor, terminate: Event
) -> None:
    if not terminate.is_set():
        print(f"Cycling at {strftime('%X')}")
        Timer(frequency, cycle, args=[stops, frequency, pool, terminate]).start()
        futures = [pool.submit(make_requests, m.StopId(stop)) for stop in stops]
        for i, f in enumerate(as_completed(futures), start=1):
            results = f.result()
            errors = (r for r in results if r is not None)
            bad_errors = [e for e in errors if not isinstance(e, pp2.IntegrityError)]
            error_types = {repr(e) for e in bad_errors}
            print(
                f"Stop {i}: Got {len(results)} results, {len(bad_errors)} errors, error types: {error_types}"
            )


def make_requests(stop: m.StopId) -> List[Optional[Exception]]:
    spr = api.stop_passage(stop)
    c = db.default_connection()
    errors = [db.store_trip(p, connection=c) for p in spr.passages]
    c.close()
    return errors

import concurrent.futures as cf
import datetime as dt
import shelve
from threading import Event
from typing import Dict, List, Union

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m
from busboy.experiments.types import PollResult


def poll_continuously(
    stops: List[m.StopId], frequency: float
) -> List[PollResult[m.StopPassageResponse]]:
    prs = []
    terminate = Event()
    while not terminate.is_set():
        try:
            t = dt.datetime.now()
            prs.append(PollResult(t, poll_stops(stops)))
            print(f"Cycled at {t}, waiting {frequency} seconds…")
            terminate.wait(frequency)
        except KeyboardInterrupt:
            print("Returning…")
            terminate.set()
    return prs


def poll_stops(
    stops: List[m.StopId]
) -> Dict[m.StopId, Union[m.StopPassageResponse, Exception]]:
    with cf.ThreadPoolExecutor(max_workers=60) as executor:
        future_to_stop = {executor.submit(api.stop_passage, s): s for s in stops}
        sprs: Dict[m.StopId, Union[m.StopPassageResponse, Exception]] = {}
        for f in cf.as_completed(future_to_stop):
            s = future_to_stop[f]
            try:
                spr = f.result()
            except Exception as e:
                sprs[s] = e
            else:
                sprs[s] = spr
        return sprs


def check_many_stops() -> None:
    ids = {s.id for s in c.stops_on_220 if s is not None}
    result = poll_continuously(list(ids), 10)
    print(f"Storing result, which has length {len(result)}")
    with shelve.open("resources/experiments/many-stops") as db:
        db["data"] = result

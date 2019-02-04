from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import shelve
from threading import Event
from typing import Dict, List, Union

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m
from busboy.experiments.types import PollResult
from busboy.util import Either, Left, Right


def poll_continuously(
    stops: List[m.StopId], interval: float
) -> List[PollResult[Either[Exception, m.StopPassageResponse]]]:
    prs = []
    terminate = Event()
    while not terminate.is_set():
        try:
            t = dt.datetime.now()
            prs.append(PollResult(t, poll_stops(stops)))
            print(f"Cycled at {t}, waiting {interval} seconds…")
            terminate.wait(interval)
        except KeyboardInterrupt:
            print("Returning…")
            terminate.set()
    return prs


def poll_stops(
    stops: List[m.StopId]
) -> Dict[m.StopId, Either[Exception, m.StopPassageResponse]]:
    with cf.ThreadPoolExecutor(max_workers=60) as executor:
        future_to_stop = {executor.submit(api.stop_passage, s): s for s in stops}
        sprs: Dict[m.StopId, Either[Exception, m.StopPassageResponse]] = {}
        for f in cf.as_completed(future_to_stop):
            s = future_to_stop[f]
            try:
                spr = f.result()
            except Exception as e:
                print("Returning exception")
                sprs[s] = Left(e)
            else:
                sprs[s] = Right(spr)
        return sprs


def check_many_stops() -> None:
    ids = {s.id for s in c.stops_on_220 if s is not None}
    result = poll_continuously(list(ids), 10)
    print(f"Storing result, which has length {len(result)}")
    with shelve.open("resources/experiments/many-stops") as db:
        db["data"] = result


def two_second() -> List[PollResult[Either[Exception, m.StopPassageResponse]]]:
    stops = [c.example_stops["gpc"], c.example_stops["ovens"]]
    return poll_continuously([s.id for s in stops], 2)


def store_two_second(filename: str) -> None:
    prs = two_second()
    print(f"Storing {len(prs)} poll results in {filename}…")
    j = [PollResult.to_json(pr) for pr in prs]
    with open(filename, "w") as f:
        json.dump(j, f, indent=4)

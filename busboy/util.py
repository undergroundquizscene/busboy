from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Optional, Set, Iterable, Callable, TypeVar, Generic
import shelve
import dataclasses
from dataclasses import dataclass
import concurrent.futures as cf
import datetime as dt
from threading import Event

import busboy.rest as api
import busboy.model as m
import busboy.constants as c
import busboy.database as db


def route_stops(r: int):
    soup = make_soup(r)
    tables = get_tables(soup)

    def right_th(e):
        return e.name == "th" and e.parent.parent.name == "tbody"

    stop_cells = [t["table"].find_all(right_th) for t in tables]
    stop_names = [
        [c.string.strip() for c in cs if c.string is not None] for cs in stop_cells
    ]
    return stop_names


def get_tables(soup):
    def right_id(i):
        return i is not None and i.startswith("table-spreadsheet")

    ts = soup.find_all(id=right_id)

    def table_id(t):
        return t.thead.tr.th.next_sibling.string.strip()

    tables = [{"table": t, "route": table_id(t)} for t in ts]
    return tables


def make_soup(r: int):
    stops_endpoint = "http://buseireann.ie/inner.php?id=406"
    html = requests.get(
        stops_endpoint,
        params={"form-view-timetables-route": r, "form-view-timetables-submit": 1},
    ).text
    return BeautifulSoup(html, features="html.parser")


def route_stops_to_file():
    import json

    f = open("resources/stoplists.json")
    f = open("resources/stoplists.json", "w")
    json.dump(stops, f)
    json.dump(stops, f)
    json.dump(stops, f, indent=4)
    f.close()
    f = open("resources/stoplists.json", "w")
    json.dump(stops, f, indent=4)
    f.close()
    f = open("resources/stoplists.json", "w")
    json.dump(stops, f, indent=2)
    f.close()


T = TypeVar("T")
U = TypeVar("U")


@dataclass
class PollResult(Generic[T]):
    time: dt.datetime
    results: Dict[m.StopId, T]

    def filter(self, f: Callable[[T], bool]) -> "PollResult[T]":
        return dataclasses.replace(
            self, results={s: spr for s, spr in self.results.items() if f(spr)}
        )

    def map(self, f: Callable[[T], U]) -> "PollResult[U]":
        return PollResult(
            time=self.time, results={s: f(spr) for s, spr in self.results.items()}
        )

    @staticmethod
    def trips(
        pr: PollResult[m.StopPassageResponse]
    ) -> "PollResult[Set[Optional[m.TripId]]]":
        return pr.map(lambda spr: {p.trip for p in spr.passages})

    @staticmethod
    def all_trips(pr: PollResult[m.StopPassageResponse]) -> "Set[Optional[m.TripId]]":
        return {t for ts in PollResult.trips(pr).results.values() for t in ts}


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


def poll_stops(stops: List[m.StopId]) -> Dict[m.StopId, m.StopPassageResponse]:
    with cf.ThreadPoolExecutor(max_workers=60) as executor:
        future_to_stop = {executor.submit(api.stop_passage, s): s for s in stops}
        sprs = {}
        for f in cf.as_completed(future_to_stop):
            s = future_to_stop[f]
            try:
                spr = f.result()
            except Exception as e:
                print(f"Got exception {e} on stop {s}")
            else:
                sprs[s] = spr
        return sprs


def check_many_stops() -> None:
    ids = {m.StopId(s.id) for s in c.stops_on_220 if s is not None}
    result = poll_continuously(list(ids), 10)
    print(f"Storing result, which has length {len(result)}")
    with shelve.open("resources/experiments/many-stops") as db:
        db["data"] = result


def get_many_stops_data() -> List[PollResult[m.StopPassageResponse]]:
    with shelve.open("resources/experiments/many-stops") as db:
        return [update_poll_result(pr) for pr in db["data"]]


def route_ids(prs: List[PollResult[m.StopPassageResponse]]) -> Set[m.RouteId]:
    return {
        p.route
        for pr in prs
        for s, spr in pr.results.items()
        for p in spr.passages
        if p.route is not None
    }


def update_poll_result(
    pr: PollResult[m.StopPassageResponse]
) -> PollResult[m.StopPassageResponse]:
    results = {
        s: m.StopPassageResponse(
            [
                m.Passage(
                    m.PassageId(p.id),
                    p.last_modified,
                    m.TripId(p.trip),
                    m.RouteId(p.route),
                    m.VehicleId(p.vehicle),
                    m.StopId(p.stop),
                    m.PatternId(p.pattern),
                    p.latitude,
                    p.longitude,
                    p.bearing,
                    p.time,
                    p.is_deleted,
                    p.is_accessible,
                    p.has_bike_rack,
                    p.direction,
                    p.congestion,
                    p.accuracy,
                    p.status,
                    p.category,
                )
                for p in spr.passages
            ]
        )
        for s, spr in pr.results.items()
    }
    return PollResult(pr.time, results)


PresenceData = Dict[Optional[m.TripId], PollResult[bool]]


def trip_presences(pr: PollResult[m.StopPassageResponse]) -> PresenceData:
    all_trips = PollResult.all_trips(pr)
    return {
        t: pr.map(lambda spr: m.StopPassageResponse.contains_trip(spr, t))
        for t in all_trips
    }


def show_presences(pd: PresenceData, stops: Dict[str, m.Stop]) -> str:
    lines = []
    stop_id_order = [s.id for s in c.stops_on_220 if s is not None]
    for t, pr in pd.items():
        lines.append(f"{t}:")
        indent = "    "
        for n, (s, b) in enumerate(
            sorted(pr.results.items(), key=lambda t: stop_id_order.index(t[0].raw)),
            start=1,
        ):
            stop = stops.get(s.raw)
            if stop is None:
                stop_name = "None"
            else:
                stop_name = stop.name
            lines.append(f"{indent}{n:2} {stop_name:50} {b}")
        lines.append("")
    return "\n".join(lines)

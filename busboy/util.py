from bs4 import BeautifulSoup
import requests
from typing import (
    List,
    Dict,
    Optional,
    Set,
    Iterable,
    Callable,
    TypeVar,
    Generic,
    Any,
    Type,
)
import shelve
import dataclasses
from dataclasses import dataclass
import concurrent.futures as cf
import datetime as dt
from threading import Event
import json

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
    def to_json(pr: "PollResult[m.StopPassageResponse]") -> Dict[str, Any]:
        return {
            "time": pr.time.isoformat(),
            "results": {s.raw: spr.to_json() for s, spr in pr.results.items()},
        }

    @staticmethod
    def from_json(j: Dict[str, Any]) -> "PollResult[m.StopPassageResponse]":
        t = dt.datetime.fromisoformat(j["time"])
        rs = {
            m.StopId(s): m.StopPassageResponse.from_my_json(spr)
            for s, spr in j["results"].items()
        }
        return PollResult(t, rs)

    @staticmethod
    def trips(
        pr: "PollResult[m.StopPassageResponse]"
    ) -> "PollResult[Set[Optional[m.TripId]]]":
        return pr.map(lambda spr: {p.trip for p in spr.passages})

    @staticmethod
    def all_trips(pr: "PollResult[m.StopPassageResponse]") -> Set[Optional[m.TripId]]:
        return {t for ts in PollResult.trips(pr).results.values() for t in ts}

    @staticmethod
    def all_passages(pr: "PollResult[m.StopPassageResponse]") -> Set[m.Passage]:
        return {p for _, spr in pr.results.items() for p in spr.passages}


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


PresenceData = Dict["PassageTrip", PollResult[bool]]


def trip_presences(pr: PollResult[m.StopPassageResponse]) -> PresenceData:
    all_trips = {PassageTrip.from_passage(p) for p in PollResult.all_passages(pr)}
    return {
        p: pr.map(lambda spr: m.StopPassageResponse.contains_trip(spr, p.id))
        for p in all_trips
    }


def presence_display(
    pd: PresenceData, stops: Dict[str, m.Stop], routes: Dict[str, m.Route]
) -> str:
    lines = []
    stop_id_order = [s.id for s in c.stops_on_220 if s is not None]
    for m, (pt, pr) in enumerate(pd.items(), start=1):
        route_data = routes.get(pt.route.raw)
        if route_data is None:
            route_data = pt.route
        pt_with_route = dataclasses.replace(pt, route=route_data)
        lines.append(f"{m:2} {pt_with_route}:")
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


@dataclass(frozen=True)
class PassageTrip(object):
    """All trip-specific information contained in a Passage."""

    id: Optional[m.TripId]
    route: Optional[m.RouteId]
    vehicle: Optional[m.VehicleId]
    latitude: Optional[float]
    longitude: Optional[float]
    bearing: Optional[int]

    @staticmethod
    def from_passage(p: m.Passage) -> "PassageTrip":
        return PassageTrip(
            p.trip, p.route, p.vehicle, p.latitude, p.longitude, p.bearing
        )


def trip_stops(
    pr: PollResult[m.StopPassageResponse]
) -> Dict[Optional[m.TripId], Set[m.StopId]]:
    """The stops trips were visible at in this poll result."""
    d = {}
    for s, spr in pr.results.items():
        for p in spr.passages:
            d.setdefault(p.trip, set()).add(s)
    return d


def route_cover(d: Dict[m.TripId, Set[m.StopId]]) -> Set[m.StopId]:
    """Supposed to find a (maybe minimal) set of stops that will get all the trips.

    Currently only finds the stops common to all trips, and there may be none.
    """
    cover = None
    for t, s in d.items():
        if cover is None:
            cover = s
        else:
            cover = cover.intersection(s)
    return cover


@dataclass(frozen=True)
class StopCounts(object):
    """How many trips are covered by each stop."""

    counts: Dict[m.StopId, int]
    total: int


def stop_counts(d: Dict[m.TripId, Set[m.StopId]]) -> StopCounts:
    """Calculates the number of trips covered by each stop."""
    counts: Dict[m.StopId, int] = {}
    trips = set()
    for t, stops in d.items():
        for s in stops:
            counts[s] = counts.get(s, 0) + 1
        trips.add(t)
    return StopCounts(counts, len(trips))


@dataclass(frozen=True)
class StopTrips(object):
    """The trips covered by each stop."""

    trips: Dict[m.StopId, Set[Optional[m.TripId]]]
    all_trips: Set[Optional[m.TripId]]


def stop_trips(pr: PollResult[m.StopPassageResponse]) -> StopTrips:
    """Determines the trips which were visible at each stop in this poll result."""
    trips = {s: {p.trip for p in spr.passages} for s, spr in pr.results.items()}
    all_trips = {t for s, ts in trips.items() for t in ts}
    return StopTrips(trips, all_trips)


def show_presences() -> None:
    prs = get_many_stops_data()
    rbn = db.routes_by_name()
    prs_220 = [
        pr.map(lambda spr: spr.filter(lambda p: p.route.raw == rbn["220"].id))
        for pr in prs
    ]
    rbi = db.routes_by_id()
    sbi = {s.id: s for s in db.stops()}
    print(presence_display(trip_presences(prs[0]), sbi, rbi))


def convert_shelf_to_json() -> None:
    prs = get_many_stops_data()
    with open("resources/experiments/many-stops.json", 'w') as f:
        json.dump([pr.to_json(pr) for pr in prs], f, indent=2)

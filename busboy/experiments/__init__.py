import concurrent.futures as cf
import dataclasses
import datetime as dt
import json
import shelve
from dataclasses import dataclass
from threading import Event
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

import busboy.constants as c
import busboy.database as db
import busboy.model as m
import busboy.rest as api
from busboy.experiments.types import (
    PassageTrip,
    PollResult,
    PresenceData,
    StopCounts,
    StopTrips,
)

data_files = {
    "many-stops": "resources/experiments/many-stops",
    "two-second": "resources/experiments/two-second",
}


def many_stops_data() -> List[PollResult[m.StopPassageResponse]]:
    return poll_result_data("resources/experiments/many-stops.json")


def two_second_data() -> List[PollResult[m.StopPassageResponse]]:
    return poll_result_data("resources/experiments/two-second.json")


def poll_result_data(path: str) -> List[PollResult[m.StopPassageResponse]]:
    with open(path) as f:
        js = json.load(f)
    return [PollResult.from_json(j) for j in js]


def poll_shelve_data(path: str) -> List[PollResult[m.StopPassageResponse]]:
    with shelve.open(path) as db:
        return [pr for pr in db["data"]]


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


def stop_counts(d: Dict[m.TripId, Set[m.StopId]]) -> StopCounts:
    """Calculates the number of trips covered by each stop."""
    counts: Dict[m.StopId, int] = {}
    trips = set()
    for t, stops in d.items():
        for s in stops:
            counts[s] = counts.get(s, 0) + 1
        trips.add(t)
    return StopCounts(counts, len(trips))


def stop_trips(pr: PollResult[m.StopPassageResponse]) -> StopTrips:
    """Determines the trips which were visible at each stop in this poll result."""
    trips = {s: {p.trip for p in spr.passages} for s, spr in pr.results.items()}
    all_trips = {t for s, ts in trips.items() for t in ts}
    return StopTrips(trips, all_trips)


def show_presences() -> None:
    prs = many_stops_data()
    rbn = db.routes_by_name()
    prs_220 = [
        pr.map(lambda spr: spr.filter(lambda p: p.route.raw == rbn["220"].id))
        for pr in prs
    ]
    rbi = db.routes_by_id()
    sbi = {s.id: s for s in db.stops()}
    print(presence_display(trip_presences(prs[0]), sbi, rbi))


def convert_shelf_to_json(path: str) -> None:
    prs = poll_result_data(path)
    with open(path + ".json", "w") as f:
        json.dump([pr.to_json(pr) for pr in prs], f, indent=2)


def route_ids(prs: List[PollResult[m.StopPassageResponse]]) -> Set[m.RouteId]:
    return {
        p.route
        for pr in prs
        for s, spr in pr.results.items()
        for p in spr.passages
        if p.route is not None
    }

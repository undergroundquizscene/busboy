import concurrent.futures as cf
import dataclasses
import json
import shelve
from dataclasses import dataclass
from datetime import datetime
from itertools import islice, tee
from threading import Event
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m
import busboy.util as u
from busboy.experiments.types import (
    PassageTrip,
    PollResult,
    PresenceData,
    StopCounts,
    StopTrips,
)
from busboy.geo import (
    DegreeLatitude,
    DegreeLongitude,
    LatLon,
    LonLat,
    RawLatitude,
    RawLongitude,
)
from busboy.util import Either, Left, Maybe, Nothing, Right, unique

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
    return {p: pr.map(lambda spr: spr_trip_time(spr, p.id)) for p in all_trips}


def spr_trip_time(spr: m.StopPassageResponse, t: m.TripId) -> Either[str, datetime]:
    lmts = [p.last_modified for p in spr.passages if p.trip == t]
    if lmts == []:
        return Left("No times for trip")
    elif len(lmts) == 1:
        return lmts[0].either("No time in only passage")
    else:
        return Left("Multiple times for trip")


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
) -> Dict[Maybe[m.TripId], Set[m.StopId]]:
    """The stops trips were visible at in this poll result."""
    d: Dict[Maybe[m.TripId], Set[m.StopId]] = {}
    for s, spr in pr.results.items():
        for p in spr.passages:
            d.setdefault(p.trip, set()).add(s)
    return d


def route_cover(d: Dict[m.TripId, Set[m.StopId]]) -> Optional[Set[m.StopId]]:
    """Supposed to find a (maybe minimal) set of stops that will get all the trips.

    Currently only finds the stops common to all trips, and there may be none.

    Returns None if the dictionary is empty.
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


def route_ids(prs: List[PollResult[m.StopPassageResponse]]) -> Set[Maybe[m.RouteId]]:
    return {
        p.route
        for pr in prs
        for s, spr in pr.results.items()
        for p in spr.passages
        if p.route is not None
    }


def updates(
    prs: List[PollResult[m.StopPassageResponse]]
) -> Dict[Maybe[m.TripId], List[m.Passage]]:
    times: Dict[Maybe[m.TripId], Set[m.Passage]] = {}
    for pr in prs:
        for p in PollResult.all_passages(pr):
            times.setdefault(p.trip, set()).add(p)
    return {t: sorted(ts, key=lambda p: p.last_modified) for t, ts in times.items()}


def update_times(
    prs: List[PollResult[m.StopPassageResponse]]
) -> Dict[Maybe[m.TripId], List[Maybe[datetime]]]:
    return {t: sorted({p.last_modified for p in ps}) for t, ps in updates(prs).items()}


def vehicle_updates(
    prs: List[PollResult[m.StopPassageResponse]]
) -> Dict[Maybe[m.VehicleId], Dict[datetime, Dict[m.StopId, List[m.Passage]]]]:
    times: Dict[
        Maybe[m.VehicleId], Dict[datetime, Dict[m.StopId, List[m.Passage]]]
    ] = {}
    for pr in prs:
        for s, spr in pr.results.items():
            for p in spr.passages:
                times.setdefault(p.vehicle, {}).setdefault(pr.time, {}).setdefault(
                    s, []
                ).append(p)
    return times


def display_update_times(uts: Dict[Any, List[Optional[datetime]]]) -> None:
    for pt, dts in sorted(uts.items(), key=lambda t: len(t[1])):
        print(pt)
        for dt in u.take(1, dts):
            print(f"- {dt.isoformat()}")
        for last, dt in u.pairwise(dts):
            print(f"- {dt.isoformat()} (+{(dt - last)})")
        print()


def display_updates(uts: Dict[Any, List[Tuple[datetime, m.Passage]]]) -> None:
    for pt, ps in sorted(uts.items(), key=lambda t: len(t[1])):
        print(pt)
        for (t, p) in ps:
            print(
                f"- (request time: {t}, mod time: {p.last_modified.isoformat()}, trip: {p.trip.raw}, position: {(p.latitude, p.longitude)})"
            )
        print()


def display_vehicle_updates(
    updates: Dict[Maybe[m.VehicleId], Dict[datetime, Dict[m.StopId, List[m.Passage]]]]
) -> None:
    for v, ts in updates.items():
        print(v.optional())
        for t, stops in ts.items():
            for s, ps in stops.items():
                for p in ps:
                    print(
                        " " * 4
                        + ", ".join(
                            [
                                f"- time: {t.time().isoformat()}",
                                f"mod: {p.last_modified.map(lambda t: t.time().isoformat()).optional()}",
                                f"trip: {p.trip.optional().raw}",
                                f"position: {p.position.optional()}",
                            ]
                        )
                    )
        print()


def display_nones(
    updates: Dict[Maybe[m.VehicleId], Dict[datetime, Dict[m.StopId, List[m.Passage]]]]
) -> None:
    display_vehicle_updates({k: v for k, v in updates.items() if k == Nothing()})


def display_poll_results(prs: List[PollResult[m.StopPassageResponse]]) -> None:
    for pr in prs:
        print(pr.time.time().isoformat())
        for s, spr in pr.results.items():
            print(" " * 2 + str(s))
            for p in spr.passages:
                print(
                    " " * 4
                    + f"- (vehicle: {p.vehicle.optional()}, mod: {p.last_modified.map(lambda t: t.isoformat()).optional()}, position: {p.position.optional()})"
                )


def positions(
    uts: Dict[m.VehicleId, List[Tuple[datetime, m.Passage]]]
) -> Dict[m.VehicleId, List[Tuple[datetime, LatLon]]]:
    d = {}
    for v, ps in sorted(uts.items(), key=lambda t: len(t[1])):
        for (t, p) in ps:
            d.setdefault(v, []).append(
                (
                    t,
                    (
                        p.latitude.map(lambda l: l / 3_600_000),
                        p.longitude.map(lambda l: l / 3_600_000),
                    ),
                )
            )
    return d


def old_unique_results(
    prs: List[PollResult[m.StopPassageResponse]]
) -> Dict[m.StopId, Set[Tuple[datetime, m.StopPassageResponse]]]:
    d: Dict[m.StopId, Set[Tuple[datetime, m.StopPassageResponse]]] = {}
    for pr in prs:
        for s, spr in pr.results.items():
            t = (pr.time, dataclasses.replace(spr, passages=tuple(spr.passages)))
            d.setdefault(s, set()).add(t)
    return d


def results(
    prs: Iterable[PollResult[m.StopPassageResponse]]
) -> Iterable[Tuple[datetime, m.StopId, m.StopPassageResponse]]:
    for pr in prs:
        for s, spr in pr.results.items():
            yield (pr.time, s, spr)


def unique_results(
    rs: Iterable[Tuple[datetime, m.StopId, m.StopPassageResponse]]
) -> Iterable[Tuple[datetime, m.StopId, m.StopPassageResponse]]:
    return unique(rs, key=lambda t: (t[1], t[2]))


def unique_positions(
    prs: Iterable[PollResult[m.StopPassageResponse]]
) -> Iterable[
    Tuple[datetime, m.StopId, Iterable[Maybe[Tuple[DegreeLatitude, DegreeLongitude]]]]
]:
    for (dt, s, spr) in unique_results(results(prs)):
        yield (dt, s, spr.positions())

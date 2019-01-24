import concurrent.futures as cf
import dataclasses
import datetime as dt
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Generic, Optional, Set, TypeVar

import busboy.apis as api
import busboy.constants as c
import busboy.database as db
import busboy.model as m

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


PresenceData = Dict["PassageTrip", PollResult[bool]]


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


@dataclass(frozen=True)
class StopCounts(object):
    """How many trips are covered by each stop."""

    counts: Dict[m.StopId, int]
    total: int


@dataclass(frozen=True)
class StopTrips(object):
    """The trips covered by each stop."""

    trips: Dict[m.StopId, Set[Optional[m.TripId]]]
    all_trips: Set[Optional[m.TripId]]

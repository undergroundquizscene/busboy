from typing import (
    Dict,
    NewType,
    Any,
    NamedTuple,
    Optional,
    List,
    TypeVar,
    Type,
    Union,
    Callable,
    cast,
)
from datetime import datetime
import json
from dataclasses import dataclass

PassageNumber = NewType("PassageNumber", int)


@dataclass(frozen=True)
class StopId(object):
    raw: str


@dataclass(frozen=True)
class TripId(object):
    raw: str


@dataclass(frozen=True)
class RouteId(object):
    raw: str


@dataclass(frozen=True)
class Route(object):
    id: str
    name: str
    direction: int
    direction_name: str
    number: int
    category: int

    @staticmethod
    def from_json(route_json: Dict[str, Any]) -> Union["Route", "IncompleteRoute"]:
        id = route_json.get("duid")
        name = route_json.get("short_name")
        direction = omap(
            lambda j: j.get("direction"),
            cast(Dict[str, Any], route_json.get("direction_extensions")),
        )
        number = route_json.get("number")
        category = route_json.get("category")
        direction_name = omap(
            lambda j: j.get("direction_name"),
            cast(Dict[str, Any], route_json.get("direction_extensions")),
        )
        if None in {id, name, direction, number, category, direction_name}:
            return IncompleteRoute(
                id, name, direction, number, category, direction_name
            )
        else:
            return Route(  # type: ignore
                id=id,
                name=name,
                direction=direction,
                number=number,
                category=category,
                direction_name=direction_name,
            )


@dataclass(frozen=True)
class IncompleteRoute(object):
    id: Optional[str]
    name: Optional[str]
    direction: Optional[int]
    direction_name: Optional[str]
    number: Optional[int]
    category: Optional[int]


@dataclass(frozen=True)
class Stop(object):
    id: str
    name: str
    latitude: float
    longitude: float
    number: int

    @classmethod
    def from_json(cls, stop_json: Dict[str, Any]) -> "Stop":
        id = stop_json["duid"]
        name = stop_json["name"]
        latitude = stop_json["lat"]
        longitude = stop_json["lng"]
        number = stop_json["num"]
        return cls(id, name, latitude, longitude, number)


class StopPassageResponse(NamedTuple):
    passages: List["Passage"]

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "StopPassageResponse":
        ps = [
            Passage.from_json(pj)
            for k, pj in json["stopPassageTdi"].items()
            if k != "foo"
        ]
        return cls(ps)


class Passage(NamedTuple):
    id: Optional[str]
    last_modified: Optional[datetime]
    trip: Optional[str]
    route: Optional[str]
    vehicle: Optional[str]
    stop: Optional[str]
    pattern: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    bearing: Optional[int]
    time: "Optional[PassageTime]"
    is_deleted: Optional[bool]
    is_accessible: Optional[bool]
    has_bike_rack: Optional[bool]
    direction: Optional[int]
    congestion: Optional[int]
    accuracy: Optional[int]
    status: Optional[int]
    category: Optional[int]

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "Passage":
        time = PassageTime.from_json(json)
        try:
            return cls(
                id=json.get("duid"),
                last_modified=omap(
                    lambda j: datetime.utcfromtimestamp(j / 1000),
                    cast(Optional[int], json.get("last_modification_timestamp")),
                ),
                is_deleted=json.get("is_deleted"),
                route=omap(
                    lambda j: j.get("duid"),
                    cast(Dict[str, Any], json.get("route_duid")),
                ),
                direction=json.get("direction"),
                trip=omap(
                    lambda j: j.get("duid"), cast(Dict[str, Any], json.get("trip_duid"))
                ),
                stop=omap(
                    lambda j: j.get("duid"),
                    cast(Dict[str, Any], json.get("stop_point_duid")),
                ),
                vehicle=omap(
                    lambda j: j.get("duid"),
                    cast(Dict[str, Any], json.get("vehicle_duid")),
                ),
                time=time,
                congestion=json.get("congestion_level"),
                accuracy=json.get("accuracy_level"),
                status=json.get("status"),
                is_accessible=omap(bool, json.get("is_accessible")),
                latitude=json.get("latitude"),
                longitude=json.get("longitude"),
                bearing=json.get("bearing"),
                pattern=omap(
                    lambda j: j.get("duid"),
                    cast(Dict[str, Any], json.get("pattern_duid")),
                ),
                has_bike_rack=omap(bool, json.get("has_bike_rack")),
                category=json.get("category"),
            )
        except KeyError as e:
            raise Exception(json, e)


class PassageTime(NamedTuple):
    arrival: Optional["ArrivalTime"]
    departure: Optional["DepartureTime"]

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "PassageTime":
        a = omap(ArrivalTime.from_json, json.get("arrival_data"))
        d = omap(DepartureTime.from_json, json.get("departure_data"))
        return cls(arrival=a, departure=d)


class ArrivalDeparture(NamedTuple):
    scheduled: Optional[int]
    actual_or_prediction: Optional[datetime]
    service_mode: Optional[int]
    type: Optional[int]
    direction_text: Optional[str]

    @classmethod
    def from_json(cls: Any, json: Dict[str, Any]) -> Any:
        return cls(
            scheduled=omap(
                datetime.utcfromtimestamp, json.get("scheduled_passage_time_utc")
            ),
            actual_or_prediction=omap(
                datetime.utcfromtimestamp, json.get("actual_passage_time_utc")
            ),
            service_mode=json.get("service_mode"),
            type=json.get("type"),
            direction_text=omap(
                lambda j: j.get("defaultValue"),
                cast(Dict[str, Any], json.get("multilingual_direction_text")),
            ),
        )


class ArrivalTime(ArrivalDeparture):
    pass


class DepartureTime(ArrivalDeparture):
    pass


A = TypeVar("A")
B = TypeVar("B")


def omap(f: Callable[[A], B], x: Optional[A]) -> Optional[B]:
    return None if x is None else f(x)

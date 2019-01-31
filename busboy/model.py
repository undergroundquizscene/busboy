import json
from dataclasses import dataclass
from datetime import datetime, time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    NewType,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from busboy.geo import DegreeLatitude, DegreeLongitude, LatLon, LonLat
from busboy.util import Just, Maybe, Nothing, omap

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
class PassageId(object):
    raw: str


@dataclass(frozen=True)
class VehicleId(object):
    raw: str


@dataclass(frozen=True)
class PatternId(object):
    raw: str


@dataclass(frozen=True)
class Route(object):
    id: RouteId
    name: str
    direction: int
    direction_name: str
    number: int
    category: int

    @staticmethod
    def from_json(route_json: Dict[str, Any]) -> "Route":
        return Route(
            id=RouteId(route_json["duid"]),
            name=route_json["short_name"],
            direction=route_json["direction_extensions"]["direction"],
            number=route_json["number"],
            category=route_json["category"],
            direction_name=route_json["direction_extensions"]["direction_name"],
        )


@dataclass(frozen=True)
class Stop(object):
    id: StopId
    name: str
    latitude: DegreeLatitude
    longitude: DegreeLongitude
    number: int

    @classmethod
    def from_json(cls, stop_json: Dict[str, Any]) -> "Stop":
        id = StopId(stop_json["duid"])
        name = stop_json["name"]
        latitude = stop_json["lat"]
        longitude = stop_json["lng"]
        number = stop_json["num"]
        return cls(id, name, latitude, longitude, number)

    @property
    def lon_lat(self) -> LonLat:
        return (self.longitude, self.latitude)

    @property
    def lat_lon(self) -> LatLon:
        return (self.latitude, self.longitude)


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

    @staticmethod
    def from_my_json(j: Dict[str, Any]) -> "StopPassageResponse":
        return StopPassageResponse([Passage.from_my_json(p) for p in j["passages"]])

    def to_json(self) -> Dict[str, Any]:
        return {"passages": [p.to_json() for p in self.passages]}

    def trip_ids(self) -> List[Optional[TripId]]:
        return [p.trip for p in self.passages]

    def filter(self, f: Callable[["Passage"], bool]) -> "StopPassageResponse":
        return StopPassageResponse([p for p in self.passages if f(p)])

    def contains_trip(self, t: Optional[TripId]) -> bool:
        return t in {p.trip for p in self.passages}


class Passage(NamedTuple):
    id: Optional[PassageId]
    last_modified: Optional[datetime]
    trip: Optional[TripId]
    route: Optional[RouteId]
    vehicle: Optional[VehicleId]
    stop: Optional[StopId]
    pattern: Optional[PatternId]
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
                id=PassageId(cast(str, json.get("duid"))),
                last_modified=omap(
                    lambda j: datetime.utcfromtimestamp(j / 1000),
                    cast(Optional[int], json.get("last_modification_timestamp")),
                ),
                is_deleted=cast(bool, json.get("is_deleted")),
                route=omap(
                    lambda j: j.get("duid"),
                    cast(Dict[str, Any], json.get("route_duid")),
                ),
                direction=cast(int, json.get("direction")),
                trip=omap(
                    lambda j: TripId(cast(str, j.get("duid"))),
                    cast(Dict[str, Any], json.get("trip_duid")),
                ),
                stop=omap(
                    lambda j: StopId(cast(str, j.get("duid"))),
                    cast(Dict[str, Any], json.get("stop_point_duid")),
                ),
                vehicle=omap(
                    lambda j: VehicleId(cast(str, j.get("duid"))),
                    cast(Dict[str, Any], json.get("vehicle_duid")),
                ),
                time=time,
                congestion=cast(int, json.get("congestion_level")),
                accuracy=cast(int, json.get("accuracy_level")),
                status=cast(int, json.get("status")),
                is_accessible=omap(bool, json.get("is_accessible")),
                latitude=cast(int, json.get("latitude")),
                longitude=cast(int, json.get("longitude")),
                bearing=cast(int, json.get("bearing")),
                pattern=omap(
                    lambda j: PatternId(cast(str, j.get("duid"))),
                    cast(Dict[str, Any], json.get("pattern_duid")),
                ),
                has_bike_rack=omap(bool, json.get("has_bike_rack")),
                category=cast(int, json.get("category")),
            )
        except KeyError as e:
            raise Exception(json, e)

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": omap(lambda i: i.raw, self.id),
            "last_modified": omap(lambda dt: dt.isoformat(), self.last_modified),
            "trip_id": omap(lambda i: i.raw, self.trip),
            "route_id": omap(lambda i: i.raw, self.route),
            "vehicle_id": omap(lambda i: i.raw, self.vehicle),
            "stop_id": omap(lambda i: i.raw, self.stop),
            "pattern_id": omap(lambda i: i.raw, self.pattern),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "bearing": self.bearing,
            "time": omap(lambda t: t.to_json(), self.time),
            "is_deleted": self.is_deleted,
            "is_accessible": self.is_accessible,
            "has_bike_rack": self.has_bike_rack,
            "direction": self.direction,
            "congestion": self.congestion,
            "accuracy": self.accuracy,
            "status": self.status,
            "category": self.category,
        }

    @staticmethod
    def from_my_json(j: Dict[str, Any]) -> "Passage":
        return Passage(
            id=omap(lambda i: StopId(i), j["id"]),
            last_modified=omap(lambda s: datetime.fromisoformat(s), j["last_modified"]),
            trip=omap(lambda s: TripId(s), j["trip_id"]),
            route=omap(lambda s: RouteId(s), j["route_id"]),
            vehicle=omap(lambda s: VehicleId(s), j["vehicle_id"]),
            stop=omap(lambda s: StopId(s), j["stop_id"]),
            pattern=omap(lambda s: PatternId(s), j["pattern_id"]),
            latitude=j["latitude"],
            longitude=j["longitude"],
            bearing=j["bearing"],
            time=omap(lambda t: PassageTime.from_json(t), j["time"]),
            is_deleted=j["is_deleted"],
            is_accessible=j["is_accessible"],
            has_bike_rack=j["has_bike_rack"],
            direction=j["direction"],
            congestion=j["congestion"],
            accuracy=j["accuracy"],
            status=j["status"],
            category=j["category"],
        )


class PassageTime(NamedTuple):
    arrival: Optional["ArrivalTime"]
    departure: Optional["DepartureTime"]

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "PassageTime":
        a = omap(ArrivalTime.from_json, json.get("arrival_data"))
        d = omap(DepartureTime.from_json, json.get("departure_data"))
        return cls(arrival=a, departure=d)

    def to_json(self) -> Dict[str, Any]:
        return {
            "arrival": omap(lambda a: a.to_json(), self.arrival),
            "departure": omap(lambda d: d.to_json(), self.departure),
        }

    @staticmethod
    def from_json(j: Dict[str, Any]) -> "PassageTime":
        return PassageTime(
            arrival=omap(lambda j: ArrivalTime.from_my_json(j), j.get("arrival")),
            departure=omap(lambda j: DepartureTime.from_my_json(j), j.get("departure")),
        )


@dataclass(frozen=True)
class ArrivalDeparture(object):
    T = TypeVar("T", bound="ArrivalDeparture")

    scheduled: Optional[datetime]
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

    def to_json(self) -> Dict[str, Any]:
        return {
            "scheduled": omap(lambda dt: dt.isoformat(), self.scheduled),
            "actual_or_prediction": omap(
                lambda dt: dt.isoformat(), self.actual_or_prediction
            ),
            "service_mode": self.service_mode,
            "type": self.type,
            "direction_text": self.direction_text,
        }

    @classmethod
    def from_my_json(cls: Type[T], j: Dict[str, Any]) -> T:
        return cls(
            scheduled=omap(lambda s: datetime.fromisoformat(s), j["scheduled"]),
            actual_or_prediction=omap(
                lambda s: datetime.fromisoformat(s), j["actual_or_prediction"]
            ),
            service_mode=j["service_mode"],
            type=j["type"],
            direction_text=j["direction_text"],
        )


@dataclass(frozen=True)
class ArrivalTime(ArrivalDeparture):
    pass


@dataclass(frozen=True)
class DepartureTime(ArrivalDeparture):
    pass

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
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

import pandas as pd

from busboy.geo import (
    DegreeLatitude,
    DegreeLongitude,
    LatLon,
    LonLat,
    RawLatitude,
    RawLongitude,
)
from busboy.util import Just, Maybe, Nothing, omap


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
    def from_json(route_json: Dict[str, Any]) -> Route:
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

    @property
    def lon_lat(self) -> LonLat:
        return (self.longitude, self.latitude)

    @property
    def lat_lon(self) -> LatLon:
        return (self.latitude, self.longitude)

    @classmethod
    def from_json(cls, stop_json: Dict[str, Any]) -> Stop:
        id = StopId(stop_json["duid"])
        name = stop_json["name"]
        latitude = stop_json["lat"]
        longitude = stop_json["lng"]
        number = stop_json["num"]
        return cls(id, name, latitude, longitude, number)

    @staticmethod
    def from_db_row(r: Tuple[Any, ...]) -> Stop:
        return Stop(
            id=StopId(r[0]),
            name=r[1],
            number=r[2],
            latitude=DegreeLatitude(r[3]),
            longitude=DegreeLongitude(r[4]),
        )


MyArrivalDepartureJson = Dict[str, Union[str, int, None]]
MyPassageTimeJson = Dict[str, Optional[MyArrivalDepartureJson]]
MyPassageJson = Dict[str, Union[str, float, None, MyPassageTimeJson]]
MyStopPassageResponseJson = Dict[str, List[MyPassageJson]]

DirectionTextJson = Dict[str, Union[str, int]]
ArrivalDepartureJson = Dict[str, Union[str, int, DirectionTextJson]]
DuidJson = Dict[str, Union[str, int]]
PassageJson = Dict[str, Union[str, int, bool, DuidJson, ArrivalDepartureJson]]
StopPassageResponseJson = Dict[str, Union[int, PassageJson]]


@dataclass(frozen=True)
class StopPassageResponse(object):
    passages: Tuple[Passage, ...]

    @staticmethod
    def from_json(json: Dict[str, Any]) -> StopPassageResponse:
        ps = tuple(
            Passage.from_json(pj)
            for k, pj in json["stopPassageTdi"].items()
            if k != "foo"
        )
        return StopPassageResponse(ps)

    @staticmethod
    def from_my_json(j: MyStopPassageResponseJson) -> StopPassageResponse:
        return StopPassageResponse(
            tuple(Passage.from_my_json(p) for p in j["passages"])
        )

    def to_json(self) -> MyStopPassageResponseJson:
        return {"passages": [p.to_json() for p in self.passages]}

    def trip_ids(self) -> List[Maybe[TripId]]:
        return [p.trip for p in self.passages]

    def filter(self, f: Callable[["Passage"], bool]) -> StopPassageResponse:
        return StopPassageResponse(tuple(p for p in self.passages if f(p)))

    def contains_trip(self, t: Optional[TripId]) -> bool:
        return t in {p.trip for p in self.passages}

    def positions(self) -> Iterable[Maybe[Tuple[DegreeLatitude, DegreeLongitude]]]:
        return (p.position.value for p in self.passages if isinstance(p.position, Just))

    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(
            {
                p.id.map(lambda i: i.raw).or_else(None): p.flatten()
                for p in self.passages
            },
            orient="index",
        )


@dataclass(frozen=True)
class Passage(object):
    id: Maybe[PassageId]
    last_modified: Maybe[datetime]
    trip: Maybe[TripId]
    route: Maybe[RouteId]
    vehicle: Maybe[VehicleId]
    stop: Maybe[StopId]
    pattern: Maybe[PatternId]
    latitude: Maybe[RawLatitude]
    longitude: Maybe[RawLongitude]
    bearing: Maybe[int]
    time: PassageTime
    is_deleted: Maybe[bool]
    is_accessible: Maybe[bool]
    has_bike_rack: Maybe[bool]
    direction: Maybe[int]
    congestion: Maybe[int]
    accuracy: Maybe[int]
    status: Maybe[int]
    category: Maybe[int]

    @property
    def position(self) -> Maybe[Tuple[DegreeLatitude, DegreeLongitude]]:
        return self.latitude.bind(
            lambda lat: self.longitude.map(
                lambda lon: (
                    DegreeLatitude(lat / 3_600_000),
                    DegreeLongitude(lon / 3_600_000),
                )
            )
        )

    @staticmethod
    def from_json(json: Dict[str, Any]) -> Passage:
        time = PassageTime.from_json(json)
        try:
            return Passage(
                id=Maybe.of(json.get("duid")).map(PassageId),
                last_modified=Maybe.of(json.get("last_modification_timestamp")).map(
                    lambda j: datetime.utcfromtimestamp(j / 1000)
                ),
                is_deleted=Maybe.of(json.get("is_deleted")),
                route=Maybe.of(json.get("route_duid"))
                .bind(lambda j: Maybe.of(cast(Dict[str, str], j).get("duid")))
                .map(RouteId),
                direction=Maybe.of(json.get("direction")),
                trip=Maybe.of(json.get("trip_duid"))
                .map(lambda j: cast(Dict[str, str], j))
                .bind(lambda j: Maybe.of(j.get("duid")))
                .map(TripId),
                stop=Maybe.of(json.get("stop_point_duid"))
                .map(lambda j: cast(Dict[str, str], j))
                .bind(lambda j: Maybe.of(j.get("duid")))
                .map(StopId),
                vehicle=Maybe.of(json.get("vehicle_duid"))
                .map(lambda j: cast(Dict[str, str], j))
                .bind(lambda j: Maybe.of(j.get("duid")))
                .map(VehicleId),
                time=time,
                congestion=Maybe.of(json.get("congestion_level")),
                accuracy=Maybe.of(json.get("accuracy_level")),
                status=Maybe.of(json.get("status")),
                is_accessible=Maybe.of(json.get("is_accessible")).map(bool),
                latitude=Maybe.of(json.get("latitude")),
                longitude=Maybe.of(json.get("longitude")),
                bearing=Maybe.of(json.get("bearing")),
                pattern=Maybe.of(json.get("pattern_duid"))
                .bind(lambda j: Maybe.of(cast(Dict[str, str], j).get("duid")))
                .map(PatternId),
                has_bike_rack=Maybe.of(json.get("has_bike_rack")).map(bool),
                category=Maybe.of(json.get("category")),
            )
        except KeyError as e:
            raise Exception(json, e)

    def to_json(self) -> MyPassageJson:
        return {
            "id": self.id.map(lambda i: i.raw).optional(),
            "last_modified": self.last_modified.map(
                lambda dt: dt.isoformat()
            ).optional(),
            "trip_id": self.trip.map(lambda i: i.raw).optional(),
            "route_id": self.route.map(lambda i: i.raw).optional(),
            "vehicle_id": self.vehicle.map(lambda i: i.raw).optional(),
            "stop_id": self.stop.map(lambda i: i.raw).optional(),
            "pattern_id": self.pattern.map(lambda i: i.raw).optional(),
            "latitude": self.latitude.optional(),
            "longitude": self.longitude.optional(),
            "bearing": self.bearing.optional(),
            "time": self.time.to_json(),
            "is_deleted": self.is_deleted.optional(),
            "is_accessible": self.is_accessible.optional(),
            "has_bike_rack": self.has_bike_rack.optional(),
            "direction": self.direction.optional(),
            "congestion": self.congestion.optional(),
            "accuracy": self.accuracy.optional(),
            "status": self.status.optional(),
            "category": self.category.optional(),
        }

    @staticmethod
    def from_my_json(j: MyPassageJson) -> Passage:
        return Passage(
            id=Just(PassageId(cast(str, j["id"]))),
            last_modified=Just(datetime.fromisoformat(cast(str, j["last_modified"]))),
            trip=Just(TripId(cast(str, j["trip_id"]))),
            route=Just(RouteId(cast(str, j["route_id"]))),
            vehicle=Just(VehicleId(cast(str, j["vehicle_id"]))),
            stop=Just(StopId(cast(str, j["stop_id"]))),
            pattern=Just(PatternId(cast(str, j["pattern_id"]))),
            latitude=Just(cast(int, j["latitude"])),
            longitude=Just(cast(int, j["longitude"])),
            bearing=Just(cast(int, j["bearing"])),
            time=PassageTime.from_json(cast(MyPassageTimeJson, j["time"])),
            is_deleted=Just(cast(bool, j["is_deleted"])),
            is_accessible=Just(cast(bool, j["is_accessible"])),
            has_bike_rack=Just(cast(bool, j["has_bike_rack"])),
            direction=Just(cast(int, j["direction"])),
            congestion=Just(cast(int, j["congestion"])),
            accuracy=Just(cast(int, j["accuracy"])),
            status=Just(cast(int, j["status"])),
            category=Just(cast(int, j["category"])),
        )

    def flatten(self) -> Dict[str, Any]:
        id = self.id.map(lambda i: i.raw).or_else(None)
        last_modified = self.last_modified.or_else(None)
        trip = self.trip.map(lambda i: i.raw).or_else(None)
        route = self.route.map(lambda i: i.raw).or_else(None)
        vehicle = self.vehicle.map(lambda i: i.raw).or_else(None)
        stop = self.stop.map(lambda i: i.raw).or_else(None)
        pattern = self.pattern.map(lambda i: i.raw).or_else(None)
        latitude = self.latitude.map(lambda l: l / 3_600_000).or_else(None)
        longitude = self.longitude.map(lambda l: l / 3_600_000).or_else(None)
        bearing = self.bearing.or_else(None)
        scheduled_arrival, predicted_arrival, scheduled_departure, predicted_departure = (
            self.time.flatten()
        )
        is_accessible = self.is_accessible.or_else(None)
        has_bike_rack = self.has_bike_rack.or_else(None)
        direction = self.direction.or_else(None)
        congestion = self.congestion.or_else(None)
        accuracy = self.accuracy.or_else(None)
        status = self.status.or_else(None)
        category = self.category.or_else(None)
        return {
            "id": id,
            "last_modified": last_modified,
            "trip": trip,
            "route": route,
            "vehicle": vehicle,
            "stop": stop,
            "pattern": pattern,
            "latitude": latitude,
            "longitude": longitude,
            "bearing": bearing,
            "scheduled_arrival": scheduled_arrival,
            "predicted_arrival": predicted_arrival,
            "scheduled_departure": scheduled_departure,
            "predicted_departure": predicted_departure,
            "is_accessible": is_accessible,
            "has_bike_rack": has_bike_rack,
            "direction": direction,
            "congestion": congestion,
            "accuracy": accuracy,
            "status": status,
            "category": category,
            "passage": self,
        }


@dataclass(frozen=True)
class PassageTime(object):
    arrival: Maybe[ArrivalTime]
    departure: Maybe[DepartureTime]

    @staticmethod
    def from_json(json: Dict[str, Any]) -> PassageTime:
        a = Maybe.of(json.get("arrival_data")).map(ArrivalTime.from_json)
        d = Maybe.of(json.get("departure_data")).map(DepartureTime.from_json)
        return PassageTime(arrival=a, departure=d)

    def to_json(self) -> MyPassageTimeJson:
        return {
            "arrival": self.arrival.map(lambda a: a.to_json()).optional(),
            "departure": self.departure.map(lambda d: d.to_json()).optional(),
        }

    @staticmethod
    def from_my_json(j: MyPassageTimeJson) -> PassageTime:
        return PassageTime(
            arrival=Maybe.of(j.get("arrival")).map(
                lambda j: ArrivalTime.from_my_json(j)
            ),
            departure=Maybe.of(j.get("departure")).map(
                lambda j: DepartureTime.from_my_json(j)
            ),
        )

    def flatten(
        self
    ) -> Tuple[
        Optional[datetime], Optional[datetime], Optional[datetime], Optional[datetime]
    ]:
        scheduled_arrival, predicted_arrival = self.arrival.map(
            lambda a: (a.scheduled.or_else(None), a.actual_or_prediction.or_else(None))
        ).or_else((None, None))
        scheduled_departure, predicted_departure = self.departure.map(
            lambda d: (d.scheduled.or_else(None), d.actual_or_prediction.or_else(None))
        ).or_else((None, None))
        return (
            scheduled_arrival,
            predicted_arrival,
            scheduled_departure,
            predicted_departure,
        )


@dataclass(frozen=True)
class ArrivalDeparture(object):
    T = TypeVar("T", bound="ArrivalDeparture")

    scheduled: Maybe[datetime]
    actual_or_prediction: Maybe[datetime]
    service_mode: Maybe[int]
    type: Maybe[int]
    direction_text: Maybe[str]

    @classmethod
    def from_json(cls: Type[T], json: Dict[str, Any]) -> T:
        return cls(
            scheduled=Maybe.of(json.get("scheduled_passage_time_utc")).map(
                datetime.utcfromtimestamp
            ),
            actual_or_prediction=Maybe.of(json.get("actual_passage_time_utc")).map(
                datetime.utcfromtimestamp
            ),
            service_mode=Maybe.of(json.get("service_mode")),
            type=Maybe.of(json.get("type")),
            direction_text=Maybe.of(json.get("multilingual_direction_text")).bind(
                lambda j: Maybe.of(cast(Dict[str, str], j).get("defaultValue"))
            ),
        )

    def to_json(self) -> MyArrivalDepartureJson:
        return {
            "scheduled": self.scheduled.map(lambda dt: dt.isoformat()).optional(),
            "actual_or_prediction": self.actual_or_prediction.map(
                lambda dt: dt.isoformat()
            ).optional(),
            "service_mode": self.service_mode.optional(),
            "type": self.type.optional(),
            "direction_text": self.direction_text.optional(),
        }

    @classmethod
    def from_my_json(cls: Type[T], j: MyArrivalDepartureJson) -> T:
        return cls(
            scheduled=Maybe.of(j.get("scheduled")).map(
                lambda s: datetime.fromisoformat(cast(str, s))
            ),
            actual_or_prediction=Maybe.of(j.get("actual_or_prediction")).map(
                lambda s: datetime.fromisoformat(cast(str, s))
            ),
            service_mode=Maybe.of(cast(Optional[int], j.get("service_mode"))),
            type=Maybe.of(cast(Optional[int], j.get("type"))),
            direction_text=Maybe.of(cast(Optional[str], j.get("direction_text"))),
        )


@dataclass(frozen=True)
class ArrivalTime(ArrivalDeparture):
    pass


@dataclass(frozen=True)
class DepartureTime(ArrivalDeparture):
    pass

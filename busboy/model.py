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
    Callable
)
from datetime import datetime
import json
from dataclasses import dataclass

PassageNumber = NewType('PassageNumber', int)

class StopId(NamedTuple):
    value: str

class TripId(NamedTuple):
    value: str

@dataclass(frozen=True)
class Route(object):
    id: str
    name: str
    direction: int
    direction_name: str
    number: int
    category: int

    def from_json(route_json: Dict[str, Any]) -> Union["Route", KeyError]:
        try:
            id = route_json['duid']
            name = route_json['short_name']
            direction = route_json['direction_extensions']['direction']
            number = route_json['number']
            category = route_json['category']
            direction_name = route_json['direction_extensions']['direction_name']
        except KeyError as e:
            return e
        else:
            return Route(
                id=id,
                name=name,
                direction=direction,
                number=number,
                category=category,
                direction_name=direction_name
            )

class Stop(object):
    id: str
    name: str
    latitude: float
    longitude: float
    number: int

    def __init__(self, stop_json: Dict[str, Any]) -> None:
        self.id = stop_json['duid']
        self.name = stop_json['name']
        self.latitude = stop_json['lat']
        self.longitude = stop_json['lng']
        self.number = stop_json['num']

class TripSnapshot(object):
    last_modified: datetime
    trip_id: str
    route_id: str
    vehicle_id: str
    pattern_id: str
    latitude: int
    longitude: int
    bearing: int
    is_accessible: bool
    has_bike_rack: bool
    direction: int
    congestion_level: int
    accuracy_level: int
    status: int
    category: int

    def __init__(self, passage_json: Dict[str, Any]) -> None:
        self.last_modified = datetime.utcfromtimestamp(passage_json[
            'last_modification_timestamp'] / 1000)
        self.trip_id = passage_json['trip_duid']['duid']
        self.route_id = passage_json['route_duid']['duid']
        self.vehicle_id = passage_json['vehicle_duid']['duid']
        self.pattern_id = passage_json['pattern_duid']['duid']
        self.latitude = passage_json['latitude']
        self.longitude = passage_json['longitude']
        self.bearing = passage_json['bearing']
        self.is_accessible = bool(passage_json['is_accessible'])
        self.has_bike_rack = bool(passage_json['has_bike_rack'])
        self.direction = passage_json['direction']
        self.congestion_level = passage_json['congestion_level']
        self.accuracy_level = passage_json['accuracy_level']
        self.status = passage_json['status']
        self.category = passage_json['category']

    @classmethod
    def from_file(cls, path: str, n: PassageNumber) -> 'TripSnapshot':
        with open(path, 'r') as f:
            j = json.load(f)
        return cls(j['stopPassageTdi'][f'passage_{n}'])

class StopPassageResponse(NamedTuple):
    passages: List['Passage']

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'StopPassageResponse':
        ps = [Passage.from_json(pj) for k, pj in json['stopPassageTdi'].items() if k != 'foo']
        return cls(ps)

class Passage(NamedTuple):
    id: str
    last_modified: datetime
    trip: str
    route: str
    vehicle: Optional[str]
    stop: str
    pattern: Optional[str]
    latitude: float
    longitude: float
    bearing: int
    time: 'PassageTime'
    is_deleted: bool
    is_accessible: Optional[bool]
    has_bike_rack: Optional[bool]
    direction: int
    congestion: Optional[int]
    accuracy: int
    status: int
    category: Optional[int]

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'Passage':
        time = PassageTime.from_json(json)
        try:
            return cls(
                id = json['duid'],
                last_modified = datetime.utcfromtimestamp(json['last_modification_timestamp'] / 1000),
                is_deleted = json['is_deleted'],
                route = json['route_duid']['duid'],
                direction = json['direction'],
                trip = json['trip_duid']['duid'],
                stop = json['stop_point_duid']['duid'],
                vehicle = omap(lambda j: j.get('duid'), json.get('vehicle_duid')), # type: ignore
                time = time,
                congestion = json.get('congestion_level'),
                accuracy = json['accuracy_level'],
                status = json['status'],
                is_accessible = omap(bool, json.get('is_accessible')),
                latitude = json['latitude'],
                longitude = json['longitude'],
                bearing = json['bearing'],
                pattern = omap(lambda j: j.get('duid'), json.get('pattern_duid')),
                has_bike_rack = omap(bool, json.get('has_bike_rack')),
                category = json.get('category')
            )
        except KeyError as e:
            raise Exception(json, e)

class PassageTime(NamedTuple):
    arrival: Optional['ArrivalTime']
    departure: Optional['DepartureTime']

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'PassageTime':
        a = omap(ArrivalTime.from_json, json.get('arrival_data', None))
        d = omap(DepartureTime.from_json, json.get('departure_data', None))
        return cls(arrival=a, departure=d)

class ArrivalDeparture(NamedTuple):
    scheduled: int
    actual_or_prediction: Optional[datetime]
    service_mode: int
    type: int
    direction_text: str

    @classmethod
    def from_json(cls: Any, json: Dict[str, Any]) -> Any:
        return cls(
            scheduled = datetime.utcfromtimestamp(json['scheduled_passage_time_utc']),
            actual_or_prediction = omap(datetime.utcfromtimestamp, json.get('actual_passage_time_utc')),
            service_mode = json['service_mode'],
            type = json['type'],
            direction_text = json['multilingual_direction_text']['defaultValue'],
        )

class ArrivalTime(ArrivalDeparture):
    pass

class DepartureTime(ArrivalDeparture):
    pass

A = TypeVar('A')
B = TypeVar('B')

def omap(f: Callable[[A], B], x: Optional[A]) -> Optional[B]:
    return None if x is None else f(x)

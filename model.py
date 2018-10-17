from typing import Dict, NewType, Any
from datetime import datetime
import json

PassageNumber = NewType('PassageNumber', int)

class Route(object):
    id: str
    name: str
    direction: int
    number: int
    category: int

    def __init__(self, route_json: Dict[str, Any]) -> None:
        self.id = route_json['duid']
        self.name = route_json['short_name']
        self.direction = route_json['direction_extensions']['direction']
        self.number = route_json['number']
        self.category = route_json['category']

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

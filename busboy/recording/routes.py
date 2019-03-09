import csv
import datetime as dt
import json
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple, cast

from busboy import constants
from busboy.apis import stop_passage
from busboy.geo import DegreeLatLon
from busboy.model import StopId, VehicleId
from busboy.util import Maybe, interval


def main() -> None:
    cce = constants.church_cross_east
    filename = "resources/routes/route.csv"
    record = RouteRecord({})
    try:
        for t in interval(2):
            check_for_updates(StopId(cce), record)
    finally:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["vehicle", "time", "latitude", "longitude"])
            for vehicle, time, coords in record.entries():
                if coords is not None:
                    latitude, longitude = coords
                writer.writerow([vehicle, time, latitude, longitude])

@dataclass
class RouteRecord(object):
    positions: Dict[Maybe[VehicleId], List[Tuple[dt.datetime, Maybe[DegreeLatLon]]]]

    def to_json(self) -> Dict[str, List[Tuple[str, Optional[DegreeLatLon]]]]:
        output: Dict[str, List[Tuple[str, Optional[DegreeLatLon]]]] = {}
        for vehicle, records in self.positions.items():
            id_text = vehicle.map(lambda v: v.raw).or_else("<no id>")
            output_records = []
            for record in records:
                time = record[0].isoformat()
                coords = record[1].or_else(None)
                output_records.append((time, coords))
            output[id_text] = output_records
        return output

    def entries(self) -> Iterator[Tuple[Optional[str], str, Optional[DegreeLatLon]]]:
        for vehicle, records in self.positions.items():
            id_text = vehicle.map(lambda v: v.raw).or_else("<no id>")
            for record in records:
                time = record[0].isoformat()
                coords = record[1].or_else(None)
                yield (id_text, time, coords)



def check_for_updates(stop: StopId, record: RouteRecord) -> None:
    time = dt.datetime.now()
    response = stop_passage(stop)
    for passage in response.passages:
        position = cast(Maybe[DegreeLatLon], passage.longitude.bind(
            lambda lon: passage.latitude.map(
                lambda lat: (lat / 3_600_000, lon / 3_600_000)
            )
        ))
        if passage.vehicle not in record.positions:
            record.positions.setdefault(passage.vehicle, []).append((time, position))
        else:
            old_position = record.positions[passage.vehicle][-1][1]
            if position != old_position:
                record.positions.setdefault(passage.vehicle, []).append((time, position))

if __name__ == '__main__':
    import warnings
    warnings.simplefilter("ignore")
    main()

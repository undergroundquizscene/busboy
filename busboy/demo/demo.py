import warnings
from collections import deque
from datetime import datetime, time, timedelta
from time import sleep
from typing import Any, Deque, Dict, List, Set, Union

import pandas as pd
from pandas import DataFrame
from sklearn.dummy import DummyRegressor

import busboy.database as db
import busboy.prediction as prediction
from busboy.apis import stop_passage
from busboy.constants import example_stops
from busboy.database import BusSnapshot, default_connection, stop_by_id
from busboy.geo import DegreeLatitude, DegreeLongitude
from busboy.model import Passage, PassageId, RouteId, StopId, VehicleId
from busboy.prediction import RouteSection
from busboy.prediction.pandas import travel_times
from busboy.prediction.sklearn import journeys as separate_journeys
from busboy.util import Just, Maybe, Right
from busboy.util.notebooks import read_preprocessed_data


def main() -> None:
    warnings.simplefilter("ignore")
    opp_wgb_id = StopId("7338653551721425381")
    wgb_id = StopId("7338653551721425841")
    church_cross_east = example_stops["cce"].id
    church_cross_west = example_stops["ccw"].id
    stop = stop_by_id(default_connection(), church_cross_west).value
    routes_by_id = db.routes_by_id()
    routes_by_name = db.routes_by_name()
    timetables = [tt.value for tt in db.timetables(routes_by_name["220"].id) if isinstance(tt, Right)]
    variants = {v for timetable in timetables for v in timetable.variants}
    filtered_variants = {v for v in variants if stop in v.stops}
    timetable = sorted(filtered_variants, key=lambda v: len(v.stops))[-1]
    route_sections = list(prediction.route_sections(timetable.stops))
    snapshots: Dict[VehicleId, List[BusSnapshot]] = {}
    preprocessed_by_timetable = dict(read_preprocessed_data("220"))
    preprocessed = preprocessed_by_timetable[timetable]
    predictors = train_average_predictors(preprocessed, stop.name + " [arrival]")
    responses: Deque[DataFrame] = deque(maxlen=360)
    arrived_passages: Dict[PassageId, datetime] = {}
    while True:
        try:
            print("-" * 80)
            loop_start = datetime.now()
            response = stop_passage(stop.id).dataframe().sort_values("scheduled_arrival")
            response["poll_time"] = loop_start
            response = response[response["predicted_arrival"] > loop_start - timedelta(minutes=10)]
            response["route"] = response["route"].apply(lambda r: Maybe.of(routes_by_id.get(RouteId(r))).map(lambda r: r.name).or_else(None))
            response = response[response["route"] == "220"]
            response["sections"] = [containing_sections(route_sections, r.longitude, r.latitude) for r in response.itertuples()]
            arrived = [arrived_passages.get(p.id, pd.NaT) for p in response["passage"]]
            my_predictions = [pd.NaT] * len(response["passage"])
            for row, passage in enumerate(response["passage"]):
                if isinstance(passage.vehicle, Just):
                    snapshot = BusSnapshot.from_passage(passage, loop_start)
                    snapshots.setdefault(passage.vehicle.value, []).append(snapshot)
                    # print(f"Snapshots for vehicle {passage.vehicle}: {len(snapshots[passage.vehicle.value])}")
                    timetable_journeys = separate_journeys(
                        snapshots[passage.vehicle.value],
                        {timetable},
                        {timetable: route_sections},
                    )
                    journeys = timetable_journeys.get(timetable)
                    if journeys is not None:
                        journeys = journeys.fillna(value=pd.NaT)
                        nonempty = journeys.loc[:, journeys.notna().any()]
                        if len(nonempty.columns) > 0:
                            last = nonempty.columns[-1]
                            if last in predictors:
                                predicted_travel_time = predictors[last].predict(journeys)
                                predicted_arrival = journeys[last].iloc[-1] + timedelta(seconds=predicted_travel_time[-1])
                                my_predictions[row] = predicted_arrival
                            if (stop.name + " [arrival]") in nonempty.columns and passage.id.value not in arrived_passages:
                                # discard journey data
                                arrival_time = nonempty[stop.name + " [arrival]"].iloc[-1]
                                arrived[row] = arrival_time
                                arrived_passages[passage.id.value] = arrival_time
                                # display prediction stats
                                evaluate_predictions(responses, passage, arrival_time)
            response["average_time_prediction"] = my_predictions
            response["arrived"] = arrived
            display(response)
            responses.appendleft(response)
            sleep(max(0, 10 - (datetime.now() - loop_start).total_seconds()))
        except KeyboardInterrupt:
            print("Exiting")
            return
        except Exception as e:
            print("Got an exception: {e}")
            print("Continuing…")
            sleep(max(0, 10 - (datetime.now() - loop_start).total_seconds()))


def evaluate_predictions(
    responses: Deque[DataFrame],
    passage: Passage,
    arrival_time: datetime,
) -> None:
    print("=" * 100)
    responses_with_passage = [
        r for r in responses
        if passage.id.value.raw in r.index
        and r["average_time_prediction"].loc[passage.id.value.raw] is not pd.NaT
    ]
    print(f"Bus {passage.vehicle} arrived – {len(responses_with_passage)} snapshots.")
    df = pd.DataFrame()
    df["poll_time"] = [r["poll_time"].loc[passage.id.value.raw] for r in responses_with_passage]
    df.set_index("poll_time", inplace=True)
    df.sort_index(inplace=True)
    df["prediction"] = [r["average_time_prediction"].loc[passage.id.value.raw] for r in responses_with_passage]
    df["real-time"] = [r["predicted_arrival"].loc[passage.id.value.raw] for r in responses_with_passage]
    df["arrival_time"] = arrival_time
    df["error (s)"] = df["prediction"] - arrival_time
    df["error (s)"] = df["error (s)"].apply(lambda td: td.total_seconds())
    df["real-time error (s)"] = df["real-time"] - arrival_time
    df["real-time error (s)"] = df["real-time error (s)"].apply(lambda td: td.total_seconds())

    df["prediction"] = df["prediction"].apply(to_time)
    df["arrival_time"] = df["arrival_time"].apply(to_time)
    df["real-time"] = df["real-time"].apply(to_time)
    df["poll_time"] = df["poll_time"].apply(to_time)
    print(df)
    print("=" * 100)


def train_average_predictors(journeys: DataFrame, target: str) -> Dict[str, Any]:
    first_column = journeys.columns[0]
    target_index = journeys.columns.get_loc(target)
    output = {}
    for last_index in range(target_index):
        last = journeys.columns[last_index]
        output[last] = train_average_predictor(journeys, last, target)
    return output


def train_average_predictor(journeys: DataFrame, last: str, target: str) -> Any:
    journeys = journeys[pd.notnull(journeys[target]) & pd.notnull(journeys[last])]
    y = travel_times(journeys, [], last, target).astype("int64") / 1_000_000_000
    predictor = DummyRegressor(strategy="median")
    predictor.fit(journeys, y)
    return predictor

def to_time(dt: Union[datetime, Any]) -> Union[time, Any]:
    if isinstance(dt, datetime) and dt is not pd.NaT:
        time = dt.time()
        return time.replace(second = round(time.second), microsecond=0)
    else:
        return dt

def display(df: DataFrame) -> None:
    df["scheduled"] = df["scheduled_arrival"].apply(to_time)
    df["real-time"] = df["predicted_arrival"].apply(to_time)
    df["prediction"] = df["average_time_prediction"].apply(to_time)
    df["arrived_at"] = df["arrived"].apply(to_time)
    print(df[["route", "vehicle", "scheduled", "real-time", "prediction", "sections", "arrived_at"]])


def show_passage(passage: Passage) -> str:
    vehicle = passage.vehicle.map(lambda i: i.raw).or_else("None")
    position = passage.position.map(str).or_else("None")
    scheduled = passage.time.arrival.bind(lambda t: t.scheduled).map(lambda t: t.time().isoformat()).or_else("None")
    predicted = passage.time.arrival.bind(lambda t: t.actual_or_prediction).map(lambda t: t.time().isoformat()).or_else("None")
    return f"{vehicle:^19} - {scheduled:^8} - {predicted:^8}"

def containing_sections(
    sections: List[RouteSection],
    longitude: DegreeLongitude,
    latitude: DegreeLatitude,
) -> Set[int]:
    return {
        i
        for i, section in enumerate(sections)
        if section.contains(longitude, latitude)
    }



if __name__ == '__main__':
    main()

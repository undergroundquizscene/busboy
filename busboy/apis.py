import json
from functools import singledispatch
from typing import Any, Dict, List, Optional, Set, Union

import requests
from bs4 import BeautifulSoup

from busboy.constants import stop_passage_tdi
from busboy.model import (
    IncompleteRoute,
    Route,
    Stop,
    StopId,
    StopPassageResponse,
    TripId,
)


def stops() -> List[Stop]:
    """Queries the API for the list of all stops."""
    j = from_var(
        requests.get("http://buseireann.ie/inc/proto/bus_stop_points.php").text
    )
    return [Stop.from_json(s) for k, s in j["bus_stops"].items()]


def routes() -> List[Union[Route, IncompleteRoute]]:
    """Queries the API for the list of all routes."""
    j = from_var(requests.get("http://buseireann.ie/inc/proto/routes.php").text)
    return [Route.from_json(r) for k, r in j["routeTdi"].items() if k != "foo"]


def from_var(r: str) -> Dict[str, Any]:
    """Strips a var declaration and returns the json assigned to it."""
    split = r.partition("{")
    string = split[1] + split[2][:-1]
    return json.loads(string)


def trips(s: StopId) -> Set[TripId]:
    """Queries the API for a stop and returns the ids of the trips in the response."""
    response = stop_passage(s)
    return {TripId(p.trip) for p in response.passages}


def stop_ids() -> Set[str]:
    """Gets all stop duids from the rest api."""
    return {s.id for s in stops()}


def routes_at_stop(stop: str) -> Set[str]:
    stop_response = requests.get(stop_passage_tdi, params={"stop_point": stop}).json()
    return {
        p["route_duid"]["duid"]
        for k, p in stop_response["stopPassageTdi"].items()
        if k != "foo"
    }


def routes_at_stops() -> Dict[str, Set[str]]:
    rs = {}
    for i, s in enumerate(stop_ids()):
        try:
            print(f"Doing stop {i} (of about 5,444)")
            rs[s] = routes_at_stop(s)
        except Exception:
            print(f"Got an error on stop {i} ({s})!")
    return rs


@singledispatch
def stop_passage(params: Dict[str, Union[StopId, TripId]]) -> StopPassageResponse:
    j = requests.get(stop_passage_tdi, params=params).json()
    return StopPassageResponse.from_json(j)


@stop_passage.register
def sp_stop(s: StopId) -> StopPassageResponse:
    return stop_passage({"stop_point": s.raw})


@stop_passage.register
def sp_trip(t: TripId) -> StopPassageResponse:
    return stop_passage({"trip": t.raw})


def route_stops(r: int):
    soup = make_soup(r)
    tables = get_tables(soup)

    def right_th(e):
        return e.name == "th" and e.parent.parent.name == "tbody"

    stop_cells = [t["table"].find_all(right_th) for t in tables]
    stop_names = [
        [c.string.strip() for c in cs if c.string is not None] for cs in stop_cells
    ]
    return stop_names


def get_tables(soup):
    def right_id(i):
        return i is not None and i.startswith("table-spreadsheet")

    ts = soup.find_all(id=right_id)

    def table_id(t):
        return t.thead.tr.th.next_sibling.string.strip()

    tables = [{"table": t, "route": table_id(t)} for t in ts]
    return tables


def make_soup(r: int):
    stops_endpoint = "http://buseireann.ie/inner.php?id=406"
    html = requests.get(
        stops_endpoint,
        params={"form-view-timetables-route": r, "form-view-timetables-submit": 1},
    ).text
    return BeautifulSoup(html, features="html.parser")


def route_stops_to_file(stops):
    import json

    f = open("resources/stoplists.json")
    f = open("resources/stoplists.json", "w")
    json.dump(stops, f)
    json.dump(stops, f)
    json.dump(stops, f, indent=4)
    f.close()
    f = open("resources/stoplists.json", "w")
    json.dump(stops, f, indent=4)
    f.close()
    f = open("resources/stoplists.json", "w")
    json.dump(stops, f, indent=2)
    f.close()

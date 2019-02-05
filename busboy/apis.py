from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import time
from functools import singledispatch
from itertools import chain, islice, zip_longest
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

import requests
from bs4 import BeautifulSoup, ResultSet
from bs4.element import Tag

from busboy.constants import stop_passage_tdi
from busboy.model import Route, Stop, StopId, StopPassageResponse, TripId
from busboy.util import Just, Maybe, Nothing, drop

timetable_endpoint = "http://buseireann.ie/inner.php?id=406"


def stops() -> List[Stop]:
    """Queries the API for the list of all stops."""
    j = from_var(
        requests.get("http://buseireann.ie/inc/proto/bus_stop_points.php").text
    )
    return [Stop.from_json(s) for k, s in j["bus_stops"].items()]


def routes() -> List[Route]:
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
def stop_passage(params: Dict[str, str]) -> StopPassageResponse:
    j = requests.get(stop_passage_tdi, params=params).json()
    return StopPassageResponse.from_json(j)


@stop_passage.register
def sp_stop(s: StopId) -> StopPassageResponse:
    return stop_passage({"stop_point": s.raw})


@stop_passage.register
def sp_trip(t: TripId) -> StopPassageResponse:
    return stop_passage({"trip": t.raw})


def web_timetables(route_name: str) -> List[WebTimetable]:
    html = requests.get(
        timetable_endpoint,
        params={
            "form-view-timetables-route": route_name,
            "form-view-timetables-submit": 1,
        },
    ).text
    return WebTimetable.from_page(BeautifulSoup(html, features="html.parser"))


def timetables(route_name: str) -> List[Timetable]:
    return [Timetable.from_web_timetable(wt) for wt in web_timetables(route_name)]


@dataclass(frozen=True)
class WebTimetable(object):
    table: Tag

    @staticmethod
    def from_page(soup: BeautifulSoup) -> List[WebTimetable]:
        def right_id(i: str) -> bool:
            return i is not None and i.startswith("table-spreadsheet")

        return [WebTimetable(t) for t in soup.find_all(id=right_id)]

    def routes(self) -> Set[str]:
        return {
            c.string
            for c in self.table.thead.tr("th")
            if c.string is not None and c.string != "Service Number"
        }

    def stop_names(self) -> List[str]:
        return [r.th.string for r in self.table.tbody("tr")]

    def columns(self) -> Iterable[Iterable[Tag]]:
        rows = (r for r in self.table.tbody("tr"))
        tds = chain([drop(1, self.table.thead.tr("th"))], (r("td") for r in rows))
        return zip_longest(*tds)

    def times(self) -> List[List[Maybe[time]]]:
        return [[WebTimetable.cell_time(c) for c in cells] for cells in self.columns()]

    def _times(self) -> Iterable[Iterable[Maybe[time]]]:
        return ((WebTimetable.cell_time(c) for c in cells) for cells in self.columns())

    def stop_times(self) -> List[List[Tuple[str, Maybe[time]]]]:
        return [list(zip(self.stop_names(), c)) for c in self._times()]

    def _stop_times(self) -> Iterable[Iterable[Tuple[str, Maybe[time]]]]:
        return (zip(self.stop_names(), c) for c in self._times())

    def variants(self) -> Set[Tuple[str, Tuple[str, ...]]]:
        vs = set()
        for column in self.columns():
            route = list(islice(column, 1))[0].string
            v = []
            for stop, cell in zip(self.stop_names(), drop(1, column)):
                time = self.cell_time(cell).map(lambda t: True)
                for t in time:
                    v.append(stop)
            if v:
                vs.add((route, tuple(v)))
        return vs

    @staticmethod
    def cell_time(t: Tag) -> Maybe[time]:
        contents = "".join([s for s in t.stripped_strings])
        try:
            return Just(time.fromisoformat(contents))
        except ValueError:
            return Nothing()


def tables_by_route(rs: ResultSet) -> List[Dict[str, Any]]:
    def table_id(t: Tag) -> str:
        return t.thead.tr.th.next_sibling.next_sibling.string.strip()

    return [{"table": t, "route": table_id(t)} for t in rs]


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


@dataclass(frozen=True)
class Timetable(object):
    caption: str
    variants: Set[TimetableVariant]

    def routes(self) -> Set[str]:
        return {v.route for v in self.variants}

    @staticmethod
    def from_web_timetable(wt: WebTimetable) -> Timetable:
        return Timetable(
            wt.table.caption.string,
            {TimetableVariant(t[0], t[1]) for t in wt.variants()},
        )


@dataclass(frozen=True)
class TimetableVariant(object):
    route: str
    stops: Tuple[str, ...]

from bs4 import BeautifulSoup
import requests
from typing import List, Dict

import busboy.rest as api
import busboy.model as m


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


def route_stops_to_file():
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


import concurrent.futures as cf
import datetime as dt
from threading import Event
from dataclasses import dataclass

@dataclass
class PollResult(object):
    time: dt.datetime
    results: Dict[m.StopId, m.StopPassageResponse]

def poll_continuously(stops: List[m.StopId], frequency: float) -> List[PollResult]:
    prs = []
    terminate = Event()
    while not terminate.is_set():
        try:
            t = dt.datetime.now()
            prs.append(PollResult(t, poll_stops(stops)))
            print(f"Cycled at {t}, waiting…")
            terminate.wait(frequency)
        except KeyboardInterrupt:
            print("Returning…")
            terminate.set()
    return prs

def poll_stops(stops: List[m.StopId]) -> Dict[m.StopId, m.StopPassageResponse]:
    with cf.ThreadPoolExecutor(max_workers=60) as executor:
        future_to_stop = {executor.submit(api.stop_passage, s): s for s in stops}
        sprs = {}
        for f in cf.as_completed(future_to_stop):
            s = future_to_stop[f]
            try:
                spr = f.result()
            except Exception as e:
                print(f"Got exception {e} on stop {s}")
            else:
                sprs[s] = spr
        return sprs

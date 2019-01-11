from bs4 import BeautifulSoup
import requests


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

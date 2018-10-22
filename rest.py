import requests
from typing import Dict, Any, Set
import json
from constants import stop_passage_tdi

def stops() -> Dict[str, Any]:
    """Gets the API response for every stop."""
    response = requests.get("http://buseireann.ie/inc/proto/bus_stop_points.php")
    split = response.text.partition('{')
    string = split[1] + split[2][:-1]
    stopJson = json.loads(string)['bus_stops']
    return {s['duid']: s for k, s in stopJson.items()}

def stop_ids() -> Set[str]:
    """Gets all stop duids from the rest api."""
    return {s for s in stops()}

def routes_at_stop(stop):
    stop_response = requests.get(stop_passage_tdi,
        params = {'stop_point': stop}).json()
    return {p['route_duid']['duid'] for k, p in stop_response['stopPassageTdi'].items() if k != 'foo'}

def routes_at_stops():
    rs = {}
    for i, s in enumerate(stop_ids()):
        try:
            print(f'Doing stop {i} (of about 5,444)')
            rs[s] = routes_at_stop(s)
        except Exception:
            print(f'Got an error on stop {i} ({s})!')
    return rs

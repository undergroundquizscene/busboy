import ipyleaflet as lf
import pandas as pd
from typing import List


import busboy.database as db


def default_map() -> lf.Map:
    return lf.Map(center=(51.89217, -8.55789), zoom=13)


def trip_markers(tps: db.TripPoints) -> List[lf.Marker]:
    return [
        lf.Marker(
            location=(tp.latitude / 3600000, tp.longitude / 3600000),
            draggable=False,
            title=tp.time.time().isoformat(),
        )
        for tp in tps.points
    ]


def markers(df: pd.DataFrame) -> List[lf.Marker]:
    return [
        lf.Marker(
            location=(r.latitude, r.longitude),
            draggable=False,
            title=r.Index.time().isoformat(),
        )
        for r in df.itertuples()
    ]

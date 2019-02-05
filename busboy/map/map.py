from typing import List, Optional

import geopy.distance as gpd
import pandas as pd
import shapely.geometry as sg

import busboy.database as db
import busboy.model as m
import ipyleaflet as lf


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


class Map(object):
    """A wrapper for a leaflet map."""

    def __init__(self, delete=True) -> None:
        self.map = default_map()
        self.active_markers = []
        self.markers = {}
        self.delete = delete
        self.layers = []

    def create_markers(self, tps: db.TripPoints) -> None:
        if self.markers.get(tps.id) is None:
            self.markers[tps.id] = trip_markers(tps)

    def create_markers_df(self, df: pd.DataFrame) -> None:
        t = df.iloc[0].trip
        if t not in self.markers:
            self.markers[t] = [
                lf.Marker(
                    location=(r.latitude, r.longitude),
                    draggable=False,
                    title=r.Index.isoformat(),
                )
                for r in df.itertuples()
            ]

    def clear_markers(self) -> None:
        for mark in self.active_markers:
            self.map.remove_layer(mark)

    def add_markers(self, t: m.TripId) -> None:
        for mark in self.markers[t]:
            self.map.add_layer(mark)
        self.active_markers = self.markers[t]

    def display(self, tps: db.TripPoints) -> None:
        self.create_markers(tps)
        if self.delete:
            self.clear_markers()
        self.add_markers(tps.id)

    def display_df(self, df: pd.DataFrame) -> None:
        if self.delete:
            self.clear_markers()
        self.create_markers_df(df)
        self.add_markers(df.iloc[0].trip)

    def add_marker(self, p: sg.Point, tooltip: str = "") -> None:
        self.add_layer(lf.Marker(location=p.coords[0], draggable=False, title=tooltip))

    def add_polygon(self, p: sg.Polygon) -> None:
        self.add_layer(
            lf.Polygon(locations=[list(p.exterior.coords), list(p.interiors)])
        )

    def add_layer(self, l: lf.Layer) -> None:
        self.layers.append(l)
        self.map.add_layer(l)

    def clear_layers(self) -> None:
        for l in self.layers:
            self.map.remove_layer(l)


def road_cover(df: pd.DataFrame, interval: float) -> pd.DataFrame:
    used = set()
    for r in df.itertuples():
        will_use = True
        for u in used:
            if (
                gpd.distance((u.latitude, u.longitude), (r.latitude, r.longitude)).m
                < interval
            ):
                will_use = False
                break

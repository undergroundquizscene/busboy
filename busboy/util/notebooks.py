"""
Utility functions for jupyter notebooks.
"""
import time
from collections import deque
from os import scandir
from typing import Callable, Deque, Iterable, Iterator, List, Tuple

import ipyleaflet as lf
import pandas as pd

import busboy.database as db
import busboy.prediction as prediction
from busboy.apis import Timetable, TimetableVariant
from busboy.database import BusSnapshot
from busboy.map.map import Map
from busboy.util import Right, drop


def snapshot_to_marker(entry: BusSnapshot) -> lf.Marker:
    return lf.Marker(
        location=(entry.latitude, entry.longitude),
        draggable=False,
        title=entry.poll_time.time().isoformat(),
    )


def plot_entries(
    m: Map,
    snapshots: List[BusSnapshot],
    interval: float = 0.1,
    initial_delay: float = 0.5,
    snapshot_to_layer: Callable[[BusSnapshot], lf.Layer] = snapshot_to_marker,
    clear: bool = True,
) -> None:
    """Displays a list of snapshots gradually on a leaflet map."""
    time.sleep(initial_delay)
    if clear:
        m.clear_layers()
    last = None
    for snapshot in sorted(snapshots, key=lambda e: e.poll_time):
        m.add_layer(snapshot_to_layer(snapshot))
        if last is None or snapshot.poll_time != last:
            time.sleep(interval)
        last = snapshot.poll_time


def plot_snapshot_trail(
    m: Map,
    snapshots: List[BusSnapshot],
    trail_size: int = 10,
    interval: float = 0.1,
    initial_delay: float = 1,
) -> None:
    time.sleep(initial_delay)
    m.clear_layers()
    trail: Deque[Tuple[BusSnapshot, lf.Marker]] = deque()
    for snapshot in sorted(snapshots, key=lambda e: e.poll_time):
        if len(trail) == 0 or trail[-1][0].poll_time != snapshot.poll_time:
            time.sleep(interval)
        trail.append(
            (
                snapshot,
                m._add_marker(
                    snapshot.latitude,
                    snapshot.longitude,
                    snapshot.poll_time.time().isoformat(),
                ),
            )
        )
        while len(trail) > trail_size:
            old_snapshot, layer = trail.popleft()
            m.remove_layer(layer)


def show_timetables(map: Map, timetables: List[Timetable]) -> None:
    for i, timetable in enumerate(timetables):
        for j, variant in enumerate(timetable.variants):
            group = lf.LayerGroup(name=f"{timetable.caption}, variant {j}")
            for stop in variant.stops:
                group.add_layer(
                    lf.Marker(
                        location=(stop.latitude, stop.longitude),
                        draggable=False,
                        title=stop.name,
                    )
                )
            map.add_layer(group)
            section_group = lf.LayerGroup(
                name=f"(Shapes) {timetable.caption}, variant {j}"
            )
            for section in prediction.route_sections(variant.stops):
                p = section.polygon
                section_group.add_layer(
                    lf.Polygon(
                        locations=[list(p.exterior.coords), list(p.interiors)],
                        color="blue",
                    )
                )
            map.add_layer(section_group)


def read_preprocessed_data(
    route_name: str
) -> List[Tuple[TimetableVariant, pd.DataFrame]]:
    rbn = db.routes_by_name()
    route_id = rbn[route_name].id
    timetables = db.timetables(route_id)
    timetable_variants = {
        t
        for timetable in timetables
        for t in timetable.value.variants
        if isinstance(timetable, Right)
    }
    dfs = []
    with scandir("data") as dir:
        for entry in dir:
            if entry.name.startswith(f"{route_name}-preprocessed"):
                df = pd.read_csv(entry.path, index_col=0).astype("datetime64")
                for variant in timetable_variants:
                    if list(df.columns) == list(
                        column_names(stop.name for stop in variant.stops)
                    ):
                        dfs.append((variant, df))
                        break
    return dfs


def column_names(stop_names: Iterable[str]) -> Iterator[str]:
    for name in stop_names:
        yield f"{name} [arrival]"
        yield f"{name} [departure]"

"""
Utility functions for jupyter notebooks.
"""
import time
from collections import deque
from typing import Callable, Deque, List, Tuple

import ipyleaflet as lf

import busboy.prediction as prediction
from busboy.apis import Timetable
from busboy.database import BusSnapshot
from busboy.map.map import Map


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

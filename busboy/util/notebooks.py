"""
Utility functions for jupyter notebooks.
"""
import time
from typing import List

from busboy.database import DatabaseEntry
from busboy.map.map import Map


def plot_entries(m: Map, entries: List[DatabaseEntry], interval: float = 0.1, initial_delay: float = 0.5) -> None:
    """Displays a list of entries gradually on a leaflet map."""
    time.sleep(initial_delay)
    m.clear_layers()
    last = None
    for entry in sorted(entries, key = lambda e: e.poll_time):
        m._add_marker(entry.latitude, entry.longitude, entry.poll_time.time().isoformat())
        if last is None or entry.poll_time != last:
            time.sleep(interval)
        last = entry.poll_time

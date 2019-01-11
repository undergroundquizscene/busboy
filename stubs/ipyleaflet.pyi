import typing as t
from dataclasses import dataclass


@dataclass
class Map(object):
    center: t.Tuple[float, float]
    zoom: int
    ...


@dataclass
class Marker(object):
    location: t.Tuple[float, float]
    draggable: bool
    title: str
    ...

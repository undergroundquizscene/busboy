import typing as t
from dataclasses import dataclass
@dataclass
class Map(object):
    center: t.Tuple[float, float]
    zoom: int
    def add_layer(self, l: Layer) -> None: ...
    def remove_layer(self, l: Layer) -> None: ...

@dataclass
class Marker(Layer):
    location: t.Tuple[float, float]
    draggable: bool
    title: str

@dataclass
class Circle(Layer):
    location: t.Tuple[float, float]
    radius: float
    color: str
    fill_color: str

class Layer(object): ...

@dataclass
class Polygon(Layer):
    locations: t.List[t.Union[t.Tuple[float, float], t.List[t.Tuple[float, float]]]]

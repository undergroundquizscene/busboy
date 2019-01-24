import readline
import rlcompleter
from typing import Callable, Optional, Tuple, TypeVar


def pipenv_tab_completion() -> None:
    readline.parse_and_bind("tab: complete")


A = TypeVar("A")
B = TypeVar("B")


def swap(t: Tuple[A, B]) -> Tuple[B, A]:
    return (t[1], t[0])


def omap(f: Callable[[A], B], x: Optional[A]) -> Optional[B]:
    return None if x is None else f(x)


def oget(x: Optional[A], a: A) -> A:
    return a if x is None else x

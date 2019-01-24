import readline
import rlcompleter
from typing import Tuple, TypeVar


def pipenv_tab_completion() -> None:
    readline.parse_and_bind("tab: complete")


A = TypeVar("A")
B = TypeVar("B")


def swap(t: Tuple[A, B]) -> Tuple[B, A]:
    return (t[1], t[0])

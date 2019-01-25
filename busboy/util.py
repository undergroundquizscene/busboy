import readline
import rlcompleter
from itertools import islice, tee
from typing import Callable, Iterable, List, Optional, Tuple, TypeVar


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


def pairwise(xs: Iterable[A]) -> Iterable[Tuple[A, A]]:
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(xs)
    next(b, None)
    return zip(a, b)


def take(n: int, iterable: Iterable[A]) -> List[A]:
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))

from __future__ import annotations

import readline
import rlcompleter
from dataclasses import dataclass
from functools import partial
from itertools import islice, tee
from typing import (
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)


def pipenv_tab_completion() -> None:
    readline.parse_and_bind("tab: complete")


A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
E = TypeVar("E")


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


def drop(n: int, iterable: Iterable[A]) -> Iterable[A]:
    """Skip the first n items of an iterable"""
    return islice(iterable, n, None)


class Maybe(Generic[A]):
    def __iter__(self) -> Iterator[A]:
        if isinstance(self, Just):
            return iter([self.value])
        else:
            return iter([])

    def map(self, f: Callable[[A], B]) -> Maybe[B]:
        if isinstance(self, Just):
            return Just(f(self.value))
        else:
            return cast(Maybe[B], self)

    def bind(self, f: Callable[[A], Maybe[B]]) -> Maybe[B]:
        if isinstance(self, Just):
            return f(self.value)
        else:
            return cast(Maybe[B], self)

    def bind_optional(self, f: Callable[[A], Optional[B]]) -> Maybe[B]:
        return self.bind(lambda a: Maybe.of(f(a)))

    def lift(self, f: Callable[[A, B], C], b: Maybe[B]) -> Maybe[C]:
        return b.ap(self.map(lambda a: partial(f, a)))

    def ap(self, f: Maybe[Callable[[A], B]]) -> Maybe[B]:
        return self.bind(lambda a: f.map(lambda g: g(a)))

    @staticmethod
    def of(x: Optional[A]) -> Maybe[A]:
        if x is None:
            return Nothing()
        else:
            return Just(x)

    def get(self, default: B) -> Union[A, B]:
        if isinstance(self, Just):
            return self.value
        else:
            return default

    def optional(self) -> Optional[A]:
        return self.get(None)

    def either(self, default: E) -> Either[E, A]:
        if isinstance(self, Just):
            return Right(self.value)
        else:
            return Left(default)


@dataclass(frozen=True, order=True)
class Just(Maybe[A]):
    value: A


@dataclass(frozen=True, order=True)
class Nothing(Maybe[A]):
    pass


class Either(Generic[E, A]):
    def map(self, f: Callable[[A], B]) -> Either[E, B]:
        if isinstance(self, Right):
            return Right(f(self.value))
        else:
            return cast(Either[E, B], self)

    def bind(self, f: Callable[[A], Either[E, B]]) -> Either[E, B]:
        if isinstance(self, Right):
            return f(self.value)
        else:
            return cast(Either[E, B], self)

    def ap(self, f: Either[E, Callable[[A], B]]) -> Either[E, B]:
        if isinstance(self, Right) and isinstance(f, Right):
            return f.value(self.value)
        elif isinstance(f, Left):
            return f
        else:
            return cast(Either[E, B], self)


@dataclass(frozen=True)
class Right(Either[E, A]):
    value: A


@dataclass(frozen=True)
class Left(Either[E, A]):
    value: E

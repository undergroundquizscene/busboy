import json
from concurrent.futures import Executor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from os import makedirs, scandir
from sys import argv
from threading import Event, Timer
from time import localtime, strftime
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

import psycopg2 as pp2
import requests
from psycopg2.extras import Json

import busboy.database as db
import busboy.recording as rec
from busboy.apis import routes_at_stop, stop_passage
from busboy.constants import (
    church_cross_east,
    cycle_stops,
    route_cover,
    stop_passage_tdi,
)
from busboy.model import StopId


def main() -> None:
    if len(argv) == 1:
        rec.loop()
    else:
        rec.loop(argv[1:])


if __name__ == "__main__":
    main()

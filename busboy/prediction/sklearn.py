from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Dict, List, Set, Tuple

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

import busboy.apis as api
import busboy.database as db
from busboy import prediction
from busboy.prediction import RouteSection
from busboy.util import dict_collect, dict_collect_list, dict_collect_set


@dataclass
class TravelTimeTransformer(BaseEstimator, TransformerMixin):
    """Transforms an array of stop times into travel times for two stops."""

    stop_names: List[str]
    target_stop: str
    last_known_stop: str

    def fit(self, X, y=None) -> TravelTimeTransformer:
        return self


def journeys(
    snapshots: List[db.BusSnapshot],
    timetable_variants: Set[api.TimetableVariant],
    route_sections: Dict[api.TimetableVariant, List[RouteSection]],
) -> Dict[api.TimetableVariant, pd.DataFrame]:
    pvars = sorted(
        prediction.possible_variants(
            prediction.drop_duplicate_positions(snapshots), route_sections
        ),
        key=lambda t: t[0].poll_time,
    )
    order_pvars = prediction.check_variant_order(pvars)
    stop_shaped_entries = [
        (
            e,
            {
                v: {t[1] for t in ts}
                for v, ts in dict_collect_set(vs, lambda tpl: tpl[0]).items()
            },
        )
        for (e, vs) in order_pvars
    ]
    stop_times = prediction.stop_times(stop_shaped_entries, route_sections)
    return dict(
        prediction.journeys_dataframe(prediction.estimate_arrival(stop_times.items()))
    )


def join_journeys(
    journeys: List[Dict[api.TimetableVariant, pd.DataFrame]],
) -> Dict[api.TimetableVariant, pd.DataFrame]:
    items = chain.from_iterable(map(lambda dfs: dfs.items(), journeys))
    d: Dict[api.TimetableVariant, List[pd.DataFrame]] = {}
    for variant, df in items:
        d.setdefault(variant, []).append(df)
    return {v: pd.concat(dfs, ignore_index=True) for v, dfs in d.items()}

from typing import List

import numpy as np
import pandas as pd


def travel_times(
    journeys: pd.DataFrame, stops: List[str], last_known_column: str, target_column: str
) -> np.ndarray:
    """Converts a dataframe of stop arrival times into an array of travel times."""
    target = journeys[target_column]
    last = journeys[last_known_column]
    return (target - last).values


def travel_times_df(
    journeys: pd.DataFrame, last_known_column: str, target_column: str
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "start_time": journeys[last_known_column],
            "end_time": journeys[target_column],
            "travel_time": (
                journeys[target_column] - journeys[last_known_column]
            ).values,
        }
    )

from typing import List

import numpy as np
import pandas as pd


def travel_times(
    journeys: pd.DataFrame,
    stops: List[str],
    last_known_column: str,
    target_column: str,
) -> np.ndarray:
    """Converts a dataframe of stop arrival times into an array of travel times."""
    target = journeys[target_column]
    last = journeys[last_known_column]
    return (target - last).values

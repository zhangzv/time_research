from typing import Literal

import pandas as pd
from pandas import DataFrame, DatetimeIndex, Timedelta, Timestamp

from utils.log import log_missing_data
from utils.valid import check_cols


def cross_join(
    syms: list[str],
    s_ts: Timestamp,
    e_ts: Timestamp,
    interval: Timedelta,
    inclusive: Literal["both", "neither", "left", "right"] = "both",
) -> DataFrame:
    """cross join between symbols and range(s_ts, e_ts) to define the 'full universe'

    Args:
        syms (list[str]): symbols
        s_ts (Timestamp): start timestamp
        e_ts (Timestamp): end timestamp
        interval (Timedelta): interval, timeframe
        inclusive (Literal[both, neither, left, right]): defines the inclusiveness of
        the time series (s_ts, e_ts)

    Returns:
        DataFrame: ['sym', 'ts']
    """
    # create full time series
    times: DatetimeIndex = pd.date_range(
        start=s_ts,
        end=e_ts,
        freq=interval,
        inclusive=inclusive,
    )
    # cross join between symbols and time points to create full universe
    df: DataFrame = pd.merge(
        left=DataFrame(data={"sym": syms}),
        right=DataFrame(data={"ts": times}),
        how="cross",
    )
    df = df[(df["ts"] >= s_ts) & (df["ts"] <= e_ts)]
    check_cols(df=df, cols=["sym", "ts"])
    return df


def padding_id_time(
    df: DataFrame,
    freq: Timedelta,
    s_ts: Timestamp | None = None,
    e_ts: Timestamp | None = None,
    category: str = "",
    check_missing_data: bool = True,
) -> DataFrame:
    """merge df with full universe

    Args:
        df (DataFrame): ['sym', 'ts', others]
        freq (Timedelta): interval
        s_ts (Timestamp | None, optional): start timestamp. Defaults to None.
        e_ts (Timestamp | None, optional): end timestamp. Defaults to None.
        category (str, optional): identifier to be used in log_missing_data function. Defaults to "".
        check_missing_data (bool, optional): check missing data or not. Defaults to True.

    Returns:
        DataFrame: ['sym', 'ts', others]
    """

    check_cols(df=df, cols=["sym", "ts"], checkRedundancy=False)
    ids: list[str] = list(df["sym"].unique())
    # if s_ts and e_ts is None, take the min and max of the available ts in the dataframe
    if s_ts is None:
        s_ts = min(df["ts"])
    if e_ts is None:
        e_ts = max(df["ts"])
    assert isinstance(s_ts, Timestamp)
    assert isinstance(e_ts, Timestamp)

    # cross join between symbols and time points to get full universe
    full_univ: DataFrame = cross_join(syms=ids, s_ts=s_ts, e_ts=e_ts, interval=freq)

    # left join the df on full_univ to check missing data
    df = pd.merge(left=full_univ, right=df, how="left", on=["sym", "ts"])
    if check_missing_data:
        missing_data: DataFrame = df[df.isnull().any(axis=1)]
        if len(missing_data):
            log_missing_data(df=missing_data, category=category)

    return df

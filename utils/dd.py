import numpy as np
from pandas import DataFrame


def top_drawdown(x: np.ndarray, time: np.ndarray, topN: int = 5) -> DataFrame:
    """calculate topN drawdowns

    Args:
        x (np.ndarray): target price data, cannot be return
        time (np.ndarray): corresponding time of each data point in x
        topN (int, optional): topN. Defaults to 5.

    Returns:
        DataFrame: [peak_time, trough_time, recovery_time, max_dd]
    """

    assert not np.isnan(x).any()
    assert len(x) == len(time)
    df = DataFrame(data={"value": x, "time": time})

    """
    get historical peak time for each data point
    """
    df["cum_max"] = df["value"].cummax()
    df["new_peak"] = df["cum_max"].shift() != df["cum_max"]
    df["peak_time"] = np.where(df["new_peak"], df["time"], np.nan)
    df["peak_time"] = df["peak_time"].fillna(method="ffill")

    """
    calculate drawdown for each data point
    """
    df["drawdown"] = df["value"] / df["cum_max"] - 1

    """
    for each peak time group:
        calculate max drawdown
        calculate trough time
        calculate recovery time
    """
    df: DataFrame = df.groupby(by=["peak_time"], group_keys=False).apply(
        func=lambda x: x.assign(
            max_dd=min(x["drawdown"]),
            recovery_time=x.iloc[-1]["time"],
            trough_time=x.loc[x["drawdown"].idxmin(), "time"],
        )
    )

    """
    sort and take topN drawdowns
    """
    top_dd: DataFrame = (
        df[["peak_time", "trough_time", "recovery_time", "max_dd"]]
        .drop_duplicates()
        .sort_values(by=["max_dd"], ascending=True)
        .head(n=topN)
        .reset_index(drop=True)
    )

    """
    adjust recovery_time for latest data point
    """
    top_dd["recovery_time"] = np.where(
        top_dd["recovery_time"] == max(df["time"]),
        np.nan,
        top_dd["recovery_time"],
    )

    return top_dd

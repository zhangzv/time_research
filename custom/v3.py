import numpy as np
from pandas import DataFrame, merge

from utils.loader import load_price
from utils.log import logger
from utils.valid import check_cols


def func(prc_df: DataFrame, cfg: dict):
    # load params from config
    lookback: int = cfg["lookback"]
    halflife: int = cfg["halflife"]
    z_lb: int = cfg["z_lb"]

    """
    1. load bybit price to help decide the mid price
    """
    bybit_prc: DataFrame = load_price(
        stime=min(prc_df["ts"]),
        etime=max(prc_df["ts"]),
        exchange="bybit",
        symbols=[cfg["ccxt_sym"]],
        timeframe=cfg["timeframe"],
    )
    check_cols(
        df=bybit_prc,
        cols=["sym", "ts", "open", "high", "low", "close", "volume"],
    )
    bybit_prc["ret"] = bybit_prc["close"] / bybit_prc["open"] - 1

    # merge bybit information to prc_df
    prc_df = merge(
        left=prc_df,
        right=bybit_prc[["sym", "ts", "open", "ret", "volume"]].rename(
            columns={
                "open": "bybit_open_prc",
                "ret": "bybit_ret",
                "volume": "bybit_vol",
            }
        ),
        how="left",
        on=["sym", "ts"],
    )
    """
    2. calculate signal
    """
    # define mid price
    prc_df["mid_prc"] = (
        prc_df["binance_open_prc"] + prc_df["okx_open_prc"] + prc_df["bybit_open_prc"]
    ) / 3
    # calculate the distance between okx open price and the mid price
    prc_df["okx_dis"] = (prc_df["okx_open_prc"] - prc_df["mid_prc"]) / prc_df["mid_prc"]
    # calculate the distance between binance open price and the mid price
    prc_df["binance_dis"] = (prc_df["binance_open_prc"] - prc_df["mid_prc"]) / prc_df[
        "mid_prc"
    ]

    # define the spread between binance and okx
    prc_df["score"] = prc_df["binance_dis"].abs() + prc_df["okx_dis"].abs()
    # calculate exponentially moving average of the score
    prc_df["rolling_mean"] = prc_df["score"].transform(
        lambda y: y.rolling(window=lookback, closed="left").apply(
            func=lambda x: x.ewm(halflife=halflife).mean().iloc[-1]
        )
    )
    # calculate rolling standard deviation of the score
    prc_df["rolling_std"] = (
        prc_df["score"].rolling(window=lookback, closed="left").std()
    )
    # calculate z score to dynamically define if the score is an extreme value that gives us signal
    prc_df["signal"] = (prc_df["score"] - prc_df["rolling_mean"]) / prc_df[
        "rolling_std"
    ]

    # Make sure binance open price and okx open price are distributed at 2 sides of the mid
    # Make sure z score is higher than the lower bound to define 'abnormal'
    prc_df["trade"] = np.where(
        (prc_df["binance_dis"] * prc_df["okx_dis"] < 0) & (prc_df["signal"] > z_lb),
        True,
        False,
    )

    """
    3. decide side for those trade==True
    """
    prc_df["binance_side"] = np.select(
        condlist=[
            prc_df["trade"] & (prc_df["binance_dis"] > 0),
            prc_df["trade"] & (prc_df["binance_dis"] < 0),
        ],
        choicelist=[-1, 1],
        default=0,
    )
    prc_df["okx_side"] = -1 * prc_df["binance_side"]

    return prc_df

import math
from typing import Literal

import ccxt
import pandas as pd
from pandas import DataFrame, Timedelta, Timestamp, to_datetime

from utils.dframe import padding_id_time
from utils.var import INTERVAL_MS_MAP


def load_price(
    stime: Timestamp,
    etime: Timestamp,
    exchange: Literal["okx", "binance"],
    symbols: list[str] = ["BTC/USDT:USDT"],
    timeframe: str = "15m",
) -> DataFrame:
    """get cex price, may have NA

    Args:
        stime (Timestamp): start time
        etime (Timestamp): end time
        exchange (Literal[bybit, binance]): cex
        symbols (list[str], optional): ccxt symbols. Defaults to ["BTC/USDT:USDT"].
        timeframe (str, optional): timeframe. Defaults to "15m".

    Returns:
        DataFrame: ['sym', 'ts', 'open', 'high', 'low', 'close', 'volume']
    """

    """
    1. set timeframe, stime, etime
    """
    # validate timeframe
    assert timeframe in INTERVAL_MS_MAP.keys(), "Incorrect interval"
    interval_ts: Timedelta = Timedelta(
        value=INTERVAL_MS_MAP[timeframe],
        unit="millisecond",
    )

    # check etime > stime
    assert etime >= stime

    """
    2. set query limit and exchange object
    """
    data_count: int = math.ceil((etime - stime) / interval_ts) + 1
    LIMIT: int = 100 if data_count > 100 else data_count
    call_times: int = math.ceil(data_count / LIMIT)
    cex: ccxt.Exchange = eval(f"ccxt.{exchange}()")

    """
    3. prepare parameters for api requests
    """
    params: list[tuple[Timestamp, Timestamp]] = [
        (
            stime + k * interval_ts * LIMIT,
            stime + (k + 1) * interval_ts * LIMIT,
        )
        for k in range(call_times)
    ]

    """
    4. make api requests and check
    """
    price_list: list[DataFrame] = []
    for symbol in symbols:
        tmp: list[list] = []
        # s is pandas Timestamp object
        # Timestamp.value is in nano second
        # fetch_ohlcv 'since' parameter take integer millisecond
        for s, e in params:
            response: list[list] = cex.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=LIMIT,
                since=int(s.value / 1e6),
            )
            tmp.extend(response)

        sym_price: list[list] = [_[0:6] for _ in tmp]
        sym_price_df: DataFrame = DataFrame(
            data=sym_price,
            columns=["ts_ms", "open", "high", "low", "close", "volume"],
        )
        sym_price_df["ts"] = to_datetime(sym_price_df["ts_ms"], unit="ms", utc=True)
        sym_price_df["sym"] = symbol
        sym_price_df.drop(columns=["ts_ms"], inplace=True)
        # check missing data
        sym_price_df = padding_id_time(
            df=sym_price_df,
            freq=interval_ts,
            category="price",
            check_missing_data=True,
        )
        price_list.append(sym_price_df)

    price_df: DataFrame = pd.concat(objs=price_list, ignore_index=True)
    price_df.drop_duplicates(inplace=True)
    price_df = price_df[(price_df["ts"] >= stime) & (price_df["ts"] <= etime)]
    return price_df

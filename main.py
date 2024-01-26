import importlib
import os
from datetime import date, timezone
from typing import Any, Callable

import numpy as np
from pandas import DataFrame, Timedelta, Timestamp, merge

from utils.config import load_cfg
from utils.dd import top_drawdown
from utils.loader import load_price
from utils.log import logger
from utils.report import gen_report
from utils.valid import check_cols
from utils.var import ANNUAL_MS, CFG_DIR, INTERVAL_MS_MAP


def main(cfg: dict):
    """
    1. get sdate, edate
    """
    # when we load config yaml file to python dict,
    # yyyy-mm-dd format in yaml file will be converted automatically to datetime.date
    # so here they are datetime.date object rather than string
    sdate: date = cfg["sdate"]
    edate: date = cfg["edate"]
    # convert datetime.date to pandas Timestamp object and set timezone to utc
    s_ts: Timestamp = Timestamp(ts_input=sdate, tz=timezone.utc)
    e_ts: Timestamp = Timestamp(ts_input=edate, tz=timezone.utc)
    logger.info(msg=f"Backtesting start time: {s_ts}")
    logger.info(msg=f"Backtesting end time: {e_ts}")

    """
    2. get timeframe
    """
    # get timeframe sting from config and convert it to pandas Timedelta object
    timeframe: str = cfg["timeframe"]
    timeframe_ts: Timedelta = Timedelta(
        value=INTERVAL_MS_MAP[timeframe],
        unit="millisecond",
    )
    logger.info(msg=f"Backtesting timeframe: {timeframe_ts}")

    """
    3. get symbol
    """
    # get ccxt_sym string from config
    ccxt_sym: str = cfg["ccxt_sym"]
    logger.info(msg=f"Backtesting symbol: {ccxt_sym}")

    """
    4. load historical price
    """
    # load price for okx
    logger.info(msg="Loading price for okx")
    okx_prc: DataFrame = load_price(
        stime=s_ts,
        etime=e_ts,
        exchange="okx",
        symbols=[ccxt_sym],
        timeframe=timeframe,
    )
    check_cols(
        df=okx_prc,
        cols=["sym", "ts", "open", "high", "low", "close", "volume"],
    )

    # load price for binance
    logger.info(msg="Loading price for binance")
    binance_prc: DataFrame = load_price(
        stime=s_ts,
        etime=e_ts,
        exchange="binance",
        symbols=[ccxt_sym],
        timeframe=timeframe,
    )
    check_cols(
        df=binance_prc,
        cols=["sym", "ts", "open", "high", "low", "close", "volume"],
    )

    """
    5. merge dataframe
    """
    # Data process
    # calculate return
    okx_prc["ret"] = okx_prc["close"] / okx_prc["open"] - 1
    binance_prc["ret"] = binance_prc["close"] / binance_prc["open"] - 1
    # merge data
    prc_df: DataFrame = merge(
        left=okx_prc[["sym", "ts", "open", "ret", "volume"]].rename(
            columns={
                "open": "okx_open_prc",
                "ret": "okx_ret",
                "volume": "okx_vol",
            }
        ),
        right=binance_prc[["sym", "ts", "open", "ret", "volume"]].rename(
            columns={
                "open": "binance_open_prc",
                "ret": "binance_ret",
                "volume": "binance_vol",
            }
        ),
        how="inner",
        on=["sym", "ts"],
    )
    check_cols(
        df=prc_df,
        cols=[
            "sym",
            "ts",
            "okx_open_prc",
            "binance_open_prc",
            "okx_ret",
            "binance_ret",
            "okx_vol",
            "binance_vol",
        ],
    )

    """
    6. call custom function to calculate signal and decide trade direction
    """
    logger.info(msg="Calculating signal")
    # call callback function to define binance side and okx side
    fn: str = cfg["file"]
    func: str = cfg["func"]
    module_name: str = "custom." + fn.replace(".py", "")
    module = importlib.import_module(name=module_name)
    callback: Callable = getattr(module, func)
    prc_df: DataFrame = callback(prc_df=prc_df.copy(), cfg=cfg)
    check_cols(
        df=prc_df,
        cols=[
            "sym",
            "ts",
            "okx_open_prc",
            "binance_open_prc",
            "okx_ret",
            "binance_ret",
            "okx_vol",
            "binance_vol",
            "binance_side",
            "okx_side",
        ],
        checkRedundancy=False,
    )

    """
    7. calculate return, fees
    """
    # from the custom function we have defined binance_side and okx_side
    # calculate strategy return at each timepoint
    prc_df["ret"] = (
        prc_df["binance_side"] * prc_df["binance_ret"]
        + prc_df["okx_side"] * prc_df["okx_ret"]
    )
    # use previous binance side and current binance side to generate the 'action' column
    prc_df["prev_binance_side"] = prc_df["binance_side"].shift().fillna(0)
    prc_df["action"] = np.select(
        condlist=[
            # keep same direction
            prc_df["binance_side"] == prc_df["prev_binance_side"],
            # close position
            (prc_df["binance_side"] != prc_df["prev_binance_side"])
            & (prc_df["binance_side"] == 0),
            # open position
            (prc_df["binance_side"] != prc_df["prev_binance_side"])
            & (prc_df["prev_binance_side"] == 0),
            # reverse position
            (prc_df["binance_side"] != prc_df["prev_binance_side"])
            & ((prc_df["binance_side"] * prc_df["prev_binance_side"]) == -1),
        ],
        choicelist=["keep", "close", "open", "reverse"],
        default=np.nan,
    )
    # calculate fees of different tiers
    prc_df["1bps"] = np.select(
        condlist=[
            prc_df["action"].isin(["close", "open"]),
            prc_df["action"] == "reverse",
        ],
        choicelist=[0.0001, 0.0002],
        default=0,
    )
    prc_df["2bps"] = np.select(
        condlist=[
            prc_df["action"].isin(["close", "open"]),
            prc_df["action"] == "reverse",
        ],
        choicelist=[0.0002, 0.0004],
        default=0,
    )
    prc_df["3bps"] = np.select(
        condlist=[
            prc_df["action"].isin(["close", "open"]),
            prc_df["action"] == "reverse",
        ],
        choicelist=[0.0003, 0.0006],
        default=0,
    )
    # deduct fees from the return to get fee adjusted return
    prc_df["adj_ret"] = np.select(
        condlist=[
            prc_df["action"].isin(["close", "open"]),
            prc_df["action"] == "reverse",
        ],
        choicelist=[
            prc_df["ret"] - cfg["fee"],
            prc_df["ret"] - 2 * cfg["fee"],
        ],
        default=prc_df["ret"],
    )

    """
    8. added debug information to be used to improve the performance
    """
    # debug columns
    prc_df["ret_diff"] = prc_df["binance_ret"] - prc_df["okx_ret"]
    prc_df["ret_diff"] = np.where(
        prc_df["ret_diff"] > cfg["fee"], prc_df["ret_diff"], 0
    )
    prc_df["ideal_binance_side"] = np.select(
        [prc_df["ret_diff"] > 0, prc_df["ret_diff"] < 0],
        [1, -1],
        0,
    )
    prc_df.to_csv("debug.csv")

    """
    9. calculate max drawdown and other risk metrics
    """
    # caculate max drawdown
    prc_df["nav"] = (prc_df["adj_ret"] + 1).cumprod()
    top_dd: DataFrame = top_drawdown(
        x=np.array(prc_df["nav"]),
        time=np.array(prc_df["ts"]),
        topN=3,
    )
    check_cols(
        df=top_dd,
        cols=["peak_time", "trough_time", "recovery_time", "max_dd"],
    )
    top_dd["max_dd"] *= 100
    top_dd["max_dd"] = top_dd["max_dd"].round(2).astype(str) + "%"

    # calculate performance metrics
    scalar: float = Timedelta(value=ANNUAL_MS, unit="millisecond") / timeframe_ts
    annual_ret: float = float(np.mean(a=prc_df["adj_ret"])) * scalar
    annual_std: float = float(np.std(a=prc_df["adj_ret"], ddof=1) * np.sqrt(scalar))
    annual_sr: float = annual_ret / annual_std
    performance_data: dict = {
        "Annual Return": str(round(annual_ret * 100, 2)) + "%",
        "Annual Std": str(round(annual_std * 100, 2)) + "%",
        "Annual Sharpe": round(annual_sr, 2),
        "Max Drawdown": top_dd["max_dd"][0],
    }

    """
    10. generate report
    """
    # generate report
    report_data: dict[str, DataFrame] = {
        "config": DataFrame(data=cfg.items(), columns=["param", "value"]),
        "performance": DataFrame(
            data=performance_data.items(), columns=["metrics", "value"]
        ),
        "drawdown": top_dd[["peak_time", "trough_time", "recovery_time", "max_dd"]],
        "ret": prc_df[["ts", "ret", "adj_ret"]],
        "signal": prc_df[["ts", "signal"]],
        "fee": prc_df[["ts", "1bps", "2bps", "3bps"]],
    }
    gen_report(report_data=report_data)
    return


if __name__ == "__main__":
    """
    1. load config
    """
    # update the cfg_fn only
    cfg_fn = "strat.yml"
    cfg_fp: str = os.path.join(CFG_DIR, cfg_fn)
    cfg: dict[str, Any] = load_cfg(cfg_fp=cfg_fp)

    """
    2. backtest
    """
    main(cfg=cfg)

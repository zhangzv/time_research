import os
from datetime import date, timezone
from typing import Any

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

    # get timeframe sting from config and convert it to pandas Timedelta object
    timeframe: str = cfg["timeframe"]
    timeframe_ts: Timedelta = Timedelta(
        value=INTERVAL_MS_MAP[timeframe],
        unit="millisecond",
    )
    logger.info(msg=f"Backtesting timeframe: {timeframe_ts}")

    # get ccxt_sym string from config
    ccxt_sym: str = cfg["ccxt_sym"]
    logger.info(msg=f"Backtesting symbol: {ccxt_sym}")

    # load price for okx
    logger.info(msg="Loading price for okx")
    okx_prc: DataFrame = load_price(
        stime=s_ts,
        etime=e_ts,
        exchange="okx",
        symbols=[ccxt_sym],
        timeframe=timeframe,
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

    # Data process
    logger.info(msg="Calculating signal")
    # calculate return
    okx_prc["ret"] = okx_prc["close"] / okx_prc["open"] - 1
    binance_prc["ret"] = binance_prc["close"] / binance_prc["open"] - 1
    # merge data
    prc_df: DataFrame = merge(
        left=okx_prc[["sym", "ts", "open", "ret"]].rename(
            columns={"open": "okx_open_prc", "ret": "okx_ret"}
        ),
        right=binance_prc[["sym", "ts", "open", "ret"]].rename(
            columns={"open": "binance_open_prc", "ret": "binance_ret"}
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
        ],
    )
    # calculate signal
    prc_df["signal"] = abs((prc_df["binance_open_prc"] / prc_df["okx_open_prc"]) - 1)
    prc_df["trade"] = prc_df["signal"] > cfg["threshold"]

    # describe signal
    logger.info(f"Threshold: {cfg['threshold']}")
    logger.info(f"Min signal: {min(prc_df['signal'])}")
    logger.info(f"0.25 quantile: {np.percentile(a=prc_df['signal'],q=25)}")
    logger.info(f"0.75 quantile: {np.percentile(a=prc_df['signal'],q=75)}")
    logger.info(f"Max signal: {max(prc_df['signal'])}")
    total_count: int = len(prc_df)
    signal_triggered_count: int = len(prc_df[prc_df["trade"]])
    logger.info(f"Opportunities count: {total_count}")
    logger.info(f"Signal triggered count: {signal_triggered_count}")
    # count trades
    if signal_triggered_count / total_count < 0.2:
        logger.warning(
            f"Signal was triggered less than 20% of total count: {100*signal_triggered_count/total_count}%, "
            "please check the threshold."
        )
        if signal_triggered_count / total_count == 0:
            logger.error(f"No signal was triggered, please check the threshold.")
            return

    # decide side
    prc_df["binance_side"] = np.select(
        condlist=[
            prc_df["trade"] & (prc_df["binance_open_prc"] > prc_df["okx_open_prc"]),
            prc_df["trade"] & (prc_df["binance_open_prc"] < prc_df["okx_open_prc"]),
        ],
        choicelist=[-1, 1],
        default=0,
    )
    prc_df["okx_side"] = -1 * prc_df["binance_side"]

    # calculate strategy return at each timepoint
    prc_df["ret"] = (
        prc_df["binance_side"]
        * prc_df["binance_ret"]
        * prc_df["okx_side"]
        * prc_df["okx_ret"]
    )

    # caculate max drawdown
    prc_df["nav"] = (prc_df["ret"] + 1).cumprod()
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
    annual_ret: float = float(np.mean(a=prc_df["ret"])) * scalar
    annual_std: float = float(np.std(a=prc_df["ret"], ddof=1) * np.sqrt(scalar))
    annual_sr: float = annual_ret / annual_std
    win_ratio: float = len(prc_df[prc_df["ret"] > 0]) / len(prc_df[prc_df["ret"] != 0])
    performance_data: dict = {
        "Annual Return": str(round(annual_ret * 100, 2)) + "%",
        "Annual Std": str(round(annual_std * 100, 2)) + "%",
        "Annual Sharpe": round(annual_sr, 2),
        "Win Ratio": str(round(win_ratio, 2)) + "%",
        "Max Drawdown": top_dd["max_dd"][0],
    }

    # generate report
    report_data: dict[str, DataFrame] = {
        "config": DataFrame(data=cfg.items(), columns=["param", "value"]),
        "performance": DataFrame(
            data=performance_data.items(), columns=["metrics", "value"]
        ),
        "drawdown": top_dd[["peak_time", "trough_time", "recovery_time", "max_dd"]],
        "ret": prc_df[["ts", "ret"]],
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

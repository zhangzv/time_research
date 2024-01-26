import numpy as np
from pandas import DataFrame

from utils.log import logger


def func(prc_df: DataFrame, cfg: dict):
    """
    1. calculate signal
    """
    # calculate signal
    prc_df["signal"] = abs((prc_df["binance_open_prc"] / prc_df["okx_open_prc"]) - 1)
    # define threshold
    # calculate 90th percentile on a 30 periods rolling window
    # use max(cfg['threshold'], rolling 90th percentile) as threshold
    prc_df["threshold"] = (
        prc_df["signal"]
        .rolling(window=30, closed="left")
        .apply(func=lambda x: np.percentile(x, q=90))
        .fillna(value=cfg["threshold"])
    )
    prc_df["threshold"] = np.where(
        prc_df["threshold"] < cfg["threshold"],
        cfg["threshold"],
        prc_df["threshold"],
    )
    # trade or not
    prc_df["trade"] = prc_df["signal"] > prc_df["threshold"]

    # prc_df["prev_binance_vol"] = prc_df["binance_vol"].shift()
    # prc_df["prev_okx_vol"] = prc_df["okx_vol"].shift()
    # prc_df["vol_ratio"] = prc_df["prev_binance_vol"] / prc_df["prev_okx_vol"]
    # prc_df["binance_vol_signal"] = prc_df["prev_binance_vol"].pct_change()
    # prc_df["okx_vol_signal"] = prc_df["prev_okx_vol"].pct_change()

    """
    2. describe signal
    """
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

    """
    3. decide side for those trade==True
    """
    prc_df["binance_side"] = np.select(
        condlist=[
            prc_df["trade"] & (prc_df["binance_open_prc"] > prc_df["okx_open_prc"]),
            prc_df["trade"] & (prc_df["binance_open_prc"] < prc_df["okx_open_prc"]),
        ],
        choicelist=[-1, 1],
        default=0,
    )
    prc_df["okx_side"] = -1 * prc_df["binance_side"]
    return prc_df

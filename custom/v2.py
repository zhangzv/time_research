from datetime import date

import numpy as np
from pandas import DataFrame


### ignore
def func(prc_df: DataFrame, cfg: dict):
    prc_df["signal"] = abs((prc_df["binance_open_prc"] / prc_df["okx_open_prc"]) - 1)
    prc_df["same_ret_direction"] = (prc_df["binance_ret"] * prc_df["okx_ret"]) > 0
    prc_df["prev_same_ret_direction"] = prc_df["same_ret_direction"].shift()

    prc_df["ideal_binance_side"] = np.where(
        prc_df["binance_ret"] > prc_df["okx_ret"], 1, -1
    )
    # prc_df["real_binance_side"] = np.where(
    #     prc_df["binance_open_prc"] > prc_df["okx_open_prc"], -1, 1
    # )
    # prc_df["side_matches"] = prc_df["ideal_binance_side"] == prc_df["real_binance_side"]
    # prc_df["ideal_ret"] = prc_df["ideal_binance_side"] * (
    #     prc_df["binance_ret"] - prc_df["okx_ret"]
    # )
    # prc_df["real_ret"] = prc_df["real_binance_side"] * (
    #     prc_df["binance_ret"] - prc_df["okx_ret"]
    # )
    prc_df["binance_side"] = np.select(
        condlist=[
            (prc_df["prev_same_ret_direction"] == False)
            & (prc_df["binance_open_prc"] > prc_df["okx_open_prc"]),
            (prc_df["prev_same_ret_direction"] == False)
            & (prc_df["binance_open_prc"] < prc_df["okx_open_prc"]),
        ],
        choicelist=[1, -1],
        default=0,
    )
    prc_df["okx_side"] = prc_df["binance_side"] * -1
    return prc_df

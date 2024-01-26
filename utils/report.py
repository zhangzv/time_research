import os
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from pandas import DataFrame

from utils.plot import plot_dist, plot_line, plot_table
from utils.valid import check_cols
from utils.var import REPORT_DIR


def gen_report(report_data: dict[str, DataFrame]):
    # load data
    cfg_df: DataFrame = report_data["config"]
    performance_df: DataFrame = report_data["performance"]
    dd_df: DataFrame = report_data["drawdown"]
    ret_df: DataFrame = report_data["ret"]
    signal_df: DataFrame = report_data["signal"]
    fee_df: DataFrame = report_data["fee"]
    check_cols(df=cfg_df, cols=["param", "value"])
    check_cols(df=performance_df, cols=["metrics", "value"])
    check_cols(df=dd_df, cols=["peak_time", "trough_time", "recovery_time", "max_dd"])
    check_cols(df=ret_df, cols=["ts", "ret", "adj_ret"])
    check_cols(df=signal_df, cols=["ts", "signal"])
    check_cols(df=fee_df, cols=["ts", "1bps", "2bps", "3bps"])

    # make sure the dir exists
    if not os.path.exists(path=REPORT_DIR):
        os.makedirs(name=REPORT_DIR)

    # define pdf object
    pdf_fn: str = ".".join(
        [
            f"R{datetime.now().strftime('%Y%m%d.%H%M%S')}",  # runtime
            f"S{min(ret_df['ts']).strftime('%Y%m%d')}",  # start time
            f"E{max(ret_df['ts']).strftime('%Y%m%d')}",  # end time
            "pdf",
        ]
    )
    pdf_fp: str = os.path.join(REPORT_DIR, pdf_fn)
    pdf = PdfPages(filename=pdf_fp)

    # config
    fig: Figure = plot_table(
        data=cfg_df,
        title=f"Configuration",
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # performance
    fig: Figure = plot_table(
        data=performance_df,
        title=f"Performance",
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # performance
    fig: Figure = plot_table(
        data=dd_df,
        title=f"Drawdown",
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # cumulative return
    fig: Figure = plot_line(
        _df=ret_df,
        _x="ts",
        _y=["ret"],
        _x_label="time",
        _y_label="return [%]",
        _title=f"Cumulative Return Without Fee",
        _cumulative=True,
        _to_percentage=True,
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # cumulative return
    fig: Figure = plot_line(
        _df=ret_df,
        _x="ts",
        _y=["adj_ret"],
        _x_label="time",
        _y_label="return [%]",
        _title=f"Cumulative Return With Fee",
        _cumulative=True,
        _to_percentage=True,
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # cumulative return
    fig: Figure = plot_line(
        _df=fee_df,
        _x="ts",
        _y=["1bps", "2bps", "3bps"],
        _x_label="time",
        _y_label="fee [%]",
        _title=f"Fee of Different Tier",
        _cumulative=True,
        _to_percentage=True,
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # periodical return
    fig: Figure = plot_line(
        _df=ret_df,
        _x="ts",
        _y=["adj_ret"],
        _x_label="time",
        _y_label="return [%]",
        _title=f"Periodical Return",
        _cumulative=False,
        _to_percentage=True,
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # return distribution
    fig: Figure = plot_dist(
        data=np.array(object=ret_df["adj_ret"] * 100),
        bins=100,
        _x_label="return [%]",
        _y_label="count",
        _title=f"Return Distribution",
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    # signal distribution
    fig: Figure = plot_dist(
        data=np.array(object=signal_df["signal"]),
        bins=100,
        _x_label="signal",
        _y_label="count",
        _title=f"Signal Distribution",
    )
    pdf.savefig(figure=fig)
    plt.close(fig=fig)

    pdf.close()
    return

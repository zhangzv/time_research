import math
from typing import Any, Literal

from cycler import cycler
from matplotlib import pyplot as plt
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from pandas import DataFrame


def update_plot_settings() -> None:
    plt.style.use(style="ggplot")  # type: ignore
    # color blind friendly color cycle
    CB_color_cycle: list[str] = [
        "#377eb8",
        "#ff7f00",
        "#4daf4a",
        "#f781bf",
        "#a65628",
        "#984ea3",
        "#999999",
        "#e41a1c",
        "#dede00",
    ]
    # rcParams
    params: dict[str, Any] = {
        "font.size": 13,
        "font.weight": 300,
        "font.family": "Times New Roman",
        "figure.subplot.wspace": 0.2,
        "figure.subplot.hspace": 0.4,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.titlesize": 17,
        "axes.titleweight": 500,
        "lines.linewidth": 1,
        "axes.labelsize": 15,
        "axes.labelweight": 400,
        "axes.prop_cycle": cycler(color=CB_color_cycle),
        "legend.fontsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "xtick.direction": "in",
        "ytick.direction": "in",
    }
    rcParams.update(params)


def plot_line(
    _df: DataFrame,
    _x: str,
    _y: list[str],
    _x_label: str,
    _y_label: str,
    _title: str,
    _fill_between: list[str | float] = [],
    _cumulative: bool = False,
    _normalise: bool = False,
    _addDot: bool = False,
    _showLast: bool = True,
    _lineShape: Literal["-", "--", "-."] = "-",
    _dotShape: Literal[".", "o", "*"] = ".",
    _addLine: bool = False,
    _showAllXTicks: bool = False,
    _to_percentage: bool = False,
) -> Figure:
    """line plot

    Args:
        _df (DataFrame): [_x] + _y
        _x (str): x column
        _y (list[str]): y columns
        _x_label (str): x label
        _y_label (str): y label
        _title (str): title
        _fill_between (list[str  |  float], optional): draw color between two lines. Defaults to [].
        _cumulative (bool, optional): update y columns to cumulative value. Defaults to False.
        _normalise (bool, optional): normalise y columns value. Defaults to False.
        _addDot (bool, optional): add dot for data points. Defaults to False.
        _showLast (bool, optional): show value of last point in legend. Defaults to True.
        _lineShape (Literal[-, --, -., optional): line shape. Defaults to "-".
        _dotShape (Literal[., o, *, optional): dot shape. Defaults to ".".
        _addLine (bool, optional): add x=0, y=0 lines. Defaults to False.
        _showAllXTicks (bool, optional): show all x ticks. Defaults to False.

    Returns:
        Figure: plot
    """
    update_plot_settings()
    cols: list[str] = _y + [_x]
    for k in cols:
        assert k in _df.columns
    _df = _df.sort_values(by=[_x])
    if _cumulative:
        for col in _y:
            _df[col] = _df[col].cumsum()
    if _to_percentage:
        for col in _y:
            _df[col] *= 100

    fig, ax = plt.subplots(figsize=(16, 9))
    marker = _lineShape
    if _addDot:
        marker += _dotShape
    if len(_fill_between):
        assert len(_fill_between) == 2
        _y1 = (
            _df[_fill_between[0]]
            if isinstance(_fill_between[0], str)
            else _fill_between[0]
        )
        _y2 = (
            _df[_fill_between[1]]
            if isinstance(_fill_between[1], str)
            else _fill_between[1]
        )
        ax.fill_between(
            x=_df[_x],
            y1=_y1,  # type:ignore
            y2=_y2,  # type:ignore
            facecolor="red",
        )

    has_line = False
    for k in _y:
        if k in _fill_between:
            continue
        has_line = True
        if _normalise:
            magnitude = int(math.log10(_df[k].abs().min()))
            label: str = k + "_1e" + str(object=magnitude)
            _df[k] /= 10**magnitude
        else:
            label = k
        if _showLast and len(_df):
            label += " : " + str(object=round(number=_df[k].iloc[-1], ndigits=2))
        ax.plot(
            _df[_x],
            _df[k],
            marker,
            label=label,
        )

    ax.set_xlabel(xlabel=_x_label)
    ax.set_ylabel(ylabel=_y_label)
    ax.set_title(label=_title)
    ax.grid(linestyle="--", alpha=1)

    if has_line:
        ax.legend()
        # get the legend object
        leg: Legend = ax.legend()
        # change the line width for the legend
        for line in leg.get_lines():
            line.set_linewidth(w=3)
    if _addLine:
        ax.axvline(x=0, c="black", ls="--")
        ax.axhline(y=0, c="black", ls="--")
    if _showAllXTicks:
        ax.set_xticks(_df[_x])
    return fig


def plot_table(
    data: DataFrame,
    title: str = "",
    header_color="#40466e",
    row_colors=["#f1f1f2", "w"],
    edge_color="w",
    row_height: float = 0.07,
    **kwargs
) -> Figure:
    update_plot_settings()
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.axis("off")
    tb_fig = ax.table(
        cellText=data.values,
        colLabels=list(data.columns),
        loc="center",
        **kwargs,
    )
    ax.set_title(title)

    for (row, col), cell in tb_fig.get_celld().items():
        cell.set_edgecolor(edge_color)
        if row == 0:
            cell.set_height(row_height * 1.5)
            cell.set_text_props(weight="bold", color="w")
            cell.set_facecolor(header_color)
        else:
            cell.set_height(row_height)
            cell.set_facecolor(row_colors[row % len(row_colors)])
    return fig

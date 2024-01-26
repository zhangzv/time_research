import logging
import os
from datetime import datetime
from logging import DEBUG, INFO, WARNING, FileHandler, Formatter, Logger, StreamHandler
from typing import Literal

import numpy as np
from pandas import DataFrame

from utils.valid import check_cols
from utils.var import LOG_DIR, MISSING_DATA_DIR

LEVEL_MAP: dict[str, int] = {"INFO": INFO, "DEBUG": DEBUG, "WARNING": WARNING}


def create_logger(
    fp: str,
    name: str = "logger",
    logger_level: Literal["INFO", "DEBUG", "WARNING"] = "INFO",
) -> Logger:
    """create a logger

    Args:
        fp (str): log file filepath
        name (str, optional): name of the logger. Defaults to "logger".
        logger_level (Literal[INFO, DEBUG, WARNING], optional): logger level. Defaults to "INFO".

    Returns:
        Logger: logger
    """
    # create a logger
    formatter: Formatter = Formatter(
        fmt=(
            "%(asctime)s [%(name)12s] [%(levelname)7s] [%(filename)s:%(lineno)4d]"
            " %(message)s"
        )
    )
    logger: Logger = logging.getLogger(name=name)
    # set logger level
    logger.setLevel(level=LEVEL_MAP[logger_level])

    # file handler
    file_handler: FileHandler = FileHandler(filename=fp)
    file_handler.setFormatter(fmt=formatter)
    logger.addHandler(hdlr=file_handler)

    # console handler
    console_handler: StreamHandler = StreamHandler()
    console_handler.setFormatter(fmt=formatter)
    logger.addHandler(hdlr=console_handler)

    return logger


# define loggers
LOGGER_FP: str = os.path.join(LOG_DIR, "time_research.log")
logger: Logger = create_logger(fp=LOGGER_FP, name="TimeResearch")


def log_missing_data(df: DataFrame, category: str = "") -> None:
    """log missing data in dataframe, warning and write to csv

    Args:
        df (DataFrame): target dataframe to be checked
        category (str, optional): identifier that will be used in warning message and csv file name. Defaults to "".
    """

    if len(df):
        df = df.copy()
    else:
        return
    check_cols(df=df, cols=["sym", "ts"], checkRedundancy=False)
    nounce: int = np.random.randint(low=1000)
    fn: str = (
        f"missing_{category}_{nounce}_{datetime.now().strftime('%Y%m%d.%H%M%S')}.csv"
    )
    fp: str = os.path.join(MISSING_DATA_DIR, fn)
    if not os.path.exists(path=MISSING_DATA_DIR):
        os.makedirs(name=MISSING_DATA_DIR)
    df.to_csv(path_or_buf=fp, index=False)
    logger.warning(
        msg=(
            f"Missing {category} data detected for symbols: {df['sym'].unique()},"
            f" please check file: {fn}"
        )
    )

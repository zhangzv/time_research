from pandas import DataFrame


def check_cols(
    df: DataFrame,
    cols: list[str],
    checkRedundancy: bool = True,
) -> None:
    """check missing columns

    Args:
        df (DataFrame): dataframe to be checked
        cols (list[str]): target columns
        checkRedundancy (bool, optional): check extra columns or not. Defaults to True.
    """
    df_cols: set[str] = set(df.columns)
    target_cols: set[str] = set(cols)
    missing_cols: set[str] = target_cols - df_cols
    assert not len(missing_cols), f"{missing_cols} not found in dataframe columns."
    if checkRedundancy:
        redundant_cols: set[str] = df_cols - target_cols
        assert not len(
            redundant_cols
        ), f"redundant columns found in dataframe: {redundant_cols}"

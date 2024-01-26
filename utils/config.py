from yaml import safe_load as yload


def load_cfg(cfg_fp: str) -> dict:
    """load_cfg

    Args:
        cfg_fp (str): config file path

    Returns:
        dict: config dict
    """

    with open(file=cfg_fp, mode="r") as fp:
        cfg: dict | None = yload(stream=fp)
    assert cfg is not None, f"{cfg_fp} not found."
    assert isinstance(cfg, dict), "yload doesn't return dict."
    return cfg

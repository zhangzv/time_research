import os

INTERVAL_MS_MAP: dict[str, int] = {
    "1m": 60000,
    "3m": 60000 * 3,
    "5m": 60000 * 5,
    "15m": 60000 * 15,
    "30m": 60000 * 30,
    "1h": 60000 * 60,
    "2h": 60000 * 60 * 2,
    "4h": 60000 * 60 * 4,
    "6h": 60000 * 60 * 6,
    "8h": 60000 * 60 * 8,
    "12h": 60000 * 60 * 12,
    "1d": 60000 * 60 * 24,
}
ANNUAL_MS: int = INTERVAL_MS_MAP["1d"] * 365

# code repo
REPO_DIR: str = os.path.join(os.path.dirname(p=__file__), "..")
CFG_DIR: str = os.path.join(REPO_DIR, "config")
DATA_DIR: str = os.path.join(REPO_DIR, "output")
REPORT_DIR: str = os.path.join(DATA_DIR, "report")
LOG_DIR: str = os.path.join(DATA_DIR, "logs")
MISSING_DATA_DIR: str = os.path.join(DATA_DIR, "missing")
DEBUG_DIR: str = os.path.join(DATA_DIR, "debug")

for fdir in (DATA_DIR, REPORT_DIR, LOG_DIR, MISSING_DATA_DIR, DEBUG_DIR):
    if not os.path.exists(path=fdir):
        os.makedirs(name=fdir)

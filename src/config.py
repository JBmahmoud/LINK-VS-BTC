"""Shared project configuration for the LINK VS BTC analysis project."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
TABLES_DIR = OUTPUTS_DIR / "tables"
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

PROCESSED_EXCEL = PROCESSED_DIR / "Link_Bitcoin.xlsx"
PROCESSED_CSV = PROCESSED_DIR / "link_bitcoin_processed.csv"

BTC_TICKER = "BTC-USD"
LINK_TICKER = "LINK-USD"
START_DATE = "2018-01-01"
END_DATE = "2025-10-30"


def ensure_project_directories() -> None:
    """Create expected project folders if they do not already exist."""
    for directory in (
        DATA_DIR,
        RAW_DIR,
        PROCESSED_DIR,
        OUTPUTS_DIR,
        CHARTS_DIR,
        TABLES_DIR,
        SCREENSHOTS_DIR,
        DASHBOARD_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

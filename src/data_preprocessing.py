"""Download, clean, merge, and enrich BTC/LINK historical market data.

This module is intentionally local and file-based. It creates the processed
Excel and CSV files consumed by the analysis scripts and the Power BI report.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

from config import (
    BTC_TICKER,
    END_DATE,
    LINK_TICKER,
    PROCESSED_CSV,
    PROCESSED_EXCEL,
    RAW_DIR,
    START_DATE,
    ensure_project_directories,
)


BASE_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
NORMALIZE_COLUMNS = [
    "BTC_Open",
    "BTC_High",
    "BTC_Low",
    "BTC_Close",
    "BTC_Volume",
    "LINK_Open",
    "LINK_High",
    "LINK_Low",
    "LINK_Close",
    "LINK_Volume",
]


def download_asset_data(ticker: str, prefix: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Download one asset from Yahoo Finance and return prefixed OHLCV columns."""
    print(f"Downloading {ticker} from {start_date} to {end_date}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)

    if data.empty:
        raise RuntimeError(f"No data downloaded for {ticker}. Check the ticker, date range, or internet connection.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    missing_columns = [column for column in BASE_COLUMNS if column not in data.columns]
    if missing_columns:
        raise RuntimeError(f"{ticker} download is missing columns: {missing_columns}")

    data = data[BASE_COLUMNS].dropna().copy()
    rename_map = {
        "Open": f"{prefix}_Open",
        "High": f"{prefix}_High",
        "Low": f"{prefix}_Low",
        "Close": f"{prefix}_Close",
        "Volume": f"{prefix}_Volume",
    }
    data = data.rename(columns=rename_map)
    data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None)

    for column in data.columns:
        if column != "Date":
            data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna().sort_values("Date").reset_index(drop=True)
    raw_path = RAW_DIR / f"{prefix.lower()}_raw.csv"
    data.to_csv(raw_path, index=False)
    print(f"Saved raw {prefix} data to {raw_path}")
    return data


def add_proxy_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Create reproducible return, ratio, and proxy metrics in Python.

    Proxy columns are not official blockchain supply, demand, or market-cap
    values. Legacy column names are retained for Power BI compatibility.
    """
    enriched = data.copy()

    for prefix in ("BTC", "LINK"):
        open_col = f"{prefix}_Open"
        close_col = f"{prefix}_Close"
        volume_col = f"{prefix}_Volume"

        enriched[f"{prefix}_Price_Change"] = enriched[close_col] - enriched[open_col]
        enriched[f"{prefix}_Daily_Return"] = ((enriched[close_col] - enriched[open_col]) / enriched[open_col]) * 100
        enriched[f"{prefix}_Intraday_Return_Pct"] = enriched[f"{prefix}_Daily_Return"]

        enriched[f"{prefix}_Supply_Proxy"] = (enriched[open_col] / enriched[close_col]) * enriched[volume_col]
        enriched[f"{prefix}_Demand_Proxy"] = (enriched[close_col] / enriched[open_col]) * enriched[volume_col]
        enriched[f"{prefix}_Market_Value_Proxy"] = enriched[close_col] * enriched[f"{prefix}_Supply_Proxy"]

        # Backward-compatible columns used by the original workbook/Power BI file.
        enriched[f"{prefix}_Supply"] = enriched[f"{prefix}_Supply_Proxy"]
        enriched[f"{prefix}_Demand"] = enriched[f"{prefix}_Demand_Proxy"]
        enriched[f"{prefix}_Inflation"] = enriched[f"{prefix}_Intraday_Return_Pct"]
        enriched[f"{prefix}_MarketCap"] = enriched[f"{prefix}_Market_Value_Proxy"]

    enriched["Price_Ratio"] = enriched["BTC_Close"] / enriched["LINK_Close"]
    enriched = enriched.replace([np.inf, -np.inf], np.nan)
    return enriched.dropna().reset_index(drop=True)


def add_normalized_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Add Min-Max normalized versions of selected OHLCV columns."""
    missing_columns = [column for column in NORMALIZE_COLUMNS if column not in data.columns]
    if missing_columns:
        raise RuntimeError(f"Cannot normalize because these columns are missing: {missing_columns}")

    normalized = data.copy()
    scaler = MinMaxScaler()
    normalized_values = scaler.fit_transform(normalized[NORMALIZE_COLUMNS])

    normalized_columns = [f"{column}_Norm" for column in NORMALIZE_COLUMNS]
    normalized_df = pd.DataFrame(normalized_values, columns=normalized_columns, index=normalized.index)
    normalized = pd.concat([normalized, normalized_df], axis=1)
    return normalized


def order_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Return columns in a stable order for Excel, CSV, and Power BI refreshes."""
    ordered_columns = [
        "Date",
        "BTC_Open",
        "BTC_High",
        "BTC_Low",
        "BTC_Close",
        "BTC_Volume",
        "BTC_Supply",
        "BTC_Demand",
        "BTC_Daily_Return",
        "BTC_Price_Change",
        "BTC_Inflation",
        "BTC_MarketCap",
        "BTC_Supply_Proxy",
        "BTC_Demand_Proxy",
        "BTC_Intraday_Return_Pct",
        "BTC_Market_Value_Proxy",
        "LINK_Open",
        "LINK_High",
        "LINK_Low",
        "LINK_Close",
        "LINK_Volume",
        "LINK_Supply",
        "LINK_Demand",
        "LINK_Daily_Return",
        "LINK_Price_Change",
        "LINK_Inflation",
        "LINK_MarketCap",
        "LINK_Supply_Proxy",
        "LINK_Demand_Proxy",
        "LINK_Intraday_Return_Pct",
        "LINK_Market_Value_Proxy",
        "Price_Ratio",
        "BTC_Open_Norm",
        "BTC_High_Norm",
        "BTC_Low_Norm",
        "BTC_Close_Norm",
        "BTC_Volume_Norm",
        "LINK_Open_Norm",
        "LINK_High_Norm",
        "LINK_Low_Norm",
        "LINK_Close_Norm",
        "LINK_Volume_Norm",
    ]
    return data[ordered_columns]


def round_processed_data(data: pd.DataFrame) -> pd.DataFrame:
    """Round numeric fields for readable exported files while keeping precision."""
    rounded = data.copy()
    numeric_columns = rounded.select_dtypes(include=["number"]).columns
    rounded[numeric_columns] = rounded[numeric_columns].round(6)
    return rounded


def build_processed_dataset(start_date: str = START_DATE, end_date: str = END_DATE) -> pd.DataFrame:
    """Run the full preprocessing workflow and return the processed dataset."""
    ensure_project_directories()

    btc_data = download_asset_data(BTC_TICKER, "BTC", start_date, end_date)
    link_data = download_asset_data(LINK_TICKER, "LINK", start_date, end_date)

    merged = pd.merge(btc_data, link_data, on="Date", how="inner")
    merged = merged.sort_values("Date").reset_index(drop=True)
    print(f"Merged dataset contains {len(merged):,} rows.")

    processed = add_proxy_metrics(merged)
    processed = add_normalized_columns(processed)
    processed = order_columns(processed)
    processed = round_processed_data(processed)
    return processed


def export_processed_dataset(data: pd.DataFrame, excel_path: Path = PROCESSED_EXCEL, csv_path: Path = PROCESSED_CSV) -> None:
    """Export processed data to Excel and CSV."""
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    data.to_excel(excel_path, index=False)
    data.to_csv(csv_path, index=False)

    print(f"Saved processed Excel file to {excel_path}")
    print(f"Saved processed CSV file to {csv_path}")


def main() -> None:
    """CLI entry point for preprocessing."""
    try:
        processed_data = build_processed_dataset()
        export_processed_dataset(processed_data)
        print("Data preprocessing completed successfully.")
    except Exception as exc:
        raise SystemExit(f"Data preprocessing failed: {exc}") from exc


if __name__ == "__main__":
    main()

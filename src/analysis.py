"""Exploratory BTC/LINK financial data analysis.

The script reads the processed dataset created by data_preprocessing.py and
saves chart/table outputs for portfolio review and Power BI support.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from config import CHARTS_DIR, PROCESSED_CSV, PROCESSED_EXCEL, TABLES_DIR, ensure_project_directories


REQUIRED_COLUMNS = [
    "Date",
    "BTC_Close",
    "LINK_Close",
    "BTC_Volume",
    "LINK_Volume",
    "BTC_Daily_Return",
    "LINK_Daily_Return",
    "Price_Ratio",
    "BTC_Supply_Proxy",
    "LINK_Supply_Proxy",
    "BTC_Demand_Proxy",
    "LINK_Demand_Proxy",
    "BTC_Market_Value_Proxy",
    "LINK_Market_Value_Proxy",
]


def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset from CSV when available, otherwise Excel."""
    if PROCESSED_CSV.exists():
        data = pd.read_csv(PROCESSED_CSV)
    elif PROCESSED_EXCEL.exists():
        data = pd.read_excel(PROCESSED_EXCEL)
    else:
        raise FileNotFoundError(
            "Processed data file was not found. Run `python src/data_preprocessing.py` first."
        )

    data["Date"] = pd.to_datetime(data["Date"])
    data["Year"] = data["Date"].dt.year
    validate_required_columns(data, REQUIRED_COLUMNS)
    return data.sort_values("Date").reset_index(drop=True)


def validate_required_columns(data: pd.DataFrame, required_columns: list[str]) -> None:
    """Raise a clear error if required columns are missing."""
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Processed dataset is missing required columns: {missing_columns}")


def save_current_figure(path) -> None:
    """Save and close the current Matplotlib figure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Saved chart: {path}")


def analyze_yearly_volatility(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate yearly return volatility and save a comparison chart/table."""
    yearly_volatility = (
        data.groupby("Year")[["BTC_Daily_Return", "LINK_Daily_Return"]]
        .std()
        .rename(columns={"BTC_Daily_Return": "BTC_Volatility", "LINK_Daily_Return": "LINK_Volatility"})
        .reset_index()
    )
    yearly_volatility["More_Volatile_Asset"] = np.where(
        yearly_volatility["BTC_Volatility"] > yearly_volatility["LINK_Volatility"],
        "BTC",
        np.where(yearly_volatility["LINK_Volatility"] > yearly_volatility["BTC_Volatility"], "LINK", "Equal"),
    )
    yearly_volatility.to_csv(TABLES_DIR / "yearly_volatility.csv", index=False)

    plt.figure(figsize=(10, 6))
    plt.plot(yearly_volatility["Year"], yearly_volatility["BTC_Volatility"], marker="o", label="BTC")
    plt.plot(yearly_volatility["Year"], yearly_volatility["LINK_Volatility"], marker="o", label="LINK")
    plt.title("Yearly Volatility of Intraday Returns")
    plt.xlabel("Year")
    plt.ylabel("Standard Deviation of Daily Return (%)")
    plt.legend()
    plt.grid(alpha=0.3)
    save_current_figure(CHARTS_DIR / "yearly_volatility.png")
    return yearly_volatility


def analyze_overall_volatility(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate overall return volatility for BTC and LINK."""
    overall_volatility = pd.DataFrame(
        [
            {"Asset": "BTC", "Overall_Volatility": data["BTC_Daily_Return"].std()},
            {"Asset": "LINK", "Overall_Volatility": data["LINK_Daily_Return"].std()},
        ]
    )
    overall_volatility.to_csv(TABLES_DIR / "overall_volatility.csv", index=False)
    print(f"Saved table: {TABLES_DIR / 'overall_volatility.csv'}")
    return overall_volatility


def analyze_correlation(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate and save a correlation matrix and heatmap."""
    correlation_columns = [
        "BTC_Daily_Return",
        "LINK_Daily_Return",
        "BTC_Close",
        "LINK_Close",
        "BTC_Volume",
        "LINK_Volume",
        "Price_Ratio",
        "BTC_Supply_Proxy",
        "LINK_Supply_Proxy",
        "BTC_Demand_Proxy",
        "LINK_Demand_Proxy",
        "BTC_Market_Value_Proxy",
        "LINK_Market_Value_Proxy",
    ]
    correlation_matrix = data[correlation_columns].corr()
    correlation_matrix.to_csv(TABLES_DIR / "correlation_matrix.csv")

    plt.figure(figsize=(13, 10))
    sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("BTC/LINK Correlation Matrix")
    save_current_figure(CHARTS_DIR / "correlation_heatmap.png")
    return correlation_matrix


def analyze_rolling_correlation(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate 30-day rolling return correlation."""
    rolling = data[["Date", "BTC_Daily_Return", "LINK_Daily_Return"]].copy()
    rolling["Rolling_30_Day_Correlation"] = rolling["BTC_Daily_Return"].rolling(30).corr(rolling["LINK_Daily_Return"])
    rolling.to_csv(TABLES_DIR / "rolling_correlation.csv", index=False)

    plt.figure(figsize=(11, 5.5))
    plt.plot(rolling["Date"], rolling["Rolling_30_Day_Correlation"], color="#2563eb")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("30-Day Rolling Correlation: BTC vs LINK Daily Returns")
    plt.xlabel("Date")
    plt.ylabel("Correlation")
    plt.grid(alpha=0.3)
    save_current_figure(CHARTS_DIR / "rolling_30_day_correlation.png")
    return rolling


def analyze_price_ratio(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze BTC/LINK close price ratio."""
    yearly_ratio = (
        data.groupby("Year")
        .agg(
            Average_Price_Ratio=("Price_Ratio", "mean"),
            Minimum_Price_Ratio=("Price_Ratio", "min"),
            Maximum_Price_Ratio=("Price_Ratio", "max"),
        )
        .reset_index()
    )
    yearly_ratio.to_csv(TABLES_DIR / "yearly_price_ratio.csv", index=False)

    highest_row = data.loc[data["Price_Ratio"].idxmax()]
    lowest_row = data.loc[data["Price_Ratio"].idxmin()]
    extremes = pd.DataFrame(
        [
            {
                "Metric": "Highest BTC/LINK Price Ratio",
                "Date": highest_row["Date"],
                "Price_Ratio": highest_row["Price_Ratio"],
            },
            {
                "Metric": "Lowest BTC/LINK Price Ratio",
                "Date": lowest_row["Date"],
                "Price_Ratio": lowest_row["Price_Ratio"],
            },
        ]
    )
    extremes.to_csv(TABLES_DIR / "price_ratio_extremes.csv", index=False)

    plt.figure(figsize=(11, 5.5))
    plt.plot(data["Date"], data["Price_Ratio"], color="#7c3aed")
    plt.title("BTC Close / LINK Close Price Ratio")
    plt.xlabel("Date")
    plt.ylabel("Price Ratio")
    plt.grid(alpha=0.3)
    save_current_figure(CHARTS_DIR / "price_ratio_trend.png")
    return yearly_ratio, extremes


def analyze_moving_averages(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate and chart 30-day and 90-day moving averages."""
    moving_average_data = data[["Date", "BTC_Close", "LINK_Close"]].copy()
    for asset in ("BTC", "LINK"):
        moving_average_data[f"{asset}_MA_30"] = moving_average_data[f"{asset}_Close"].rolling(30).mean()
        moving_average_data[f"{asset}_MA_90"] = moving_average_data[f"{asset}_Close"].rolling(90).mean()

    moving_average_data.to_csv(TABLES_DIR / "moving_averages.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(moving_average_data["Date"], moving_average_data["BTC_Close"], alpha=0.45, label="BTC Close")
    axes[0].plot(moving_average_data["Date"], moving_average_data["BTC_MA_30"], label="BTC 30-Day MA")
    axes[0].plot(moving_average_data["Date"], moving_average_data["BTC_MA_90"], label="BTC 90-Day MA")
    axes[0].set_title("BTC Moving Averages")
    axes[0].set_ylabel("Close Price")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(moving_average_data["Date"], moving_average_data["LINK_Close"], alpha=0.45, label="LINK Close")
    axes[1].plot(moving_average_data["Date"], moving_average_data["LINK_MA_30"], label="LINK 30-Day MA")
    axes[1].plot(moving_average_data["Date"], moving_average_data["LINK_MA_90"], label="LINK 90-Day MA")
    axes[1].set_title("LINK Moving Averages")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Close Price")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    save_current_figure(CHARTS_DIR / "moving_averages.png")
    return moving_average_data


def analyze_drawdown(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate cumulative return and drawdown for BTC and LINK."""
    drawdown_data = data[["Date", "BTC_Close", "LINK_Close"]].copy()

    max_drawdown_rows = []
    for asset in ("BTC", "LINK"):
        close_col = f"{asset}_Close"
        cumulative_col = f"{asset}_Cumulative_Return"
        drawdown_col = f"{asset}_Drawdown"

        drawdown_data[cumulative_col] = drawdown_data[close_col] / drawdown_data[close_col].iloc[0] - 1
        running_peak = drawdown_data[close_col].cummax()
        drawdown_data[drawdown_col] = drawdown_data[close_col] / running_peak - 1

        max_drawdown_index = drawdown_data[drawdown_col].idxmin()
        max_drawdown_rows.append(
            {
                "Asset": asset,
                "Max_Drawdown": drawdown_data.loc[max_drawdown_index, drawdown_col],
                "Max_Drawdown_Date": drawdown_data.loc[max_drawdown_index, "Date"],
            }
        )

    max_drawdown = pd.DataFrame(max_drawdown_rows)
    drawdown_data.to_csv(TABLES_DIR / "drawdown_timeseries.csv", index=False)
    max_drawdown.to_csv(TABLES_DIR / "max_drawdown.csv", index=False)

    plt.figure(figsize=(11, 5.5))
    plt.plot(drawdown_data["Date"], drawdown_data["BTC_Drawdown"], label="BTC Drawdown")
    plt.plot(drawdown_data["Date"], drawdown_data["LINK_Drawdown"], label="LINK Drawdown")
    plt.title("BTC vs LINK Drawdown Comparison")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.grid(alpha=0.3)
    save_current_figure(CHARTS_DIR / "drawdown_comparison.png")
    return drawdown_data, max_drawdown


def main() -> None:
    """Run all analysis steps."""
    try:
        ensure_project_directories()
        sns.set_theme(style="whitegrid")
        data = load_processed_data()

        analyze_yearly_volatility(data)
        analyze_overall_volatility(data)
        analyze_correlation(data)
        analyze_rolling_correlation(data)
        analyze_price_ratio(data)
        analyze_moving_averages(data)
        analyze_drawdown(data)

        print("Analysis completed successfully.")
    except Exception as exc:
        raise SystemExit(f"Analysis failed: {exc}") from exc


if __name__ == "__main__":
    main()

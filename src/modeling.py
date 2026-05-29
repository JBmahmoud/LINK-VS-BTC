"""Exploratory linear regression modeling for LINK close price.

The model is used only to study relationships in the processed dataset. It is
not a trading model and should not be used for financial decision-making.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from config import CHARTS_DIR, PROCESSED_CSV, PROCESSED_EXCEL, TABLES_DIR, ensure_project_directories


TARGET_COLUMN = "LINK_Close"
FEATURE_COLUMNS = ["BTC_Close", "LINK_Supply_Proxy", "LINK_Demand_Proxy"]
REQUIRED_COLUMNS = ["Date", TARGET_COLUMN, *FEATURE_COLUMNS]


def load_modeling_data() -> pd.DataFrame:
    """Load processed data for modeling."""
    if PROCESSED_CSV.exists():
        data = pd.read_csv(PROCESSED_CSV)
    elif PROCESSED_EXCEL.exists():
        data = pd.read_excel(PROCESSED_EXCEL)
    else:
        raise FileNotFoundError(
            "Processed data file was not found. Run `python src/data_preprocessing.py` first."
        )

    data["Date"] = pd.to_datetime(data["Date"])
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Processed dataset is missing required modeling columns: {missing_columns}")

    model_data = data[REQUIRED_COLUMNS].replace([np.inf, -np.inf], np.nan).dropna()
    if model_data.empty:
        raise ValueError("No valid rows remain for modeling after dropping missing or infinite values.")

    return model_data.sort_values("Date").reset_index(drop=True)


def run_train_test_regression(data: pd.DataFrame) -> tuple[LinearRegression, pd.DataFrame, pd.DataFrame]:
    """Fit a time-ordered train/test linear regression model."""
    x = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, shuffle=False)
    test_dates = data.loc[x_test.index, "Date"].reset_index(drop=True)

    model = LinearRegression()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    residuals = y_test.to_numpy() - predictions

    metrics = pd.DataFrame(
        [
            {"Metric": "R2", "Value": r2_score(y_test, predictions)},
            {"Metric": "MAE", "Value": mean_absolute_error(y_test, predictions)},
            {"Metric": "RMSE", "Value": np.sqrt(mean_squared_error(y_test, predictions))},
            {"Metric": "Training_Rows", "Value": len(x_train)},
            {"Metric": "Testing_Rows", "Value": len(x_test)},
        ]
    )

    coefficients = pd.DataFrame(
        [{"Feature": "Intercept", "Coefficient": model.intercept_}]
        + [
            {"Feature": feature, "Coefficient": coefficient}
            for feature, coefficient in zip(FEATURE_COLUMNS, model.coef_)
        ]
    )

    predictions_table = pd.DataFrame(
        {
            "Date": test_dates,
            "Actual_LINK_Close": y_test.reset_index(drop=True),
            "Predicted_LINK_Close": predictions,
            "Residual": residuals,
        }
    )

    return model, metrics, coefficients, predictions_table


def save_model_outputs(metrics: pd.DataFrame, coefficients: pd.DataFrame, predictions: pd.DataFrame) -> None:
    """Save regression tables and diagnostic charts."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(TABLES_DIR / "regression_metrics.csv", index=False)
    coefficients.to_csv(TABLES_DIR / "regression_coefficients.csv", index=False)
    predictions.to_csv(TABLES_DIR / "regression_predictions.csv", index=False)

    plt.figure(figsize=(11, 5.5))
    plt.plot(predictions["Date"], predictions["Actual_LINK_Close"], label="Actual LINK Close")
    plt.plot(predictions["Date"], predictions["Predicted_LINK_Close"], label="Predicted LINK Close", alpha=0.85)
    plt.title("Exploratory Regression: LINK Actual vs Predicted Close")
    plt.xlabel("Date")
    plt.ylabel("LINK Close")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "link_actual_vs_predicted.png", dpi=160, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(9, 5.5))
    plt.scatter(predictions["Predicted_LINK_Close"], predictions["Residual"], alpha=0.65)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Exploratory Regression Residuals")
    plt.xlabel("Predicted LINK Close")
    plt.ylabel("Residual")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "regression_residuals.png", dpi=160, bbox_inches="tight")
    plt.close()

    print(f"Saved table: {TABLES_DIR / 'regression_metrics.csv'}")
    print(f"Saved table: {TABLES_DIR / 'regression_coefficients.csv'}")
    print(f"Saved chart: {CHARTS_DIR / 'link_actual_vs_predicted.png'}")
    print(f"Saved chart: {CHARTS_DIR / 'regression_residuals.png'}")


def main() -> None:
    """Run the exploratory regression workflow."""
    try:
        ensure_project_directories()
        data = load_modeling_data()
        _model, metrics, coefficients, predictions = run_train_test_regression(data)
        save_model_outputs(metrics, coefficients, predictions)
        print("Modeling completed successfully. This model is exploratory only.")
    except Exception as exc:
        raise SystemExit(f"Modeling failed: {exc}") from exc


if __name__ == "__main__":
    main()

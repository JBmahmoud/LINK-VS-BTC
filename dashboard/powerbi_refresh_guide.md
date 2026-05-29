# Power BI Refresh Guide

This project keeps the Power BI report local and does not automatically edit the `.pbix` file.

## Current Dashboard File

Open this file in Power BI Desktop:

```text
dashboard/Dashboard Jaber Mahmoud 235479.pbix
```

## Refresh Steps

1. Run the Python preprocessing pipeline:

   ```powershell
   python src/data_preprocessing.py
   ```

2. Confirm the processed Excel file exists:

   ```text
   data/processed/Link_Bitcoin.xlsx
   ```

3. Open `dashboard/Dashboard Jaber Mahmoud 235479.pbix` in Power BI Desktop.

4. In Power BI Desktop, open data source settings.

5. If the workbook path points to the old project root, update it to:

   ```text
   data/processed/Link_Bitcoin.xlsx
   ```

6. Refresh the report.

7. Verify that the existing pages still render correctly:

   - Close
   - Volume
   - Supply
   - Demand
   - Inflation
   - Market
   - Ratio

## Notes About Renamed Metrics

The improved Python pipeline keeps legacy columns such as `BTC_Supply`, `LINK_Demand`, `BTC_Inflation`, and `LINK_MarketCap` so the original dashboard can refresh.

The pipeline also adds clearer proxy metric names:

- `BTC_Supply_Proxy`
- `BTC_Demand_Proxy`
- `BTC_Market_Value_Proxy`
- `LINK_Supply_Proxy`
- `LINK_Demand_Proxy`
- `LINK_Market_Value_Proxy`
- `BTC_Intraday_Return_Pct`
- `LINK_Intraday_Return_Pct`

These proxy metrics are calculated from OHLCV data. They are not official blockchain supply, demand, inflation, or market-cap values.

## Recommended Improved Power BI Page Structure

For a stronger portfolio dashboard, consider manually restructuring the report into:

1. Executive Summary
2. Price Trend Comparison
3. Volume Comparison
4. Volatility Analysis
5. Correlation Analysis
6. Price Ratio Analysis
7. Regression Results

## Manual Check After Refresh

After refreshing, confirm:

- Date filters still work.
- Existing visual fields still resolve.
- No visual shows a missing field error.
- New proxy metrics are available in the data pane.
- The report still uses the intended processed workbook.

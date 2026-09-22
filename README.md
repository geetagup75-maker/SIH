# ✈️ Real-Time Airfare Price Index for India — Revised

## What was changed

1. **Index logic reframed:** the live calculation is explicitly a **DGCA passenger-weighted Lowe/Laspeyres-style index**. Paasche/Fisher are not used without observed current/base quantities.
2. **`route_weights` table:** SQLite migration creates a table for verified DGCA route passenger percentages.
3. **Advance-booking stratification:** index aggregation uses **1–3, 7–14 and 15–30 days**. Each route/window requires N ≥ 5 in both base and target periods.
4. **Dynamic paths:** modules use `Path(__file__).resolve().parent`; no dashboard-relative DB path is required.
5. **Trigger Live Scrape demo:** the button safely creates a parsed/fallback record, inserts it into SQLite, and recalculates the index. It does not fake a claim of external scraping.
6. **Pinned requirements:** exact versions are in `requirements.txt`.
7. **Dynamic index time series:** `dashboard/pages/1_📈_Index_Trends.py` recalculates from `fare_records` instead of relying only on stored `index_values`.
8. **Sample-size checks:** outlier analysis returns `insufficient_sample` for N < 5.
9. **CPI Comparison tab:** accepts an official MOSPI CSV and overlays it with the generated airfare index. No official CPI values are invented.
10. **Documentation:** this README documents the revised architecture and setup.

## Architecture

```text
DGCA / authorized fare source
          │
          ▼
   Fare collection/parser
          │
          ▼
     SQLite fare_records
          │
          ▼
 Cleaning + duplicate removal
          │
          ├──────────────► IQR / Z / MAD (N ≥ 5)
          │
          ▼
 Advance-window stratification
  1–3 | 7–14 | 15–30 days
          │
          ▼
 DGCA route passenger weights
          │
          ▼
 Lowe / Laspeyres-style price relatives
          │
          ▼
 Dynamic time-series index
          │
          ├────────► Streamlit dashboard
          └────────► MOSPI CPI comparison
```

## Important data-integrity note

The uploaded database did not contain a `route_weights` table. Therefore this revision creates the table but **does not fabricate official DGCA percentages**. Populate it only with verified DGCA route-level passenger traffic percentages and retain the source/reference period in each row.

DGCA publishes domestic-air-transport traffic statistics, including sector/city and passenger information. Use the official DGCA source when populating the table.

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt

python migrate_route_weights.py

python -m streamlit run app.py
```

## Route-weight CSV format

`data/route_weights_template.csv`:

```text
route,passenger_percentage,source,reference_period,official
DEL → BOM,<verified percentage>,DGCA,<month/year>,1
```

Do not use sample percentages in a production index.

## CPI comparison CSV

The dashboard expects:

```text
date,cpi_index
2026-08-01,xxx.xx
2026-09-01,xxx.xx
```

Use an official MOSPI series and preserve its base/series metadata when presenting results.

## Database

Existing `fare_records` and `index_values` are preserved. A new `route_weights` table is created by `migrate_route_weights.py`.

## Live scrape demo

The Streamlit **Trigger Live Scrape** button intentionally uses a safe fallback record generated from an existing fare record. It is a demonstration of the end-to-end insertion/recalculation path, not a claim that a live airline/OTA request was executed.

Replace `live_demo.py` with the project's authorized scraper/API parser when credentials and source access are available.

# ✈️ Real-Time Airfare Price Index for India

## Development of a Real-Time Airfare Price Index for India through Automated Collection and Statistical Processing of Airfare Data for CPI Augmentation

A Streamlit-based analytical system for collecting, cleaning, analyzing, weighting, and visualizing domestic airfare observations in India.

The project is designed to produce a transparent airfare price indicator that can be evaluated alongside official CPI trends. The current implementation uses a **DGCA-weighted Lowe/Laspeyres-style framework** rather than presenting Paasche or Fisher results when the required current-period quantity data are unavailable.

---

## 📌 Project Overview

Airfare prices can change substantially depending on:

- Route
- Airline
- Travel date
- Advance booking period
- Fare class
- Data source
- Market conditions

This project converts airfare observations into a structured analytical pipeline:

```text
Airfare Data
     ↓
Data Validation
     ↓
Cleaning & Standardization
     ↓
Duplicate Removal
     ↓
Outlier / Sample-Size Checks
     ↓
Booking-Window Stratification
     ↓
Route Weight Assignment
     ↓
Price Relatives
     ↓
DGCA-Weighted Lowe / Laspeyres-Style Index
     ↓
Time-Series Analysis
     ↓
Streamlit Dashboard
The system also provides a separate CPI Comparison interface for comparing the generated airfare index with an official MOSPI CPI series when such a dataset is supplied.
🎯 Objectives
The project aims to:
1. Collect and process airfare observations.
2. Standardize airfare records into a common schema.
3. Remove duplicate observations.
4. Detect and handle anomalous fare observations.
5. Stratify observations by advance-booking windows.
6. Apply a minimum sample-size requirement of N ≥ 5 for comparable route/window groups.
7. Incorporate externally justified DGCA passenger-traffic weights.
8. Calculate price relatives.
9. Construct a DGCA-weighted Lowe/Laspeyres-style airfare index.
10. Analyze route-level and airline-level airfare movements.
11. Analyze monthly and advance-booking trends.
12. Provide a live-scrape demonstration workflow.
13. Compare the generated airfare index with official CPI data when supplied.
14. Provide a transparent Streamlit dashboard for demonstration and analysis.
🏗️ System Architecture
                    AIRFARE DATA SOURCES
                            │
                            ▼
                 Excel / Live Demo Records
                            │
                            ▼
                    Data Validation
                            │
                            ▼
                 Data Cleaning & Parsing
                            │
                            ▼
                  Duplicate Removal
                            │
                            ▼
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Outlier Detection          Sample Size Check
        IQR / Z-Score / MAD            N ≥ 5
              │                           │
              └─────────────┬─────────────┘
                            ▼
                 Booking Window Groups
                  ┌─────────┼─────────┐
                  ▼         ▼         ▼
                1–3       7–14      15–30
                 days       days       days
                  └─────────┼─────────┘
                            ▼
                  Comparable Fare Data
                            │
                            ▼
                  DGCA Route Weights
                            │
                            ▼
                    Price Relatives
                            │
                            ▼
             Lowe / Laspeyres-Style Index
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Index Trends    Route Analysis  Airline Analysis
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    Streamlit Dashboard
                            │
                            ▼
                     CPI Comparison
📊 Index Methodology
1. Price Relative
For a comparable fare product:
\[
R_t = \frac{P_t}{P_0}\times100
\]where:
- \(P_t\) = current-period price
- \(P_0\) = base-period price
A value of 100 represents the base-period level.
2. Lowe / Laspeyres-Style Weighted Index
The project uses an externally supplied route-weight framework.
A general weighted price-relative form is:
\[
I_t =
\frac{\sum_r w_r R_{r,t}}
{\sum_r w_r}
\]where:
- \(R_{r,t}\) = route-level price relative
- \(w_r\) = externally justified route weight
- \(r\) = route
The route weights are intended to represent passenger-traffic importance.
The implementation is therefore described as a DGCA-weighted Lowe/Laspeyres-style index.
Why not claim Paasche/Fisher?
The airfare database does not contain complete current-period and base-period quantity fields \(Q_t\) and \(Q_0\).
Therefore:
- Paasche is not presented as a fully estimated official index.
- Fisher is not presented as a fully estimated official index.
- Passenger weights must come from an externally justified source.
This avoids inventing quantity data.
🧮 Booking-Window Stratification
Airfares vary strongly with how far in advance the booking is made.
The project therefore groups observations into:
Booking window	Meaning
1–3 days	Near-departure booking
7–14 days	Short-term advance booking
15–30 days	Medium-term advance booking


Comparable index observations are evaluated within these windows before aggregation.
🔎 Sample-Size Requirement
For reliable route/window comparisons, the project applies:
\[
N \geq 5
\]A route and booking-window group with fewer than five comparable observations is flagged as insufficient rather than being silently treated as statistically adequate.
⚖️ DGCA Route Weights
The project contains a route_weights table/template for externally supplied passenger-traffic weights.
Expected information includes:
route
passenger_weight / passenger_percentage
source
reference_period
official
Important
The project does not fabricate DGCA passenger percentages.
The route_weights_template.csv file is a template. Official DGCA passenger-traffic values should be populated before describing the resulting index as an official DGCA-weighted index.
📁 Airfare Input Data
The current project supports the supplied Excel dataset:
data/
└── Combined_Flight_Data.xlsx
The primary sheet used for the airfare pipeline is:
airfare_dataset_SAMPLE
Relevant fields include:
- unique_flight_id
- timestamp_scraped
- travel_date
- lead_time_days
- origin
- destination
- route
- airline
- flight_number
- fare_class
- total_fare
- source_portal
The Excel file is converted into the project's standardized fare_records schema before analytical processing.
The application uses dynamic pathlib.Path references, so the project does not depend on a hardcoded Windows path.
🗄️ Database Structure
SQLite is used for local storage.
fare_records
Main fields include:
id
origin
destination
carrier_code
carrier_name
departure_date
booking_date
advance_days
base_fare
taxes
convenience_fee
total_fare
fare_class
source
scraped_at
index_values
Stores calculated index observations:
id
date
index_value
period
base_value
route_weights
Stores externally supplied route passenger weights used by the weighted index framework.
🧹 Data Preprocessing
The preprocessing pipeline performs:
- Date conversion
- Numeric conversion
- String normalization
- Route construction
- Month extraction
- Year extraction
- Day-of-week extraction
- Fare-component calculations
- Duplicate detection and removal
The system also checks for invalid or incomplete observations before index processing.
🔎 Outlier Detection
Three statistical approaches are available.
IQR
\[
IQR=Q_3-Q_1
\]Lower bound:
\[
Q_1-1.5(IQR)
\]Upper bound:
\[
Q_3+1.5(IQR)
\]Z-Score
\[
Z=\frac{x-\mu}{\sigma}
\]Median Absolute Deviation
MAD is used as a robust alternative for skewed airfare distributions.
The project applies sample-size safeguards so that insufficient groups are not treated as statistically adequate.
📈 Dashboard
The Streamlit dashboard contains:
1. Executive Overview
Displays:
- Average fare
- Median fare
- Number of routes
- Number of airlines
- Number of observations
- Daily airfare trend
- Route comparisons
2. Airfare Price Index
Displays:
- Current index
- Base value
- Index trend
- MoM movement
- YoY movement
- DGCA-weighting status
- Sample-size validation
- Booking-window information
3. Index Trends
Provides dynamic time-series recalculation from the current airfare data and weighting framework.
4. Route Analysis
Provides:
- Average fare by route
- Median fare
- Minimum fare
- Maximum fare
- Fare range
- Route-level observations
5. Airline Analysis
Provides:
- Average fare by airline
- Fare distributions
- Airline comparisons
- Airline-level observations
6. Statistical Analysis
Provides:
- Mean
- Median
- Standard deviation
- Quartiles
- IQR
- Z-score analysis
- MAD analysis
- Coefficient of Variation
7. Time-Series Analysis
Provides:
- Monthly fare trends
- MoM changes
- Day-of-week patterns
- Advance-booking effects
- Fare movement over time
8. Data Quality
Provides:
- Missing values
- Duplicate observations
- Missing percentage
- Data-source coverage
- Record counts
9. CPI Comparison
A separate dashboard section allows the user to upload an official MOSPI CPI dataset and visually compare:
Airfare Price Index
        vs.
Official CPI Series
The CPI series should be sourced from official MOSPI data rather than generated from the airfare dataset.
10. CPI Methodology
Documents the index-number methodology, weighting approach, outlier methods, and limitations.
11. Live Scrape
Provides a controlled demonstration workflow for triggering a live/fallback airfare record, inserting it into SQLite, and refreshing the analytical results.
🔄 Live Scrape Demonstration
The project includes a Trigger Live Scrape workflow.
Its purpose is to demonstrate:
Trigger Live Scrape
       ↓
Obtain / parse fare observation
       ↓
Validate record
       ↓
Insert into SQLite
       ↓
Refresh data
       ↓
Recalculate index
       ↓
Update dashboard
Fallback/demo data should be clearly identified and should not be represented as an official live market observation.
📊 CPI Comparison
The CPI Comparison section is intentionally separate from the airfare dataset.
Required conceptually:
Official MOSPI CPI data
        ↓
Date/period normalization
        ↓
CPI time series
        ↓
Comparison with Airfare Index
The airfare workbook itself is not treated as an official CPI dataset.
🗂️ Project Structure
airfare_index_revised/
│
├── app.py
├── database.py
├── preprocessing.py
├── statistics.py
├── styles.py
├── requirements.txt
├── README.md
├── airfare.db
├── live_demo.py
├── migrate_route_weights.py
│
├── airfare_index/
│   ├── __init__.py
│   ├── index_calculator.py
│   └── outlier_detector.py
│
├── dashboard/
│   └── pages/
│       └── 1_📈_Index_Trends.py
│
└── data/
    ├── Combined_Flight_Data.xlsx
    └── route_weights_template.csv
🧩 Main Modules
app.py
Main Streamlit dashboard and navigation.
database.py
Responsible for:
- SQLite connection
- Fare-record loading
- Index-value loading
- Excel airfare loading
- Route-weight access
preprocessing.py
Responsible for:
- Data cleaning
- Date conversion
- Numeric conversion
- Duplicate handling
- Standardization
airfare_index/index_calculator.py
Responsible for:
- Price relatives
- Lowe/Laspeyres-style calculations
- Weighted calculations
- Index changes
- MoM calculations
- YoY calculations
airfare_index/outlier_detector.py
Responsible for:
- IQR checks
- Z-score checks
- MAD checks
- Minimum sample-size validation
statistics.py
Responsible for:
- Descriptive statistics
- IQR
- Z-score
- MAD
- Coefficient of Variation
dashboard/pages/1_📈_Index_Trends.py
Responsible for dynamic index trend visualization and recalculation.
live_demo.py
Responsible for the controlled live-scrape/fallback demonstration workflow.
migrate_route_weights.py
Creates/updates the route-weight database structure.
🛠️ Technologies Used
Programming
- Python 3.13
Data Processing
- Pandas
- NumPy
- OpenPyXL
Visualization
- Plotly
Dashboard
- Streamlit
Database
- SQLite
Statistical Methods
- IQR
- Z-Score
- Median Absolute Deviation
- Coefficient of Variation
- Price relatives
- Lowe / Laspeyres-style weighted index
File Handling
- pathlib
🚀 Installation
1. Clone the repository
git clone <your-repository-url>
cd airfare_index_revised
2. Install dependencies
pip install -r requirements.txt
If Excel support is required separately:
pip install openpyxl
3. Check the data directory
Place the airfare workbook here:
data/Combined_Flight_Data.xlsx
The application expects the relevant airfare sheet:
airfare_dataset_SAMPLE
4. Initialize route weights
Run:
python migrate_route_weights.py
Populate the route-weight table/template with verified DGCA passenger-traffic data before using the weighted index as an official-data demonstration.
5. Run the dashboard
python -m streamlit run app.py
🔐 Data and Methodology Notes
No fabricated passenger quantities
Passenger weights should come from an externally justified source.
No fabricated CPI values
The CPI Comparison section requires official CPI data.
No unsupported Paasche/Fisher claims
Paasche requires current-period quantities and Fisher requires both Laspeyres and Paasche. Where those quantity inputs are unavailable, the project uses the explicitly documented Lowe/Laspeyres-style framework.
Data-source coverage
Airfare datasets may not cover every airline, route, fare class, or booking condition. Coverage limitations should be documented when interpreting results.
Demonstration vs official statistical production
This project is an analytical/hackathon implementation. It should not be interpreted as an official Government of India CPI series unless independently validated and adopted through the appropriate statistical process.
🎯 Current Project Status
Implemented
- SQLite database integration
- Excel airfare input
- Fare-record standardization
- Data preprocessing
- Duplicate handling
- IQR analysis
- Z-score analysis
- MAD analysis
- Coefficient of Variation
- Route analysis
- Airline analysis
- Time-series analysis
- Data-quality analysis
- Global dashboard filters
- Streamlit dashboard
- Dynamic project paths using pathlib
- Booking-window stratification
- N ≥ 5 sample-size validation
- DGCA route-weight table/template
- Lowe/Laspeyres-style weighted index framework
- Dynamic index-trend page
- CPI Comparison interface
- Live scrape demonstration workflow
- Updated project documentation
Requires verified external data
- Official DGCA route passenger percentages
- Official MOSPI CPI series
- Production-grade authorized live airfare source
- Final statistical validation of the index
📌 Key Methodological Limitation
The airfare dataset provides observed prices but does not by itself provide complete base-period and current-period passenger quantities.
Therefore, the project does not invent \(Q_0\) or \(Q_t\).
Instead, route weights are maintained separately and are intended to be populated using externally justified passenger-traffic data.
This makes the weighting assumption explicit and auditable.
👥 Project
SIH 2026
Real-Time Airfare Price Index for India
Objective: Develop a timely and granular airfare indicator that can support research into CPI transport-price measurement.

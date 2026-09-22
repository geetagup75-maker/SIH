import sqlite3
from pathlib import Path
import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DB_PATH = PROJECT_ROOT / "airfare.db"

DATA_DIR = PROJECT_ROOT / "data"

EXCEL_PATH = DATA_DIR / "Combined_Flight_Data.xlsx"

EXCEL_SHEET = "airfare_dataset_SAMPLE"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def load_fare_records():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM fare_records", conn)

def load_index_values():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM index_values", conn)

def ensure_route_weights_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS route_weights (
                route TEXT PRIMARY KEY,
                passenger_percentage REAL NOT NULL,
                source TEXT NOT NULL,
                reference_period TEXT NOT NULL,
                official INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def load_route_weights():
    ensure_route_weights_table()
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT route, passenger_percentage, source, reference_period, official "
            "FROM route_weights ORDER BY passenger_percentage DESC",
            conn,
        )

def upsert_route_weights(df: pd.DataFrame):
    required = {"route", "passenger_percentage", "source", "reference_period"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing route-weight columns: {sorted(missing)}")
    ensure_route_weights_table()
    rows = df[list(required)].copy()
    rows["official"] = rows.get("official", 1)
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO route_weights
            (route, passenger_percentage, source, reference_period, official)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(route) DO UPDATE SET
                passenger_percentage=excluded.passenger_percentage,
                source=excluded.source,
                reference_period=excluded.reference_period,
                official=excluded.official
            """,
            rows[["route","passenger_percentage","source","reference_period","official"]].itertuples(index=False, name=None),
        )
        conn.commit()

def insert_fare_records(df: pd.DataFrame):
    required = [
        "origin","destination","carrier_code","carrier_name","departure_date",
        "booking_date","advance_days","base_fare","taxes","convenience_fee",
        "total_fare","fare_class","source","scraped_at"
    ]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing fare columns: {sorted(missing)}")
    with get_connection() as conn:
        df[required].to_sql("fare_records", conn, if_exists="append", index=False)

def save_index_value(date, index_value, period, base_value=100.0):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO index_values(date,index_value,period,base_value) VALUES (?,?,?,?)",
            (str(date), float(index_value), str(period), float(base_value)),
        )
        conn.commit()
# =========================================================
# LOAD AIRFARE DATA FROM EXCEL
# =========================================================

def load_airfare_excel():

    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Excel file not found:\n{EXCEL_PATH}"
        )

    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name=EXCEL_SHEET
    )

    required_columns = [
        "unique_flight_id",
        "timestamp_scraped",
        "travel_date",
        "lead_time_days",
        "origin",
        "destination",
        "route",
        "airline",
        "flight_number",
        "fare_class",
        "total_fare",
        "source_portal"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns in Excel sheet "
            f"'{EXCEL_SHEET}': {missing_columns}"
        )

    # -----------------------------------------------------
    # DATE CONVERSION
    # -----------------------------------------------------

    df["travel_date"] = pd.to_datetime(
        df["travel_date"],
        errors="coerce"
    )

    df["timestamp_scraped"] = pd.to_datetime(
        df["timestamp_scraped"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # NUMERIC CONVERSION
    # -----------------------------------------------------

    df["lead_time_days"] = pd.to_numeric(
        df["lead_time_days"],
        errors="coerce"
    )

    df["total_fare"] = pd.to_numeric(
        df["total_fare"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # CONVERT TO YOUR fare_records STRUCTURE
    # -----------------------------------------------------

    records = pd.DataFrame()

    records["origin"] = df["origin"]

    records["destination"] = df["destination"]

    records["carrier_code"] = (
        df["airline"]
        .astype("string")
        .str.upper()
        .str.replace(" ", "", regex=False)
    )

    records["carrier_name"] = df["airline"]

    records["departure_date"] = df["travel_date"]

    # Observation/scraping date
    records["booking_date"] = (
        df["timestamp_scraped"].dt.normalize()
    )

    records["advance_days"] = df["lead_time_days"]

    # The Excel dataset gives total_fare.
    # It does NOT separately provide base fare,
    # taxes and convenience fee.
    records["base_fare"] = df["total_fare"]

    records["taxes"] = 0.0

    records["convenience_fee"] = 0.0

    records["total_fare"] = df["total_fare"]

    records["fare_class"] = df["fare_class"]

    records["source"] = df["source_portal"]

    records["scraped_at"] = df["timestamp_scraped"]

    # -----------------------------------------------------
    # REMOVE INVALID RECORDS
    # -----------------------------------------------------

    records = records.dropna(
        subset=[
            "origin",
            "destination",
            "departure_date",
            "advance_days",
            "total_fare"
        ]
    )

    records = records[
        records["total_fare"] > 0
    ]

    return records.reset_index(drop=True)
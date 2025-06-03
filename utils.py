# utils.py

import base64
import io
import uuid
import time
from datetime import datetime

import polars as pl
import pandas as pd
from sqlalchemy import create_engine, text
import sqlalchemy

# ——— Database connection ———
SERVER = 'CND3420Y19'
DATABASE = 'TransactionsDB'
engine = create_engine(
    f'mssql+pyodbc://@{SERVER}/{DATABASE}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server',
    connect_args={'fast_executemany': True}
)

# ——— Cache for historical fraud rate ———
_cache = {}
_CACHE_TIMEOUT = 300  # seconds


def process_uploaded_file(contents: str) -> pd.DataFrame | None:
    """
    Decode base64-encoded CSV, clean and normalize columns, add a unique
    transaction_id, cast types, and return a pandas DataFrame.
    Returns None on error.
    """
    try:
        _, b64 = contents.split(',', 1)
        decoded = base64.b64decode(b64).decode('utf-8')
        lines = decoded.splitlines()
        if not lines:
            raise ValueError("Empty file")

        # detect & skip duplicate headers
        header = [c.strip().lower() for c in lines[0].split(',')]
        if "fraud" in header and len(lines) > 1:
            second = [c.strip().lower() for c in lines[1].split(',')]
            if set(second) == set(header):
                lines = lines[2:]

        csv_data = "\n".join(lines)
        df_pl = pl.read_csv(io.StringIO(csv_data), try_parse_dates=False)

        # clean column names
        clean_cols = [c.replace('[','').replace(']','').strip() for c in df_pl.columns]
        df_pl.columns = clean_cols
        df_pl = df_pl.fill_null(0)

        # add transaction_id
        df_pl = df_pl.with_columns(
            pl.Series("transaction_id", [str(uuid.uuid4())] * df_pl.height)
        )

        # cast types
        if 'fraud' in df_pl.columns:
            df_pl = df_pl.with_columns([
                pl.col("amount").cast(pl.Float64),
                pl.col("fraud").cast(pl.Int64)
            ]).filter(pl.col("fraud").is_in([0,1]))
        else:
            df_pl = df_pl.with_columns(pl.col("amount").cast(pl.Float64))

        return df_pl.to_pandas()

    except Exception as e:
        print(f"[utils] Error in process_uploaded_file: {e}")
        return None


def save_to_database(df: pd.DataFrame, file_name: str = "") -> str | None:
    """
    Write the given DataFrame to transactions_<timestamp>.
    Only tables with a 'fraud' column are recorded in MasterTable.
    Returns the table name or None on failure.
    """
    table_name = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        required = ['customer','zipcodeOri','merchant','zipMerchant','category','amount','fraud']
        subset = df[[c for c in required if c in df.columns]].copy()
        subset.columns = [c.replace('[','').replace(']','') for c in subset.columns]

        subset.to_sql(
            table_name,
            engine,
            if_exists='replace',
            index=False,
            chunksize=5000,
            dtype={col: sqlalchemy.types.String() for col in subset.columns}
        )

        # record only training tables
        if 'fraud' in subset.columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO dbo.MasterTable (table_name, file_name, uploaded_at) "
                        "VALUES (:tn, :fn, GETDATE())"
                    ),
                    {"tn": table_name, "fn": file_name}
                )

        return table_name

    except Exception as e:
        print(f"[utils] Error in save_to_database: {e}")
        return None


def get_historical_fraud_rate() -> float | None:
    """
    Compute and cache the overall fraud rate across tables that truly
    contain a 'fraud' column. Returns percentage 0–100, or None.
    """
    now = time.time()
    if 'fraud_rate' in _cache and now - _cache['ts'] < _CACHE_TIMEOUT:
        return _cache['fraud_rate']

    try:
        schema_sql = """
        SELECT m.table_name
        FROM dbo.MasterTable AS m
        JOIN INFORMATION_SCHEMA.COLUMNS AS c
          ON c.TABLE_SCHEMA = 'dbo'
         AND c.TABLE_NAME = m.table_name
         AND c.COLUMN_NAME = 'fraud'
        WHERE m.table_name LIKE 'transactions_%'
        """
        tbls = pd.read_sql(schema_sql, engine)
        if tbls.empty:
            return None

        unions = [
            f"SELECT fraud FROM dbo.{t} WHERE fraud IN (0,1)"
            for t in tbls['table_name']
        ]
        full_q = " UNION ALL ".join(unions)
        df_all = pd.read_sql(full_q, engine)
        if df_all.empty:
            return None

        rate = df_all['fraud'].astype(int).mean() * 100
        _cache['fraud_rate'] = rate
        _cache['ts'] = now
        return rate

    except Exception as e:
        print(f"[utils] Error in get_historical_fraud_rate: {e}")
        return None

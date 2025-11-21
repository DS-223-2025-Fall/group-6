import pandas as pd
from sqlalchemy import text
from Database.database import engine
from loguru import logger
from sqlalchemy.orm import Session
from Database.models import DimDate
from datetime import datetime

def load_user_activity_and_subscription_dfs():
    """
    Load fact_user_daily_activity and dim_subscription_plan tables into pandas DataFrames.
    Merge on subscription_plan_key to get base_price for monetary calculation.
    Returns merged DataFrame with necessary columns.
    """
    with engine.connect() as conn:
        # Load fact_user_daily_activity
        activity_df = pd.read_sql_table("fact_user_daily_activity", conn)
        # Load dim_subscription_plan
        subscription_df = pd.read_sql_table("dim_subscription_plan", conn)

    logger.info(f"[load_user_activity_and_subscription_dfs] Loaded {len(activity_df)} activity rows and {len(subscription_df)} subscription rows")

    # Merge to get base_price for each user activity row
    merged_df = pd.merge(
        activity_df,
        subscription_df[['subscription_plan_key', 'base_price']],
        left_on='subscription_plan_key',
        right_on='subscription_plan_key',
        how='left'
    )

    return merged_df

def save_snapshot_to_db(snapshot_df: pd.DataFrame, table_name: str = "fact_user_analytics_snapshot"):
    """
    Save the final user analytics snapshot DataFrame (with RFM/KMeans/CLV/churn) to the DB.

    Parameters:
    - snapshot_df: DataFrame with columns matching your snapshot table schema
    - table_name: Target table name (default = "fact_user_analytics_snapshot")
    """
    try:
        with engine.begin() as conn:
            snapshot_df.to_sql(table_name, con=conn, if_exists="append", index=False, method="multi")
        logger.info(f"Saved analytics snapshot to table: {table_name}")
    except Exception as e:
        logger.error(f"Error saving snapshot to database table {table_name}: {e}")

def ensure_snapshot_date(session: Session, snapshot_date_key: int):
    exists = session.query(DimDate).filter_by(date_key=snapshot_date_key).first()
    if not exists:
        dt = datetime.strptime(str(snapshot_date_key), "%Y%m%d")
        dim_date = DimDate(
            date_key=snapshot_date_key,
            full_date=dt.date(),
            year=dt.year,
            quarter=(dt.month - 1)//3 + 1,
            month=dt.month,
            month_name=dt.strftime("%B"),
            week_of_year=int(dt.strftime("%U")),
            day_of_month=dt.day,
            day_of_week=dt.isoweekday(),
            day_name=dt.strftime("%A"),
            is_weekend=dt.isoweekday() >= 6
        )
        session.add(dim_date)
        session.commit()
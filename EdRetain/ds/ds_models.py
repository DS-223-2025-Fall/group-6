# ds_models.py
"""
Data science models and ETL integration for customer analytics.
- RFM calculation
"""

sys.path.insert(0, str(Path(__file__).parent.parent / "etl"))

import pandas as pd
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path
from Database.database import engine
from helpers import load_user_activity_and_subscription_dfs, save_snapshot_to_db

def compute_basic_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute RFM metrics for users:
    - Recency: minimum days_since_last_login per user
    - Frequency: maximum active_days_last_30d per user
    - Monetary: maximum base_price per user

    Returns:
        DataFrame with user_key, Recency, Frequency, Monetary
    """
    rfm_df = df.groupby('user_key').agg(
        Recency=('days_since_last_login', 'min'),
        Frequency=('active_days_last_30d', 'max'),
        Monetary=('base_price', 'max')
    ).reset_index()
    logger.info(f"[compute_basic_rfm] Computed RFM for {len(rfm_df)} users")
    return rfm_df

def rfm_to_snapshot():
    """
    Executes RFM computation and saves the result as an analytics snapshot to the database.
    Can be scheduled/run independently or imported as a callable.
    """
    # Load user activity and subscription data
    merged_df = load_user_activity_and_subscription_dfs()

    # Compute RFM metrics
    rfm_df = compute_basic_rfm(merged_df)

    # Prepare snapshot table row
    snapshot_date_key = int(datetime.now().strftime("%Y%m%d"))
    rfm_snapshot = rfm_df.copy()
    rfm_snapshot['snapshot_date_key'] = snapshot_date_key

    # Assign Nones (will populate with additional model output when available)
    rfm_snapshot['subscription_plan_key'] = None
    rfm_snapshot['rfm_segment'] = None
    rfm_snapshot['kmeans_cluster'] = None
    rfm_snapshot['kmeans_segment_label'] = None
    rfm_snapshot['churn_probability'] = None
    rfm_snapshot['churn_risk_band'] = None
    rfm_snapshot['survival_median_time_to_downgrade'] = None
    rfm_snapshot['survival_risk_90d'] = None
    rfm_snapshot['clv_value'] = None

    rfm_snapshot = rfm_snapshot[[
        'user_key',
        'snapshot_date_key',
        'subscription_plan_key',
        'rfm_segment',
        'kmeans_cluster',
        'kmeans_segment_label',
        'churn_probability',
        'churn_risk_band',
        'survival_median_time_to_downgrade',
        'survival_risk_90d',
        'clv_value'
    ]]

    save_snapshot_to_db(rfm_snapshot)
    logger.info("[rfm_to_snapshot] RFM snapshot saved to database.")

if __name__ == "__main__":
    rfm_to_snapshot()

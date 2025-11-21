import pandas as pd
from datetime import datetime
from loguru import logger

from sqlalchemy.orm import Session
from Database.database import engine, SessionLocal
from Database.models import DimDate
from helpers import load_user_activity_and_subscription_dfs, save_snapshot_to_db, ensure_snapshot_date

def compute_basic_rfm(df: pd.DataFrame) -> pd.DataFrame:
    rfm_df = df.groupby('user_key').agg(
        rfm_recency=('days_since_last_login', 'min'),
        rfm_frequency=('active_days_last_30d', 'max'),
        rfm_monetary=('base_price', 'max')
    ).reset_index()
    logger.info(f"[compute_basic_rfm] Computed RFM for {len(rfm_df)} users")
    return rfm_df

def rfm_to_snapshot():
    merged_df = load_user_activity_and_subscription_dfs()
    rfm_df = compute_basic_rfm(merged_df)
    
    snapshot_date_key = int(datetime.now().strftime("%Y%m%d"))
    rfm_snapshot = rfm_df.copy()
    rfm_snapshot['snapshot_date_key'] = snapshot_date_key

    # Assign None to columns we're not computing yet
    rfm_snapshot['subscription_plan_key'] = None
    rfm_snapshot['rfm_r_score'] = None
    rfm_snapshot['rfm_f_score'] = None
    rfm_snapshot['rfm_m_score'] = None
    rfm_snapshot['rfm_segment'] = None
    rfm_snapshot['kmeans_cluster'] = None
    rfm_snapshot['segment_label'] = None             
    rfm_snapshot['churn_probability'] = None
    rfm_snapshot['churn_risk_band'] = None
    rfm_snapshot['survival_median_time_to_downgrade'] = None
    rfm_snapshot['survival_risk_90d'] = None
    rfm_snapshot['clv_value'] = None
    rfm_snapshot['clv_band'] = None                  
    rfm_snapshot['model_version'] = 'v1.0'            

    rfm_snapshot = rfm_snapshot[[
        'user_key',
        'snapshot_date_key',
        'subscription_plan_key',
        'rfm_recency',
        'rfm_frequency',
        'rfm_monetary',
        'rfm_r_score',
        'rfm_f_score',
        'rfm_m_score',
        'rfm_segment',
        'kmeans_cluster',
        'segment_label',
        'churn_probability',
        'churn_risk_band',
        'survival_median_time_to_downgrade',
        'survival_risk_90d',
        'clv_value',
        'clv_band',
        'model_version'
    ]]

    # Ensure dim_date entry exists
    with SessionLocal() as session:
        ensure_snapshot_date(session, snapshot_date_key)

    save_snapshot_to_db(rfm_snapshot)
    logger.info("[rfm_to_snapshot] RFM snapshot saved to database.")

if __name__ == "__main__":
    rfm_to_snapshot()

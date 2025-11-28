import pandas as pd
from sqlalchemy import text
from Database.database import engine
from loguru import logger
from sqlalchemy.orm import Session
from Database.models import DimDate
from datetime import datetime

<<<<<<< HEAD

def load_user_activity_and_subscription_dfs():
    """
    Load fact_user_daily_activity and dim_subscription_plan tables into pandas DataFrames.
    Merge to get subscription pricing information.
=======
def load_user_activity_and_subscription_dfs():
    """
    Load fact_user_daily_activity and dim_subscription_plan tables into pandas DataFrames.
    Merge on subscription_plan_key to get base_price for monetary calculation.
    Returns merged DataFrame with necessary columns.
>>>>>>> main
    """
    with engine.connect() as conn:
        # Load fact_user_daily_activity
        activity_df = pd.read_sql_table("fact_user_daily_activity", conn)
        # Load dim_subscription_plan
        subscription_df = pd.read_sql_table("dim_subscription_plan", conn)

    logger.info(f"[load_user_activity_and_subscription_dfs] Loaded {len(activity_df)} activity rows and {len(subscription_df)} subscription rows")

<<<<<<< HEAD
    # Merge to get base_price and billing_cycle for each activity record
    merged_df = pd.merge(
        activity_df,
        subscription_df[['subscription_plan_key', 'base_price', 'billing_cycle']],
        on='subscription_plan_key',
=======
    # Merge to get base_price for each user activity row
    merged_df = pd.merge(
        activity_df,
        subscription_df[['subscription_plan_key', 'base_price']],
        left_on='subscription_plan_key',
        right_on='subscription_plan_key',
>>>>>>> main
        how='left'
    )

    return merged_df

<<<<<<< HEAD

def calculate_total_lifetime_revenue(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total lifetime monetary value for each user based on unique billing periods
    within the 3-month observation window.
    
    Billing cycles supported:
    - Monthly: Count unique months (max 3 in a 3-month period)
    - Yearly: Count unique years (max 1 in a 3-month period)
    
    Includes ALL premium users (active and cancelled) to capture full revenue history.
    """
    # Filter only premium subscriptions (base_price > 0)
    premium_df = merged_df[merged_df['base_price'] > 0].copy()
    
    logger.info(f"[calculate_total_lifetime_revenue] Processing {len(premium_df)} premium activity records")
    
    # Convert date_key (YYYYMMDD) to datetime
    premium_df['date'] = pd.to_datetime(premium_df['date_key'], format='%Y%m%d')
    premium_df['year'] = premium_df['date'].dt.year
    premium_df['year_month'] = premium_df['date'].dt.to_period('M')  # Format: 2025-09
    
    revenue_records = []
    
    # Group by user and subscription plan
    for (user_key, plan_key), group in premium_df.groupby(['user_key', 'subscription_plan_key']):
        base_price = group['base_price'].iloc[0]
        billing_cycle = str(group['billing_cycle'].iloc[0]).lower()
        
        # Count unique billing periods based on cycle type
        if 'month' in billing_cycle:
            # Count unique months (e.g., Sep, Oct, Nov = 3 periods)
            unique_periods = group['year_month'].nunique()
        elif 'year' in billing_cycle or 'annual' in billing_cycle:
            # Count unique years (will be 1 in a 3-month window)
            unique_periods = group['year'].nunique()
        else:
            # Default to monthly if billing_cycle is unexpected
            logger.warning(f"Unknown billing_cycle '{billing_cycle}' for plan_key {plan_key}, defaulting to monthly")
            unique_periods = group['year_month'].nunique()
        
        # Total revenue = number of billing periods × base price
        total_revenue = unique_periods * base_price
        
        revenue_records.append({
            'user_key': user_key,
            'subscription_plan_key': plan_key,
            'billing_cycles_paid': unique_periods,
            'base_price': base_price,
            'billing_cycle': billing_cycle,
            'revenue_from_plan': total_revenue
        })
    
    # Create DataFrame from records
    plan_revenue_df = pd.DataFrame(revenue_records)
    
    # Log some examples for verification
    logger.info(f"[calculate_total_lifetime_revenue] Sample billing calculations:")
    if len(plan_revenue_df) > 0:
        for idx, row in plan_revenue_df.head(5).iterrows():
            logger.info(f"  User {row['user_key']}: {row['billing_cycles_paid']} {row['billing_cycle']} "
                       f"periods × ${row['base_price']:.2f} = ${row['revenue_from_plan']:.2f}")
    
    # Sum revenue across all plans for each user (handles plan switches)
    revenue_df = plan_revenue_df.groupby('user_key').agg(
        total_lifetime_revenue=('revenue_from_plan', 'sum'),
        total_billing_cycles=('billing_cycles_paid', 'sum')
    ).reset_index()
    
    logger.info(f"[calculate_total_lifetime_revenue] Calculated lifetime revenue for {len(revenue_df)} users")
    logger.info(f"Average revenue (3-month period): ${revenue_df['total_lifetime_revenue'].mean():.2f}")
    logger.info(f"Median revenue: ${revenue_df['total_lifetime_revenue'].median():.2f}")
    logger.info(f"Average billing cycles paid: {revenue_df['total_billing_cycles'].mean():.1f}")
    logger.info(f"Revenue range: ${revenue_df['total_lifetime_revenue'].min():.2f} - ${revenue_df['total_lifetime_revenue'].max():.2f}")
    
    return revenue_df


def save_snapshot_to_db(snapshot_df: pd.DataFrame, table_name: str = "fact_user_analytics_snapshot"):
    """
    Save the final user analytics snapshot DataFrame to the database.
=======
def save_snapshot_to_db(snapshot_df: pd.DataFrame, table_name: str = "fact_user_analytics_snapshot"):
    """
    Save the final user analytics snapshot DataFrame (with RFM/KMeans/CLV/churn) to the DB.

    Parameters:
    - snapshot_df: DataFrame with columns matching your snapshot table schema
    - table_name: Target table name (default = "fact_user_analytics_snapshot")
>>>>>>> main
    """
    try:
        with engine.begin() as conn:
            snapshot_df.to_sql(table_name, con=conn, if_exists="append", index=False, method="multi")
        logger.info(f"Saved analytics snapshot to table: {table_name}")
    except Exception as e:
        logger.error(f"Error saving snapshot to database table {table_name}: {e}")

<<<<<<< HEAD
def save_dashboard_metrics_to_db(metrics_dict: dict):
    """
    Save dashboard KPIs to database.
    
    Args:
        metrics_dict: Dictionary containing all dashboard metrics
    """
    import pandas as pd
    from datetime import datetime
    
    # Convert to DataFrame
    metrics_df = pd.DataFrame([metrics_dict])
    
    # Add timestamp
    metrics_df['created_at'] = datetime.now()
    
    try:
        with engine.begin() as conn:
            metrics_df.to_sql(
                'dashboard_metrics', 
                con=conn, 
                if_exists='append', 
                index=False, 
                method='multi'
            )
        logger.info(f"Dashboard metrics saved to database for snapshot {metrics_dict['snapshot_date_key']}")
        
    except Exception as e:
        logger.error(f"Error saving dashboard metrics to database: {e}")
        raise

=======
>>>>>>> main
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
<<<<<<< HEAD
        session.commit()
=======
        session.commit()
>>>>>>> main

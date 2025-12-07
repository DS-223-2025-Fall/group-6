from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, DATE
from loguru import logger
from datetime import datetime, timezone
from Database.database import Base, engine

Base = declarative_base()

class DimUser(Base):
    """Dimension table for user-related attributes.

    Stores one row per user with stable information such as demographics,
    signup date, country/city, user type, and current subscription status.
    """
    __tablename__ = "dim_user"

    user_key = Column(Integer, primary_key=True, autoincrement=True)
    user_id_nk = Column(String)
    signup_date_key = Column(Integer)
    birth_date = Column(DateTime)
    gender = Column(String)
    country = Column(String)
    city = Column(String)
    user_type = Column(String)
    acquisition_channel = Column(String)
    initial_plan_key = Column(Integer, ForeignKey("dim_subscription_plan.subscription_plan_key"))
    is_premium_ever = Column(Boolean)
    current_status = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class DimDate(Base):
    """Date dimension.

    Stores one row per calendar date with fields such as year, quarter,
    month, weekday, and weekend flag to support time-based analysis.
    """
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)
    full_date = Column(Date)
    year = Column(Integer)
    quarter = Column(Integer)
    month = Column(Integer)
    month_name = Column(String)
    week_of_year = Column(Integer)
    day_of_month = Column(Integer)
    day_of_week = Column(Integer)
    day_name = Column(String)
    is_weekend = Column(Boolean)

class DimSubscriptionPlan(Base):
    """Subscription plan dimension.

    Describes each subscription plan and tier, including billing cycle,
    base price, currency and plan features (certificate, mentoring, downloads).
    """
    __tablename__ = "dim_subscription_plan"

    subscription_plan_key = Column(Integer, primary_key=True, autoincrement=True)
    plan_id_nk = Column(String)
    plan_name = Column(String)
    tier = Column(String)
    billing_cycle = Column(String)
    base_price = Column(Float)
    currency = Column(String)
    has_certificate = Column(Boolean)
    has_mentoring = Column(Boolean)
    has_downloads = Column(Boolean)

class DimCampaign(Base):
    """Campaign dimension.

    Contains core information about marketing campaigns, such as type,
    target segment, default channel, and start/end dates.
    """
    __tablename__ = "dim_campaign"
    campaign_key = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id_nk = Column(String)
    campaign_name = Column(String)
    campaign_type = Column(String)
    target_risk_segment = Column(String)
    offer_type = Column(String)
    default_channel = Column(String)
    start_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    end_date_key = Column(Integer, ForeignKey("dim_date.date_key"))

class DimChannel(Base):
    """Channel dimension.

    Lists the communication channels (for example email, in-app, SMS)
    used to deliver campaigns and messages to users.
    """
    __tablename__ = "dim_channel"
    channel_key = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String)
    description = Column(String)

class FactUserDailyActivity(Base):
    """Fact table for daily user engagement.

    Stores one row per user per day with metrics such as logins, sessions,
    minutes watched, course activity, and inactivity indicators.
    """
    __tablename__ = "fact_user_daily_activity"
    fact_user_daily_activity_id = Column(Integer, primary_key=True, autoincrement=True)
    user_key = Column(Integer, ForeignKey("dim_user.user_key"))
    date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    subscription_plan_key = Column(Integer, ForeignKey("dim_subscription_plan.subscription_plan_key"))
    campaign_key = Column(Integer, ForeignKey("dim_campaign.campaign_key"))
    is_premium = Column(Boolean)
    has_active_subscription = Column(Boolean)
    logins_count = Column(Integer)
    sessions_count = Column(Integer)
    minutes_watched = Column(Integer)
    lessons_completed = Column(Integer)
    quizzes_attempted = Column(Integer)
    distinct_courses_accessed = Column(Integer)
    active_days_last_30d = Column(Integer)
    days_since_last_login = Column(Integer)
    is_inactive_7d_flag = Column(Boolean)
    active_courses_count = Column(Integer)
    completed_courses_total = Column(Integer)
    created_at = Column(DateTime)

class FactCampaignInteraction(Base):
    """Fact table for campaign interactions.

    Tracks how each user interacted with a campaign on a given date,
    including sent, opened, clicked and converted flags.
    """
    __tablename__ = "fact_campaign_interaction"
    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_key = Column(Integer, ForeignKey("dim_user.user_key"))
    campaign_key = Column(Integer, ForeignKey("dim_campaign.campaign_key"))
    date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    channel_key = Column(Integer, ForeignKey("dim_channel.channel_key"))
    sent_flag = Column(Boolean)
    opened_flag = Column(Boolean)
    clicked_flag = Column(Boolean)
    converted_flag = Column(Boolean)
    time_to_conversion_days = Column(Integer)
    created_at = Column(DateTime)

class FactUserAnalyticsSnapshot(Base):
    """Fact table for user analytics snapshots.

    Stores model-based metrics for each user at a snapshot date,
    including RFM scores, clusters, churn risk, survival metrics and CLV.
    """
    __tablename__ = "fact_user_analytics_snapshot"
    fact_user_analytics_snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    user_key = Column(Integer, ForeignKey("dim_user.user_key"))
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    subscription_plan_key = Column(Integer, ForeignKey("dim_subscription_plan.subscription_plan_key"))
    
    # RFM
    rfm_recency = Column(Integer)
    rfm_frequency = Column(Integer)
    rfm_monetary = Column(Float)
    rfm_r_score = Column(Integer)
    rfm_f_score = Column(Integer)
    rfm_m_score = Column(Integer)
    rfm_segment = Column(String)
    segment_label = Column(String)
    
    engagement_level = Column(String)

    # Clustering
    kmeans_cluster = Column(Integer)
    kmeans_segment_label = Column(String)

    # Churn Prediction
    churn_probability = Column(Float)
    churn_risk_band = Column(String)

    # Survival Analysis
    survival_median_time_to_downgrade = Column(Integer)
    survival_risk_90d = Column(Float)

    # CLV
    clv_value = Column(Float)
    clv_band = Column(String)

    # Metadata
    model_version = Column(String)


class FeatureImportance(Base):
    """Feature importance scores for models.

    Keeps importance score and rank for each feature, per model type
    and model version, to support explainability and dashboards.
    """
    __tablename__ = "feature_importance"
    
    feature_importance_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    model_type = Column(String)  # 'churn_prediction', 'retention_model', 'clv_model'
    model_version = Column(String)  # 'v1.0', 'v1.1', etc.
    
    # Feature details
    feature_name = Column(String)  # 'Support Tickets', 'Feature Usage', 'Time on Platform', 'Login Frequency', 'Course Completion Rate', 'Payment Issues'
    importance_score = Column(Float)  # Relative importance (0-100 or 0-1)
    importance_rank = Column(Integer)  # 1, 2, 3, 4... for ordering
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class DashboardMetrics(Base):
    """Aggregated dashboard metrics.

    Stores precomputed key performance indicators and engagement
    segment counts for each snapshot date used in dashboards.
    """
    __tablename__ = "dashboard_metrics"
    
    dashboard_metrics_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    
    # === Core KPI Metrics ===
    active_premium_learners = Column(Integer)  # Count of users with recency <= 7 days
    at_risk_learners = Column(Integer)  # Count of High-Value at Risk + Declining + Dormant
    average_retention_rate = Column(Float)  # Overall retention percentage
    total_premium_learners = Column(Integer)  # Total premium users
    churned_learners = Column(Integer)  # Recently Churned segment count
    new_premium_learners = Column(Integer)  # New Premium Users segment count
    
    # === Change Indicators (from previous period) ===
    active_premium_change_pct = Column(Float, nullable=True)  # e.g., +12.0
    at_risk_change_count = Column(Integer, nullable=True)  # e.g., +8
    retention_rate_change_pct = Column(Float, nullable=True)  # e.g., -2.2
    
    # === Monthly Trends (for line chart) ===
    monthly_retention_rate = Column(Float)  # Retention % for this month
    monthly_churn_rate = Column(Float)  # Churn % for this month
    
    # === Engagement Segmentation (for donut chart) ===
    highly_engaged_count = Column(Integer)
    highly_engaged_pct = Column(Float)  # e.g., 45.0
    medium_engaged_count = Column(Integer)
    medium_engaged_pct = Column(Float)  # e.g., 30.0
    at_risk_count = Column(Integer)
    at_risk_pct = Column(Float)  # e.g., 10.0
    dormant_count = Column(Integer)
    dormant_pct = Column(Float)  # e.g., 15.0
    
    # === Metadata ===
    created_at = Column(DateTime, default=datetime.utcnow)


class ChurnReasons(Base):
    """Aggregated churn reasons.

    Summarises the main reasons behind churn or high churn risk,
    with counts, percentages, average churn probability and severity.
    """
    __tablename__ = "churn_reasons"
    
    churn_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    
    # Churn reason classification
    reason_category = Column(String)  # 'Inactivity', 'Course Dropped', 'Payment Delay', 'Support Issues', 'Low Engagement', 'Content Dissatisfaction'
    reason_display_name = Column(String)  # User-friendly name for dashboard
    reason_count = Column(Integer)  # Number of at-risk users with this primary reason
    reason_pct = Column(Float)  # Percentage of total at-risk users
    
    # Additional context
    avg_churn_probability = Column(Float, nullable=True)  # Average churn risk for users with this reason
    severity_level = Column(String, nullable=True)  # 'High', 'Medium', 'Low'
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class CampaignPerformance(Base):
    """Campaign performance metrics.

    Stores retention and uplift results for campaigns, including
    open rate, retention lift and campaign/control group sizes.
    """
    __tablename__ = "campaign_performance"
    
    campaign_performance_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    campaign_key = Column(Integer, ForeignKey("dim_campaign.campaign_key"))
    
    campaign_name = Column(String)
    target_segment = Column(String)
    launch_date = Column(Integer, nullable=True)  
    
    users_sent = Column(Integer)
    users_opened = Column(Integer)
    open_rate = Column(Float)  
    
    campaign_retention_rate = Column(Float)  
    control_retention_rate = Column(Float)   
    retention_lift = Column(Float)           
    
    campaign_size = Column(Integer, nullable=True)    
    control_size = Column(Integer, nullable=True)   
    
    status = Column(String)  
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ModelPerformanceMetrics(Base):
    """Model performance metrics.

    Records evaluation results for each model type and version,
    including accuracy, precision, recall, F1, AUC and confusion matrix.
    """
    __tablename__ = "model_performance_metrics"

    model_performance_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))

    # Model identification
    model_type = Column(String)
    model_version = Column(String)

    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)

    # Sample sizes
    train_samples = Column(Integer)
    test_samples = Column(Integer)

    # Confusion matrix values
    true_negatives = Column(Integer, nullable=True)
    false_positives = Column(Integer, nullable=True)
    false_negatives = Column(Integer, nullable=True)
    true_positives = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
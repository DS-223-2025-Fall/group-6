"""SQLAlchemy ORM models for the EdRetain analytical data warehouse.

This module defines dimension and fact tables used for user activity tracking,
marketing campaigns, churn and survival analysis, CLV estimation, and model
monitoring.
"""

from loguru import logger
from sqlalchemy import Boolean, Date, create_engine, Column, Integer, String, Float, DATE, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone 
from Database.database import Base, engine


class DimUser(Base):
    """Dimension table that stores core learner attributes.

    Captures stable user information such as external user ID, demographic
    details, location, acquisition channel, subscription history and current
    status. Linked to activity and analytics fact tables via `user_key`.
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
    """Date dimension used for all time-based analysis.

    Provides a surrogate `date_key` and decomposed calendar attributes such
    as year, quarter, month, weekday and weekend flags to support reporting
    and aggregations.
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

    Describes the characteristics of a subscription plan: name, tier,
    billing cycle, base price, currency and included benefits. Referenced
    by fact tables whenever a learner has or had a plan.
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
    """Marketing campaign dimension.

    Holds metadata for outbound campaigns, including type, targeted risk
    segment, offer, default channel and start/end dates. Used by campaign
    interaction and performance fact tables.
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
    """Channel dimension describing communication or acquisition channels."""
    __tablename__ = "dim_channel"
    channel_key = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String)
    description = Column(String)


class FactUserDailyActivity(Base):
    """Fact table capturing daily behavioural metrics per user.

    Stores login, session, content consumption and course progress metrics
    for each (user, date, subscription, campaign) combination. Used as the
    base for RFM, churn and engagement modelling.
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
    """Fact table for user-level campaign interactions.

    Records whether a campaign was sent, opened, clicked and converted,
    along with time-to-conversion where applicable, per user and channel.
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
    """Aggregated user analytics snapshot fact table.

    Contains derived features for each user on a specific snapshot date,
    including RFM scores, clustering labels, churn probability, survival
    estimates and CLV values. Used to drive dashboards and retention
    decision-making.
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
    """Stores feature importance values for trained models.

    Logs per-feature importance, rank and model metadata for a given
    snapshot date, enabling auditability and interpretability of ML
    models used in production.
    """
    __tablename__ = "feature_importance"
    
    feature_importance_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    model_type = Column(String)
    model_version = Column(String)
    
    feature_name = Column(String)
    importance_score = Column(Float)
    importance_rank = Column(Integer)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DashboardMetrics(Base):
    """Pre-calculated aggregate metrics for the executive dashboard.

    Stores high-level KPIs such as active premium learners, at-risk
    learners, retention, churn and engagement distributions for each
    snapshot date.
    """
    __tablename__ = "dashboard_metrics"
    
    dashboard_metrics_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    active_premium_learners = Column(Integer)
    at_risk_learners = Column(Integer)
    average_retention_rate = Column(Float)
    total_premium_learners = Column(Integer)
    churned_learners = Column(Integer)
    new_premium_learners = Column(Integer)
    active_premium_change_pct = Column(Float, nullable=True)
    at_risk_change_count = Column(Integer, nullable=True)
    retention_rate_change_pct = Column(Float, nullable=True)
    monthly_retention_rate = Column(Float)
    monthly_churn_rate = Column(Float)
    highly_engaged_count = Column(Integer)
    highly_engaged_pct = Column(Float)
    medium_engaged_count = Column(Integer)
    medium_engaged_pct = Column(Float)
    at_risk_count = Column(Integer)
    at_risk_pct = Column(Float)
    dormant_count = Column(Integer)
    dormant_pct = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChurnReasons(Base):
    """Aggregated reasons for churn or downgrade.

    Groups churn feedback into categories with counts, percentages and
    severity, supporting qualitative interpretation of churn patterns.
    """
    __tablename__ = "churn_reasons"
    
    churn_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    
    reason_category = Column(String)
    reason_display_name = Column(String)
    reason_count = Column(Integer)
    reason_pct = Column(Float)
    
    avg_churn_probability = Column(Float, nullable=True)
    severity_level = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CampaignPerformance(Base):
    """Summarised performance metrics for marketing campaigns.

    Contains retention and churn outcomes for treatment vs control groups,
    together with basic engagement rates (opens, clicks) for each campaign
    snapshot.
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

    campaign_churn_rate = Column(Float, nullable=True)  
    control_churn_rate = Column(Float, nullable=True)    
    
    campaign_size = Column(Integer, nullable=True)    
    control_size = Column(Integer, nullable=True)   
    
    status = Column(String)  
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ModelPerformanceMetrics(Base):
    """Tracks evaluation metrics for predictive models over time.

    Stores accuracy, precision, recall, F1, AUC and confusion-matrix
    components for a given model type and version at a specific snapshot
    date, together with train/test sample sizes.
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

# Base.metadata.create_all(engine)

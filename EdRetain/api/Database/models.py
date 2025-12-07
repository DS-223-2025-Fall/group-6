"""
Database models for the learner retention analytics platform.

This module defines the SQLAlchemy ORM models for the dimensional and fact
tables used in the ETL pipeline, analytics snapshots, dashboards, and
campaign performance tracking.

Modules:
    - sqlalchemy: For ORM mapping and database schema definition.
    - pydantic: For data validation in other layers of the application.
    - datetime: For timestamp and date fields in the models.
"""

from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, DATE
from loguru import logger
from datetime import datetime, timezone
from Database.database import Base, engine

Base = declarative_base()

class DimUser(Base):
    """
    Represents a learner in the database.

    Attributes:
        user_key (int): The unique identifier for the user (auto-incremented).
        user_id_nk (str): The natural key from the source system.
        signup_date_key (int): Foreign key to the date dimension for signup date.
        birth_date (datetime): The user's date of birth.
        gender (str): The user's gender.
        country (str): The user's country of residence.
        city (str): The user's city of residence.
        user_type (str): The type of user (e.g., student, educator).
        acquisition_channel (str): The channel through which the user was acquired.
        initial_plan_key (int): Foreign key to the subscription plan at signup.
        is_premium_ever (bool): Flag indicating if the user has ever had a premium subscription.
        current_status (str): The current status of the user account.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
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
    """
    Represents a calendar date in the database.

    Attributes:
        date_key (int): The unique identifier for the date (surrogate key).
        full_date (date): The actual calendar date.
        year (int): The year component of the date.
        quarter (int): The quarter of the year (1-4).
        month (int): The month of the year (1-12).
        month_name (str): The name of the month.
        week_of_year (int): The week number within the year.
        day_of_month (int): The day of the month (1-31).
        day_of_week (int): The day of the week (0-6, where 0 is Monday).
        day_name (str): The name of the day (e.g., Monday, Tuesday).
        is_weekend (bool): Flag indicating if the date falls on a weekend.
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
    """
    Represents a subscription plan in the database.

    Attributes:
        subscription_plan_key (int): The unique identifier for the plan (auto-incremented).
        plan_id_nk (str): The natural key from the source system.
        plan_name (str): The name of the subscription plan.
        tier (str): The tier level of the plan (e.g., Free, Basic, Premium).
        billing_cycle (str): The billing cycle (e.g., monthly, annual).
        base_price (float): The base price of the plan.
        currency (str): The currency for the plan price.
        has_certificate (bool): Flag indicating if the plan includes certificates.
        has_mentoring (bool): Flag indicating if the plan includes mentoring.
        has_downloads (bool): Flag indicating if the plan allows content downloads.
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
    """
    Represents a marketing or retention campaign in the database.

    Attributes:
        campaign_key (int): The unique identifier for the campaign (auto-incremented).
        campaign_id_nk (str): The natural key from the source system.
        campaign_name (str): The name of the campaign.
        campaign_type (str): The type of campaign (e.g., retention, acquisition).
        target_risk_segment (str): The target risk segment for the campaign.
        offer_type (str): The type of offer (e.g., discount, free trial).
        default_channel (str): The default communication channel for the campaign.
        start_date_key (int): Foreign key to the date dimension for campaign start.
        end_date_key (int): Foreign key to the date dimension for campaign end.
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
    """
    Represents a communication channel in the database.

    Attributes:
        channel_key (int): The unique identifier for the channel (auto-incremented).
        channel_name (str): The name of the channel (e.g., email, SMS, in-app).
        description (str): A description of the channel.
    """
    __tablename__ = "dim_channel"
    channel_key = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String)
    description = Column(String)

class FactUserDailyActivity(Base):
    """
    Represents daily learner activity in the database.

    Attributes:
        fact_user_daily_activity_id (int): The unique identifier for the record (auto-incremented).
        user_key (int): Foreign key to the user dimension.
        date_key (int): Foreign key to the date dimension.
        subscription_plan_key (int): Foreign key to the subscription plan dimension.
        campaign_key (int): Foreign key to the campaign dimension.
        is_premium (bool): Flag indicating if the user is premium on this date.
        has_active_subscription (bool): Flag indicating if the user has an active subscription.
        logins_count (int): Number of logins on this date.
        sessions_count (int): Number of sessions on this date.
        minutes_watched (int): Total minutes of content watched.
        lessons_completed (int): Number of lessons completed.
        quizzes_attempted (int): Number of quizzes attempted.
        distinct_courses_accessed (int): Number of distinct courses accessed.
        active_days_last_30d (int): Number of active days in the last 30 days.
        days_since_last_login (int): Number of days since the last login.
        is_inactive_7d_flag (bool): Flag indicating if the user has been inactive for 7+ days.
        active_courses_count (int): Number of currently active courses.
        completed_courses_total (int): Total number of courses completed to date.
        created_at (datetime): Timestamp when the record was created.
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
    """
    Represents campaign interaction events in the database.

    Attributes:
        interaction_id (int): The unique identifier for the interaction (auto-incremented).
        user_key (int): Foreign key to the user dimension.
        campaign_key (int): Foreign key to the campaign dimension.
        date_key (int): Foreign key to the date dimension.
        channel_key (int): Foreign key to the channel dimension.
        sent_flag (bool): Flag indicating if the campaign was sent to the user.
        opened_flag (bool): Flag indicating if the user opened the campaign.
        clicked_flag (bool): Flag indicating if the user clicked the campaign.
        converted_flag (bool): Flag indicating if the user converted.
        time_to_conversion_days (int): Number of days from send to conversion.
        created_at (datetime): Timestamp when the record was created.
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
    """
    Represents learner analytics snapshots in the database.

    Attributes:
        fact_user_analytics_snapshot_id (int): The unique identifier for the snapshot (auto-incremented).
        user_key (int): Foreign key to the user dimension.
        snapshot_date_key (int): Foreign key to the date dimension for the snapshot date.
        subscription_plan_key (int): Foreign key to the subscription plan dimension.
        rfm_recency (int): Recency value (days since last activity).
        rfm_frequency (int): Frequency value (number of activities).
        rfm_monetary (float): Monetary value (total spend or value).
        rfm_r_score (int): RFM recency score (1-5).
        rfm_f_score (int): RFM frequency score (1-5).
        rfm_m_score (int): RFM monetary score (1-5).
        rfm_segment (str): RFM segment classification.
        segment_label (str): Human-readable segment label.
        engagement_level (str): Overall engagement level.
        kmeans_cluster (int): K-means cluster assignment.
        kmeans_segment_label (str): K-means cluster label.
        churn_probability (float): Predicted churn probability (0-1).
        churn_risk_band (str): Churn risk classification band.
        survival_median_time_to_downgrade (int): Median days until downgrade from survival model.
        survival_risk_90d (float): 90-day survival risk score.
        clv_value (float): Customer lifetime value estimate.
        clv_band (str): CLV classification band.
        model_version (str): Version of the analytics model used.
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
    """
    Represents feature importance metrics for ML models in the database.

    Attributes:
        feature_importance_id (int): The unique identifier for the record (auto-incremented).
        snapshot_date_key (int): Foreign key to the date dimension for the snapshot date.
        model_type (str): The type of model (e.g., churn_prediction, clv_model).
        model_version (str): The version of the model (e.g., v1.0, v1.1).
        feature_name (str): The name of the feature.
        importance_score (float): The importance score of the feature (0-100 or 0-1).
        importance_rank (int): The rank of the feature by importance (1 is most important).
        created_at (datetime): Timestamp when the record was created.
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
    """
    Represents aggregated dashboard KPI metrics in the database.

    Attributes:
        dashboard_metrics_id (int): The unique identifier for the record (auto-incremented).
        snapshot_date_key (int): Foreign key to the date dimension for the snapshot date.
        active_premium_learners (int): Count of active premium learners.
        at_risk_learners (int): Count of at-risk learners.
        average_retention_rate (float): Overall retention rate percentage.
        total_premium_learners (int): Total count of premium learners.
        churned_learners (int): Count of recently churned learners.
        new_premium_learners (int): Count of new premium learners.
        active_premium_change_pct (float): Percentage change in active premium learners from previous period.
        at_risk_change_count (int): Change in at-risk learner count from previous period.
        retention_rate_change_pct (float): Percentage change in retention rate from previous period.
        monthly_retention_rate (float): Monthly retention rate percentage.
        monthly_churn_rate (float): Monthly churn rate percentage.
        highly_engaged_count (int): Count of highly engaged learners.
        highly_engaged_pct (float): Percentage of highly engaged learners.
        medium_engaged_count (int): Count of medium engaged learners.
        medium_engaged_pct (float): Percentage of medium engaged learners.
        at_risk_count (int): Count of at-risk learners in engagement segmentation.
        at_risk_pct (float): Percentage of at-risk learners.
        dormant_count (int): Count of dormant learners.
        dormant_pct (float): Percentage of dormant learners.
        created_at (datetime): Timestamp when the record was created.
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
    """
    Represents churn reason analysis in the database.

    Attributes:
        churn_reason_id (int): The unique identifier for the record (auto-incremented).
        snapshot_date_key (int): Foreign key to the date dimension for the snapshot date.
        reason_category (str): The category of churn reason.
        reason_display_name (str): User-friendly name for the churn reason.
        reason_count (int): Number of at-risk users with this primary reason.
        reason_pct (float): Percentage of total at-risk users with this reason.
        avg_churn_probability (float): Average churn probability for users with this reason.
        severity_level (str): Severity level of the churn reason (High, Medium, Low).
        created_at (datetime): Timestamp when the record was created.
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
    """
    Represents campaign performance metrics in the database.

    Attributes:
        campaign_performance_id (int): The unique identifier for the record (auto-incremented).
        snapshot_date_key (int): Foreign key to the date dimension for the snapshot date.
        campaign_key (int): Foreign key to the campaign dimension.
        campaign_name (str): The name of the campaign.
        target_segment (str): The target segment for the campaign.
        launch_date (int): The launch date key for the campaign.
        users_sent (int): Number of users who were sent the campaign.
        users_opened (int): Number of users who opened the campaign.
        open_rate (float): Campaign open rate percentage.
        campaign_retention_rate (float): Retention rate for the campaign group.
        control_retention_rate (float): Retention rate for the control group.
        retention_lift (float): Lift in retention rate (campaign vs control).
        campaign_size (int): Size of the campaign group.
        control_size (int): Size of the control group.
        status (str): Current status of the campaign.
        created_at (datetime): Timestamp when the record was created.
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
    """
    Represents machine learning model performance metrics in the database.

    Attributes:
        model_performance_id (int): The unique identifier for the record (auto-incremented).
        snapshot_date_key (int): Foreign key to the date dimension for the snapshot date.
        model_type (str): The type of model (e.g., churn_prediction, clv_model).
        model_version (str): The version of the model.
        accuracy (float): Model accuracy score.
        precision (float): Model precision score.
        recall (float): Model recall score.
        f1_score (float): Model F1 score.
        auc_roc (float): Model AUC-ROC score.
        train_samples (int): Number of training samples.
        test_samples (int): Number of test samples.
        true_negatives (int): Count of true negatives in confusion matrix.
        false_positives (int): Count of false positives in confusion matrix.
        false_negatives (int): Count of false negatives in confusion matrix.
        true_positives (int): Count of true positives in confusion matrix.
        created_at (datetime): Timestamp when the record was created.
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
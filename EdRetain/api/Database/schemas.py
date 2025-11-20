from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel

# --- DIM USER ---
class DimUserBase(BaseModel):
    user_id_nk: str
    signup_date_key: int
    birth_date: Optional[datetime]
    gender: Optional[str]
    country: Optional[str]
    city: Optional[str]
    user_type: Optional[str]
    acquisition_channel: Optional[str]
    initial_plan_key: Optional[int]
    is_premium_ever: Optional[bool]
    current_status: Optional[str]

class DimUserCreate(DimUserBase):
    pass

class DimUserSchema(DimUserBase):
    user_key: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True

# --- DIM DATE ---
class DimDateBase(BaseModel):
    date_key: int
    full_date: date
    year: int
    quarter: int
    month: int
    month_name: str
    week_of_year: int
    day_of_month: int
    day_of_week: int
    day_name: str
    is_weekend: Optional[bool]

class DimDateCreate(DimDateBase):
    pass

class DimDateSchema(DimDateBase):
    class Config:
        orm_mode = True

# --- DIM SUBSCRIPTION PLAN ---
class DimSubscriptionPlanBase(BaseModel):
    plan_id_nk: str
    plan_name: str
    tier: str
    billing_cycle: str
    base_price: float
    currency: str
    has_certificate: Optional[bool]
    has_mentoring: Optional[bool]
    has_downloads: Optional[bool]

class DimSubscriptionPlanCreate(DimSubscriptionPlanBase):
    pass

class DimSubscriptionPlanSchema(DimSubscriptionPlanBase):
    subscription_plan_key: int
    class Config:
        orm_mode = True

# --- DIM CAMPAIGN ---
class DimCampaignBase(BaseModel):
    campaign_id_nk: str
    campaign_name: str
    campaign_type: Optional[str]
    target_risk_segment: Optional[str]
    offer_type: Optional[str]
    default_channel: Optional[str]
    start_date_key: Optional[int]
    end_date_key: Optional[int]

class DimCampaignCreate(DimCampaignBase):
    pass

class DimCampaignSchema(DimCampaignBase):
    campaign_key: int
    class Config:
        orm_mode = True

# --- DIM CHANNEL ---
class DimChannelBase(BaseModel):
    channel_name: str
    description: Optional[str]

class DimChannelCreate(DimChannelBase):
    pass

class DimChannelSchema(DimChannelBase):
    channel_key: int
    class Config:
        orm_mode = True

# --- FACT USER DAILY ACTIVITY ---
class FactUserDailyActivityBase(BaseModel):
    user_key: int
    date_key: int
    subscription_plan_key: int
    campaign_key: Optional[int]
    is_premium: Optional[bool]
    has_active_subscription: Optional[bool]
    logins_count: Optional[int]
    sessions_count: Optional[int]
    minutes_watched: Optional[int]
    lessons_completed: Optional[int]
    quizzes_attempted: Optional[int]
    distinct_courses_accessed: Optional[int]
    active_days_last_30d: Optional[int]
    days_since_last_login: Optional[int]
    is_inactive_7d_flag: Optional[bool]
    active_courses_count: Optional[int]
    completed_courses_total: Optional[int]

class FactUserDailyActivityCreate(FactUserDailyActivityBase):
    pass

class FactUserDailyActivitySchema(FactUserDailyActivityBase):
    fact_user_daily_activity_id: int
    created_at: Optional[datetime]
    class Config:
        orm_mode = True

# --- FACT CAMPAIGN INTERACTION ---
class FactCampaignInteractionBase(BaseModel):
    user_key: int
    campaign_key: int
    date_key: int
    channel_key: int
    sent_flag: Optional[bool]
    opened_flag: Optional[bool]
    clicked_flag: Optional[bool]
    converted_flag: Optional[bool]
    time_to_conversion_days: Optional[int]

class FactCampaignInteractionCreate(FactCampaignInteractionBase):
    pass

class FactCampaignInteractionSchema(FactCampaignInteractionBase):
    interaction_id: int
    created_at: Optional[datetime]
    class Config:
        orm_mode = True

# --- FACT USER ANALYTICS SNAPSHOT ---
class FactUserAnalyticsSnapshotBase(BaseModel):
    user_key: int
    snapshot_date_key: int
    subscription_plan_key: int
    rfm_recency: Optional[int]
    rfm_frequency: Optional[int]
    rfm_monetary: Optional[float]
    rfm_r_score: Optional[int]
    rfm_f_score: Optional[int]
    rfm_m_score: Optional[int]
    rfm_segment: Optional[str]
    kmeans_cluster: Optional[int]
    segment_label: Optional[str]
    churn_probability: Optional[float]
    churn_risk_band: Optional[str]
    survival_median_time_to_downgrade: Optional[int]
    survival_risk_90d: Optional[float]
    clv_value: Optional[float]
    clv_band: Optional[str]
    model_version: Optional[str]

class FactUserAnalyticsSnapshotCreate(FactUserAnalyticsSnapshotBase):
    pass

class FactUserAnalyticsSnapshotSchema(FactUserAnalyticsSnapshotBase):
    fact_user_analytics_snapshot_id: int
    class Config:
        orm_mode = True

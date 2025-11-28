from fastapi import FastAPI, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from Database.database import get_db
from sqlalchemy import func, desc
import random
from typing import List, Dict, Optional


from Database.models import (
    DimUser, DimDate, DimSubscriptionPlan, DimCampaign, DimChannel,
    FactUserDailyActivity, FactCampaignInteraction, FactUserAnalyticsSnapshot,
    FeatureImportance, DashboardMetrics, ChurnReasons, CampaignPerformance,
    ModelPerformanceMetrics
)
from Database.schemas import (
    DimUserCreate, DimUserSchema,
    DimDateCreate, DimDateSchema,
    DimSubscriptionPlanCreate, DimSubscriptionPlanSchema,
    DimCampaignCreate, DimCampaignSchema,
    DimChannelCreate, DimChannelSchema,
    FactUserDailyActivityCreate, FactUserDailyActivitySchema,
    FactCampaignInteractionCreate, FactCampaignInteractionSchema,
    FactUserAnalyticsSnapshotCreate, FactUserAnalyticsSnapshotSchema,
    FeatureImportanceCreate, FeatureImportanceSchema,
    DashboardMetricsCreate, DashboardMetricsSchema,
    ChurnReasonsCreate, ChurnReasonsSchema, CampaignPerformanceCreate,
    CampaignPerformanceSchema, ModelPerformanceMetricsCreate,
    ModelPerformanceMetricsSchema
)

app = FastAPI(title="Project API")


# Page 1
class DateRange:
    """Simple value object to carry a date range around the app.

    Attributes:
        date_from: Start date (inclusive) as a datetime.date.
        date_to:   End date (inclusive) as a datetime.date.
    """
    def __init__(self, date_from: date, date_to: date):
        self.date_from = date_from
        self.date_to = date_to

def get_date_range(
    date_from: date = Query(..., description="Start date (inclusive) in YYYY-MM-DD"),
    date_to: date = Query(..., description="End date (inclusive) in YYYY-MM-DD"),
) -> DateRange:
    """Dependency that parses date_from/date_to query params and
    returns a DateRange object used by dashboard endpoints."""
    return DateRange(date_from=date_from, date_to=date_to)

def get_date_keys_in_range(db: Session, date_range: DateRange):
    """Return a subquery of DimDate.date_key values for the given
    calendar date range. Used to limit DashboardMetrics rows to
    the selected period."""
    return (
        db.query(DimDate.date_key)
        .filter(
            DimDate.full_date >= date_range.date_from,
            DimDate.full_date <= date_range.date_to,
        )
        .subquery()
    )


# Active premium leaners
@app.get("/dashboard/active-premium-learners")
def get_active_premium_learners(
    date_range: DateRange = Depends(get_date_range),
    db: Session = Depends(get_db),
):
    """
    Card: Active Premium Learners.

    For the selected period (date_from/date_to), finds the most recent
    DashboardMetrics row and returns:
      - active_premium_learners: current count of active premium users.
      - active_premium_change_pct: % change vs previous period (precomputed in DB).
    """
    date_keys_subq = get_date_keys_in_range(db, date_range)

    latest_row = (
        db.query(DashboardMetrics)
        .filter(DashboardMetrics.snapshot_date_key.in_(date_keys_subq))
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics for given period")

    return {
        "active_premium_learners": latest_row.active_premium_learners,
        "active_premium_change_pct": latest_row.active_premium_change_pct,
    }


# At risk learners 
@app.get("/dashboard/at-risk-learners")
def get_at_risk_learners(
    date_range: DateRange = Depends(get_date_range),
    db: Session = Depends(get_db),
):
    """
    Card: At-Risk Learners.

    For the selected period, returns from the latest DashboardMetrics row:
      - at_risk_learners: current count of at-risk learners.
      - at_risk_change_count: change in count vs previous period
        (precomputed and stored in DashboardMetrics).
    """
    date_keys_subq = get_date_keys_in_range(db, date_range)

    latest_row = (
        db.query(DashboardMetrics)
        .filter(DashboardMetrics.snapshot_date_key.in_(date_keys_subq))
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics for given period")

    return {
        "at_risk_learners": latest_row.at_risk_learners,
        "at_risk_change_count": latest_row.at_risk_change_count,
    }


# Average retention rate
@app.get("/dashboard/average-retention-rate")
def get_average_retention_rate(
    date_range: DateRange = Depends(get_date_range),
    db: Session = Depends(get_db),
):
    """
    Card: Average Retention Rate.

    For the selected period, returns from the latest DashboardMetrics row:
      - average_retention_rate: overall retention %.
      - retention_rate_change_pct: change in retention vs previous period.
    """
    date_keys_subq = get_date_keys_in_range(db, date_range)

    latest_row = (
        db.query(DashboardMetrics)
        .filter(DashboardMetrics.snapshot_date_key.in_(date_keys_subq))
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics for given period")

    return {
        "average_retention_rate": latest_row.average_retention_rate,
        "retention_rate_change_pct": latest_row.retention_rate_change_pct,
    }


# Trend of churn and retention rate
@app.get("/dashboard/retention-churn-trend")
def get_retention_churn_trend(
    date_range: DateRange = Depends(get_date_range),
    db: Session = Depends(get_db),
):
    """Line chart: monthly retention and churn trend.

    For all DashboardMetrics rows whose snapshot_date_key lies in the
    selected date range, joins DimDate to get calendar dates and
    returns a list of points ordered by date:
      - date
      - month_name
      - monthly_retention_rate
      - monthly_churn_rate
    """
    date_keys_subq = get_date_keys_in_range(db, date_range)

    rows = (
        db.query(DashboardMetrics, DimDate)
        .join(DimDate, DashboardMetrics.snapshot_date_key == DimDate.date_key)
        .filter(DashboardMetrics.snapshot_date_key.in_(date_keys_subq))
        .order_by(DimDate.full_date.asc())
        .all()
    )

    data = [
        {
            "date": dim_date.full_date,
            "month_name": dim_date.month_name,
            "monthly_retention_rate": metrics.monthly_retention_rate,
            "monthly_churn_rate": metrics.monthly_churn_rate,
        }
        for metrics, dim_date in rows
    ]

    return data


# Learners' segmentation
@app.get("/dashboard/learner-segmentation")
def get_learner_segmentation(
    date_range: DateRange = Depends(get_date_range),
    db: Session = Depends(get_db),
):
    """
    Donut chart: Learner segmentation by engagement.

    For the latest DashboardMetrics row within the selected period,
    returns counts and percentages for four engagement buckets:
      - highly_engaged
      - medium_engaged
      - at_risk
      - dormant
    """
    date_keys_subq = get_date_keys_in_range(db, date_range)

    latest_row = (
        db.query(DashboardMetrics)
        .filter(DashboardMetrics.snapshot_date_key.in_(date_keys_subq))
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics for given period")

    return {
        "highly_engaged": {
            "count": latest_row.highly_engaged_count,
            "pct": latest_row.highly_engaged_pct,
        },
        "medium_engaged": {
            "count": latest_row.medium_engaged_count,
            "pct": latest_row.medium_engaged_pct,
        },
        "at_risk": {
            "count": latest_row.at_risk_count,
            "pct": latest_row.at_risk_pct,
        },
        "dormant": {
            "count": latest_row.dormant_count,
            "pct": latest_row.dormant_pct,
        },
    }


# Top features driving churn
@app.get("/dashboard/top-features-driving-churn")
def get_top_features_driving_churn(
    date_range: DateRange = Depends(get_date_range),
    db: Session = Depends(get_db),
):
    """
    Bar chart: Top features driving churn.

    For the selected period:
      - filters FeatureImportance to churn_prediction models within
        the date range,
      - orders by latest snapshot first, then by importance_rank,
      - returns feature_name, importance_score and importance_rank
        for each row.
    """
    date_keys_subq = get_date_keys_in_range(db, date_range)

    rows = (
        db.query(FeatureImportance)
        .filter(
            FeatureImportance.snapshot_date_key.in_(date_keys_subq),
            FeatureImportance.model_type == "churn_prediction",
        )
        .order_by(FeatureImportance.snapshot_date_key.desc(),
                  FeatureImportance.importance_rank.asc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No feature importance data for given period")

    return [
        {
            "feature_name": r.feature_name,
            "importance_score": r.importance_score,
            "importance_rank": r.importance_rank,
        }
        for r in rows
    ]


# Second page, RFM analysis
@app.get("/learners/rfm-analysis")
def get_learners_rfm_analysis(
    country: Optional[str] = Query(None, description="Filter by country"),
    subscription_tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    RFM Analysis table endpoint.

    Returns one row per learner combining:
      - user profile (DimUser),
      - latest RFM / CLV / churn prediction snapshot (FactUserAnalyticsSnapshot),
      - latest daily activity (FactUserDailyActivity),
      - subscription plan (DimSubscriptionPlan).

    Optional filters:
      * country: restrict learners to a specific DimUser.country (or 'All Countries' on UI to skip).
      * subscription_tier: restrict learners to a specific DimSubscriptionPlan.tier
        (or 'All' on UI to skip).

    Response fields per learner:
      - user_id: natural key / external user identifier.
      - country: learner's country.
      - segment: RFM segment label.
      - rfm_score: sum of R, F, M scores (r_score + f_score + m_score).
      - clv: predicted customer lifetime value.
      - churn_risk_pct: churn_probability as a fraction (0–1, front‑end can convert to %).
      - last_active_days_ago: days_since_last_login from FactUserDailyActivity.
    """

    # Latest analytics snapshot per user
    subq_latest_snap = (
        db.query(
            FactUserAnalyticsSnapshot.user_key,
            func.max(FactUserAnalyticsSnapshot.snapshot_date_key).label("latest_key"),
        )
        .group_by(FactUserAnalyticsSnapshot.user_key)
        .subquery()
    )

    # Latest daily-activity row per user (for days_since_last_login)
    subq_latest_activity = (
        db.query(
            FactUserDailyActivity.user_key,
            func.max(FactUserDailyActivity.date_key).label("latest_date_key"),
        )
        .group_by(FactUserDailyActivity.user_key)
        .subquery()
    )

    q = (
        db.query(
            DimUser,
            FactUserAnalyticsSnapshot,
            DimSubscriptionPlan,
            FactUserDailyActivity,
        )
        .join(subq_latest_snap, DimUser.user_key == subq_latest_snap.c.user_key)
        .join(
            FactUserAnalyticsSnapshot,
            (FactUserAnalyticsSnapshot.user_key == subq_latest_snap.c.user_key)
            & (FactUserAnalyticsSnapshot.snapshot_date_key == subq_latest_snap.c.latest_key),
        )
        .join(
            DimSubscriptionPlan,
            FactUserAnalyticsSnapshot.subscription_plan_key
            == DimSubscriptionPlan.subscription_plan_key,
        )
        .join(
            subq_latest_activity,
            DimUser.user_key == subq_latest_activity.c.user_key,
        )
        .join(
            FactUserDailyActivity,
            (FactUserDailyActivity.user_key == subq_latest_activity.c.user_key)
            & (FactUserDailyActivity.date_key == subq_latest_activity.c.latest_date_key),
        )
    )

    if country and country != "All Countries":
        q = q.filter(DimUser.country == country)

    if subscription_tier and subscription_tier != "All":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)

    rows = q.all()

    result = []
    for user, snap, plan, activity in rows:
        rfm_score = (
            (snap.rfm_r_score or 0)
            + (snap.rfm_f_score or 0)
            + (snap.rfm_m_score or 0)
        )
        result.append(
            {
                "user_id": user.user_id_nk,
                "country": user.country,
                "segment": snap.rfm_segment,
                "rfm_score": rfm_score,
                "clv": snap.clv_value,
                "churn_risk_pct": snap.churn_probability,
                "last_active_days_ago": activity.days_since_last_login,
            }
        )

    return result


# Third page
# High-risk sumamry
@app.get("/high-risk/summary")
def get_high_risk_summary(
    risk_threshold: float = Query(0.7, description="Minimum churn_probability to be high-risk"),
    subscription_tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    db: Session = Depends(get_db),
):
    """
    Header cards: High-Risk Learners summary.

    Computes two numbers for the current high-risk cohort:
      - total_high_risk_learners: total count of users whose churn_probability
        is >= risk_threshold, optionally filtered by subscription tier.
      - new_high_risk_recent: how many of those high-risk users entered the
        snapshot in the last 7 date_key values (approx. “this week”).

    Args:
        risk_threshold: Minimum churn_probability (0–1) for a learner to be
            considered high-risk (default 0.7).
        subscription_tier: Optional DimSubscriptionPlan.tier filter
            (UI may pass 'All Subscriptions' to skip).

        db: SQLAlchemy session dependency.

    Uses:
        - FactUserAnalyticsSnapshot for churn_probability and snapshot_date_key.
        - DimSubscriptionPlan for filtering by plan tier.
        - DimDate to identify the latest 7 snapshot dates.
    """
    q = (
        db.query(FactUserAnalyticsSnapshot, DimSubscriptionPlan)
        .join(
            DimSubscriptionPlan,
            FactUserAnalyticsSnapshot.subscription_plan_key
            == DimSubscriptionPlan.subscription_plan_key,
        )
        .filter(FactUserAnalyticsSnapshot.churn_probability >= risk_threshold)
    )

    if subscription_tier and subscription_tier != "All Subscriptions":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)

    total_high_risk = q.count()

    # “new this week” = users whose snapshot_date_key is in the last 7 days
    latest_key_subq = (
        db.query(func.max(DimDate.date_key))
        .join(FactUserAnalyticsSnapshot,
              FactUserAnalyticsSnapshot.snapshot_date_key == DimDate.date_key)
        .scalar_subquery()
    )

    last_7_days_subq = (
        db.query(DimDate.date_key)
        .filter(DimDate.date_key <= latest_key_subq)
        .order_by(DimDate.date_key.desc())
        .limit(7)
        .subquery()
    )

    q_new = q.filter(FactUserAnalyticsSnapshot.snapshot_date_key.in_(last_7_days_subq))
    new_high_risk = q_new.count()

    return {
        "total_high_risk_learners": total_high_risk,
        "new_high_risk_recent": new_high_risk,
    }


# High-Risk Learner List
def _segment_to_campaign_type(rfm_segment: str) -> str:
    """Map a detailed RFM segment label into a broader campaign type.

    Args:
        rfm_segment: Text label from RFM segmentation
            (e.g., 'High-Value at Risk', 'Active High-Value Learners').

    Returns:
        One of:
          - 'retention'    for at-risk / declining / casual / dormant segments.
          - 'reactivation' for 'Recently Churned'.
          - 'upsell'       for healthy/loyal segments.
          - 'onboarding'   as a default fallback for other segments.
    """
    seg = (rfm_segment or "").lower()

    if (
        "high-value at risk" in seg
        or "declining engagement" in seg
        or "casual users" in seg
        or "dormant premium" in seg
    ):
        return "retention"

    if "recently churned" in seg:
        return "reactivation"

    if (
        "active high-value learners" in seg
        or "engaged subscribers" in seg
        or "loyal long-term" in seg
        or "promising starters" in seg
        or "new premium users" in seg
    ):
        return "upsell"

    return "onboarding"


CAMPAIGN_CONFIG = {
    "retention": {
        "offer_types": ["Discount", "Free Trial Extension"],
        "channels": ["Email", "SMS"],
    },
    "reactivation": {
        "offer_types": ["Free Trial Extension", "Discount"],
        "channels": ["Email", "Push Notification"],
    },
    "upsell": {
        "offer_types": ["Mentoring Session", "Free Content"],
        "channels": ["Email", "In-App"],
    },
    "onboarding": {
        "offer_types": ["Free Content", "Mentoring Session"],
        "channels": ["Email", "Push Notification"],
    },
}


def choose_suggested_action(rfm_segment: str) -> str:
    """Derive a recommended campaign action (channel + offer) from RFM segment.

    Uses _segment_to_campaign_type to classify the learner, then samples a
    combination from CAMPAIGN_CONFIG for that campaign type.

    Args:
        rfm_segment: Detailed segment label for the learner.

    Returns:
        String like 'Email / Discount' or 'Push Notification / Free Trial Extension'
        for display in the Suggested Action column.
    """
    campaign_type = _segment_to_campaign_type(rfm_segment)
    cfg = CAMPAIGN_CONFIG[campaign_type]
    offer = random.choice(cfg["offer_types"])
    channel = random.choice(cfg["channels"])
    # single column value combining both parts
    return f"{channel} / {offer}"


@app.get("/high-risk/learners")
def get_high_risk_learners(
    risk_threshold: float = Query(0.7, description="Minimum churn_probability to include"),
    subscription_tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    High-Risk Learner List table.

    Builds the rows for the main table on the High-Risk Learners page with:
      - Name
      - Segment (RFM segment)
      - Days Inactive
      - Churn Probability
      - Suggested Action (channel / offer)

    Logic:
      * Finds each user's latest analytics snapshot and latest daily activity.
      * Filters learners whose churn_probability >= risk_threshold.
      * Optionally filters by subscription_tier (DimSubscriptionPlan.tier).
      * For each learner, computes a suggested action using RFM segment.

    Args:
        risk_threshold: Minimum churn_probability (0–1) to be included.
        subscription_tier: Optional subscription tier filter
            ('All Subscriptions' on UI means no filtering).
        db: SQLAlchemy session dependency.
    """
    subq_latest_snap = (
        db.query(
            FactUserAnalyticsSnapshot.user_key,
            func.max(FactUserAnalyticsSnapshot.snapshot_date_key).label("latest_key"),
        )
        .group_by(FactUserAnalyticsSnapshot.user_key)
        .subquery()
    )

    subq_latest_act = (
        db.query(
            FactUserDailyActivity.user_key,
            func.max(FactUserDailyActivity.date_key).label("latest_date_key"),
        )
        .group_by(FactUserDailyActivity.user_key)
        .subquery()
    )

    q = (
        db.query(
            DimUser,
            FactUserAnalyticsSnapshot,
            DimSubscriptionPlan,
            FactUserDailyActivity,
        )
        .join(subq_latest_snap, DimUser.user_key == subq_latest_snap.c.user_key)
        .join(
            FactUserAnalyticsSnapshot,
            (FactUserAnalyticsSnapshot.user_key == subq_latest_snap.c.user_key)
            & (FactUserAnalyticsSnapshot.snapshot_date_key == subq_latest_snap.c.latest_key),
        )
        .join(
            DimSubscriptionPlan,
            FactUserAnalyticsSnapshot.subscription_plan_key
            == DimSubscriptionPlan.subscription_plan_key,
        )
        .join(subq_latest_act, DimUser.user_key == subq_latest_act.c.user_key)
        .join(
            FactUserDailyActivity,
            (FactUserDailyActivity.user_key == subq_latest_act.c.user_key)
            & (FactUserDailyActivity.date_key == subq_latest_act.c.latest_date_key),
        )
        .filter(FactUserAnalyticsSnapshot.churn_probability >= risk_threshold)
    )

    if subscription_tier and subscription_tier != "All Subscriptions":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)

    rows = q.all()

    result: List[Dict] = []
    for user, snap, plan, activity in rows:
        suggested_action = choose_suggested_action(snap.rfm_segment)
        result.append(
            {
                "name": user.user_id_nk,
                "segment": snap.rfm_segment,
                "days_inactive": activity.days_since_last_login,
                "churn_probability": snap.churn_probability,
                "suggested_action": suggested_action,  # e.g. "Email / Discount"
            }
        )

    return result


# Churn reason - Bar chart
@app.get("/high-risk/reasons-for-churn")
def get_reasons_for_churn(db: Session = Depends(get_db)) -> list[dict]:
    """
    Bar chart: Reasons for Churn.

    Uses the latest snapshot in ChurnReasons to build a list of
    churn drivers with:
      - reason: display name for the reason category.
      - count: number of at-risk / churned learners for that reason.

    This powers the 'Reasons for Churn' bar chart on the High-Risk page.
    """
    latest_key = db.query(func.max(ChurnReasons.snapshot_date_key)).scalar()
    if latest_key is None:
        return []

    rows = (
        db.query(ChurnReasons)
        .filter(ChurnReasons.snapshot_date_key == latest_key)
        .order_by(ChurnReasons.reason_count.desc())
        .all()
    )

    return [
        {
            "reason": r.reason_display_name,
            "count": r.reason_count,
        }
        for r in rows
    ]


# Churn by tier - Pie chart
@app.get("/high-risk/churn-by-tier")
def get_churn_by_tier(
    risk_threshold: float = Query(
        ..., description="Minimum churn_probability to be high-risk"
    ),
    subscription_tier: Optional[str] = Query(
        None, description="Optional filter for a single tier"
    ),
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Donut chart: distribution of high-risk learners by subscription tier.

    Counts how many high-risk learners (churn_probability >= risk_threshold)
    fall into each subscription plan tier, based on their latest analytics
    snapshot and current subscription plan.

    Args:
        risk_threshold: Minimum churn_probability (0–1) to treat as high-risk.
        subscription_tier: Optional tier filter; if provided (and not
            'All Subscriptions'), restricts the cohort to that tier only.
        db: SQLAlchemy session.

    Returns:
        List of objects with:
          - tier: subscription tier label.
          - count: number of high-risk learners in that tier.
          - pct: share of high-risk learners in that tier (0–100).
    """

    # latest analytics snapshot per user
    subq_latest_snap = (
        db.query(
            FactUserAnalyticsSnapshot.user_key,
            func.max(FactUserAnalyticsSnapshot.snapshot_date_key).label("latest_key"),
        )
        .group_by(FactUserAnalyticsSnapshot.user_key)
        .subquery()
    )

    q = (
        db.query(
            DimSubscriptionPlan.tier.label("tier"),
            func.count(FactUserAnalyticsSnapshot.user_key).label("count"),
        )
        .join(
            subq_latest_snap,
            FactUserAnalyticsSnapshot.user_key == subq_latest_snap.c.user_key,
        )
        .join(
            DimSubscriptionPlan,
            FactUserAnalyticsSnapshot.subscription_plan_key
            == DimSubscriptionPlan.subscription_plan_key,
        )
        .filter(
            FactUserAnalyticsSnapshot.snapshot_date_key == subq_latest_snap.c.latest_key,
            FactUserAnalyticsSnapshot.churn_probability >= risk_threshold,
        )
    )

    if subscription_tier and subscription_tier != "All Subscriptions":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)

    rows = q.group_by(DimSubscriptionPlan.tier).all()
    total = sum(r.count for r in rows) or 1

    return [
        {
            "tier": r.tier,
            "count": r.count,
            "pct": (r.count / total) * 100.0,
        }
        for r in rows
    ]


# Fourth page
@app.get("/campaigns/overview")
def get_campaigns_overview(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Active & Recent Campaigns table.

    Builds the data for the campaigns overview grid with one row per
    campaign, including:
      - campaign: campaign name.
      - target_segment: dominant engagement_level of learners who
        interacted with the campaign.
      - launch_date: campaign start date from DimCampaign / DimDate.
      - open_rate_pct: campaign-level open rate from CampaignPerformance.
      - retention_lift_pct: retention lift vs. control from CampaignPerformance.
      - status: campaign lifecycle status (e.g., Active, Completed).

    Joins:
      * CampaignPerformance → DimCampaign (by campaign_key) for campaign metadata.
      * DimCampaign → DimDate (by start_date_key) for launch date.
      * DimCampaign → FactUserDailyActivity (by campaign_key) to find
        users in the campaign.
      * FactUserDailyActivity → FactUserAnalyticsSnapshot (by user_key and date_key)
        to read engagement_level.

    Grouping is done by campaign and engagement_level to derive one
    engagement-based target segment per campaign row.
    """

    rows = (
        db.query(
            CampaignPerformance,
            DimCampaign,
            DimDate,
            FactUserAnalyticsSnapshot.engagement_level,
        )
        .join(DimCampaign, CampaignPerformance.campaign_key == DimCampaign.campaign_key)
        .join(DimDate, DimCampaign.start_date_key == DimDate.date_key)
        .join(
            FactUserDailyActivity,
            FactUserDailyActivity.campaign_key == DimCampaign.campaign_key,
        )
        .join(
            FactUserAnalyticsSnapshot,
            (FactUserAnalyticsSnapshot.user_key == FactUserDailyActivity.user_key)
            & (FactUserAnalyticsSnapshot.snapshot_date_key == FactUserDailyActivity.date_key),
        )
        .group_by(
            CampaignPerformance.campaign_performance_id,
            DimCampaign.campaign_key,
            DimDate.date_key,
            FactUserAnalyticsSnapshot.engagement_level,
        )
        .order_by(DimDate.full_date.desc())
        .all()
    )

    result: List[Dict] = []
    for perf, camp, date, engagement_level in rows:
        result.append(
            {
                "campaign": perf.campaign_name or camp.campaign_name,
                "target_segment": engagement_level or "Unknown",
                "launch_date": date.full_date.isoformat(),
                "open_rate_pct": perf.open_rate,
                "retention_lift_pct": perf.retention_lift,
                "status": perf.status,
            }
        )

    return result


@app.get("/campaigns/performance-comparison")
def get_campaign_performance_comparison(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Campaign Performance Comparison chart (Lift vs. Churn Rate).

    For each campaign, returns:
      - campaign: campaign name.
      - churn_rate_pct: implied churn rate for the campaign group
        (100 - campaign_retention_rate).
      - retention_lift_pct: lift in retention vs. control group.

    Data source:
      * CampaignPerformance provides campaign_retention_rate,
        control_retention_rate and retention_lift.
      * DimCampaign provides the human-readable campaign_name.

    This output feeds the grouped bar chart where:
      - blue bar = churn_rate_pct.
      - green bar = retention_lift_pct.
    """
    rows = (
        db.query(
            DimCampaign.campaign_name.label("campaign_name"),
            CampaignPerformance.campaign_retention_rate.label("campaign_retention_rate"),
            CampaignPerformance.control_retention_rate.label("control_retention_rate"),
            CampaignPerformance.retention_lift.label("retention_lift"),
        )
        .join(CampaignPerformance, CampaignPerformance.campaign_key == DimCampaign.campaign_key)
        .order_by(DimCampaign.campaign_name.asc())
        .all()
    )

    result: List[Dict] = []
    for r in rows:
        # churn rate for chart = 100 - campaign_retention_rate
        churn_rate_pct = 100.0 - (r.campaign_retention_rate or 0.0)

        result.append(
            {
                "campaign": r.campaign_name,
                "churn_rate_pct": churn_rate_pct,
                "retention_lift_pct": r.retention_lift,
            }
        )

    return result


# Fifth page
# Accuracy
@app.get("/models/accuracy")
def get_model_accuracy(
    model_type: str = "churn_prediction",
    db: Session = Depends(get_db),
) -> Dict:
    """
    Model Accuracy card.

    For the given model_type (default: 'churn_prediction'), looks at the
    two most recent ModelPerformanceMetrics rows and returns:
      - current_accuracy_pct: latest accuracy multiplied by 100.
      - accuracy_change_pct: difference (current - previous) in
        percentage points, or None if only one snapshot exists.

    This powers the main accuracy KPI card with the big percentage and
    the small up/down delta indicator.
    """

    rows = (
        db.query(ModelPerformanceMetrics)
        .filter(ModelPerformanceMetrics.model_type == model_type)
        .order_by(desc(ModelPerformanceMetrics.snapshot_date_key))
        .limit(2)
        .all()
    )

    if not rows:
        return {"current_accuracy_pct": None, "accuracy_change_pct": None}

    current = rows[0]
    current_acc = (current.accuracy or 0.0) * 100.0

    if len(rows) == 1:
        change = None
    else:
        prev = rows[1]
        prev_acc = (prev.accuracy or 0.0) * 100.0
        change = current_acc - prev_acc

    return {
        "current_accuracy_pct": current_acc,
        "accuracy_change_pct": change,
    }


# Precision
@app.get("/models/precision")
def get_model_precision(
    model_type: str = "churn_prediction",
    db: Session = Depends(get_db),
) -> Dict:
    """
    Precision card.

    For the given model_type, compares the last two performance snapshots
    and returns:
      - current_precision_pct: latest precision * 100.
      - precision_change_pct: current_precision_pct - previous_precision_pct,
        or None if there is only one snapshot.

    This card shows how often positive predictions are actually correct
    for the churn model, plus the recent improvement or decline.
    """
    rows = (
        db.query(ModelPerformanceMetrics)
        .filter(ModelPerformanceMetrics.model_type == model_type)
        .order_by(desc(ModelPerformanceMetrics.snapshot_date_key))
        .limit(2)
        .all()
    )

    if not rows:
        return {"current_precision_pct": None, "precision_change_pct": None}

    current = rows[0]
    current_prec = (current.precision or 0.0) * 100.0

    if len(rows) == 1:
        change = None
    else:
        prev = rows[1]
        prev_prec = (prev.precision or 0.0) * 100.0
        change = current_prec - prev_prec

    return {
        "current_precision_pct": current_prec,
        "precision_change_pct": change,
    }


# Recall
@app.get("/models/recall")
def get_model_recall(
    model_type: str = "churn_prediction",
    db: Session = Depends(get_db),
) -> Dict:
    """
    Recall card.

    For the given model_type, compares the two latest model runs and returns:
      - current_recall_pct: latest recall * 100.
      - recall_change_pct: change in recall vs. previous snapshot in
        percentage points, or None if no previous snapshot exists.

    Recall here measures how many actual churners the model correctly
    flags, and the delta shows recent trend in sensitivity.
    """
    rows = (
        db.query(ModelPerformanceMetrics)
        .filter(ModelPerformanceMetrics.model_type == model_type)
        .order_by(desc(ModelPerformanceMetrics.snapshot_date_key))
        .limit(2)
        .all()
    )

    if not rows:
        return {"current_recall_pct": None, "recall_change_pct": None}

    current = rows[0]
    current_rec = (current.recall or 0.0) * 100.0

    if len(rows) == 1:
        change = None
    else:
        prev = rows[1]
        prev_rec = (prev.recall or 0.0) * 100.0
        change = current_rec - prev_rec

    return {
        "current_recall_pct": current_rec,
        "recall_change_pct": change,
    }


# AUC-ROC
@app.get("/models/auc-roc")
def get_model_auc_roc(
    model_type: str = "churn_prediction",
    db: Session = Depends(get_db),
) -> Dict:
    """
    AUC-ROC Score card.

    For the given model_type, inspects the last two entries in
    ModelPerformanceMetrics and returns:
      - current_auc_roc: latest area under the ROC curve (0–1).
      - auc_roc_change: difference between current and previous AUC
        (current_auc_roc - previous_auc_roc), or None if only one
        snapshot exists.

    This card summarizes overall ranking performance of the churn model
    across all thresholds, together with its recent improvement.
    """

    rows = (
        db.query(ModelPerformanceMetrics)
        .filter(ModelPerformanceMetrics.model_type == model_type)
        .order_by(desc(ModelPerformanceMetrics.snapshot_date_key))
        .limit(2)
        .all()
    )

    if not rows:
        return {"current_auc_roc": None, "auc_roc_change": None}

    current = rows[0]
    current_auc = current.auc_roc or 0.0

    if len(rows) == 1:
        change = None
    else:
        prev = rows[1]
        prev_auc = prev.auc_roc or 0.0
        change = current_auc - prev_auc

    return {
        "current_auc_roc": current_auc,
        "auc_roc_change": change,
    }


# Feature Importance
@app.get("/models/feature-importance")
def get_model_feature_importance(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Feature Importance horizontal bar chart.

    Retrieves the latest feature importance snapshot for the churn prediction model
    (model_type = 'churn_prediction') and returns the features ordered by their
    importance_rank.

    For each feature, the response includes:
      - feature_name: human-readable feature label.
      - importance_score: relative importance value (scale defined by DS pipeline).

    The frontend uses this list to draw a horizontal bar chart where each bar
    represents a feature and its contribution to the churn model.
    """
    latest_key = (
        db.query(func.max(FeatureImportance.snapshot_date_key))
        .filter(FeatureImportance.model_type == "churn_prediction")
        .scalar()
    )
    if latest_key is None:
        return []

    rows = (
        db.query(FeatureImportance)
        .filter(
            FeatureImportance.snapshot_date_key == latest_key,
            FeatureImportance.model_type == "churn_prediction",
        )
        .order_by(FeatureImportance.importance_rank.asc())
        .all()
    )

    return [
        {
            "feature_name": r.feature_name,
            "importance_score": r.importance_score,
        }
        for r in rows
    ]


# Needs to be reviewed for final milestone
@app.get("/models/roc-curve")
def get_model_roc_curve(
    model_type: str = "churn_prediction",
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Churn Prediction Accuracy (ROC Curve).

    Builds an approximate ROC curve for the specified model_type using the most
    recent ModelPerformanceMetrics row:

      - If no metrics or no AUC is available, returns a simple diagonal
        ROC (fpr = tpr) representing a random classifier.
      - Otherwise, generates 11 points (fpr from 0.0 to 1.0 in steps of 0.1)
        and approximates tpr as an increasing function of fpr and the model's
        auc_roc score.

    Output format:
      - fpr: false positive rate (x-axis).
      - tpr: true positive rate (y-axis).

    The frontend plots these points as the blue ROC curve and can overlay its
    own diagonal baseline for comparison.
    """

    latest = (
        db.query(ModelPerformanceMetrics)
        .filter(ModelPerformanceMetrics.model_type == model_type)
        .order_by(desc(ModelPerformanceMetrics.snapshot_date_key))
        .first()
    )
    if not latest or latest.auc_roc is None:
        # fallback: diagonal line (random classifier)
        return [{"fpr": x / 10.0, "tpr": x / 10.0} for x in range(0, 11)]

    auc = latest.auc_roc

    # simple parametric ROC approximation: tpr = (fpr ** 0.5) * (2 * auc - 1 + 1)
    points: List[Dict] = []
    for i in range(0, 11):
        fpr = i / 10.0
        base = fpr ** 0.5
        tpr = min(1.0, max(0.0, base * (2 * auc - 1 + 1)))  # keep in [0,1]
        points.append({"fpr": fpr, "tpr": tpr})

    return points


# Segment-retention-probability
@app.get("/models/segment-retention-probability")
def get_segment_retention_probability(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Segment-wise Retention Probability bar chart.

    For each engagement segment (engagement_level) in FactUserAnalyticsSnapshot,
    this endpoint calculates the average retention probability based on the
    most recent snapshot per user.

    Steps:
      1. Find the latest snapshot_date_key for each user.
      2. Join back to FactUserAnalyticsSnapshot on (user_key, latest_key).
      3. Group by engagement_level and compute:
           retention_prob = avg(1 - churn_probability).

    Returns a list of:
      - segment: engagement_level label (e.g., 'Highly Engaged', 'At Risk').
      - retention_probability_pct: average retention probability in percent (0–100).

    The frontend uses this to draw a bar chart comparing how likely different
    segments are to stay subscribed.
    """

    # latest snapshot per user
    subq_latest = (
        db.query(
            FactUserAnalyticsSnapshot.user_key,
            func.max(FactUserAnalyticsSnapshot.snapshot_date_key).label("latest_key"),
        )
        .group_by(FactUserAnalyticsSnapshot.user_key)
        .subquery()
    )

    rows = (
        db.query(
            FactUserAnalyticsSnapshot.engagement_level.label("segment"),
            func.avg(1.0 - FactUserAnalyticsSnapshot.churn_probability).label("retention_prob"),
        )
        .join(
            subq_latest,
            (FactUserAnalyticsSnapshot.user_key == subq_latest.c.user_key)
            & (FactUserAnalyticsSnapshot.snapshot_date_key == subq_latest.c.latest_key),
        )
        .group_by(FactUserAnalyticsSnapshot.engagement_level)
        .all()
    )

    return [
        {
            "segment": r.segment or "Unknown",
            "retention_probability_pct": (r.retention_prob or 0.0) * 100.0,
        }
        for r in rows
    ]


# Survival curve
@app.get("/models/survival-curve")
def get_survival_curve(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Survival Curve (Expected Subscription Duration).

    Approximates a global subscription survival curve using summary survival
    information from FactUserAnalyticsSnapshot:

      - Computes the average survival_median_time_to_downgrade (in days) over
        all users and converts it to months.
      - Assumes an exponential-like survival process where S(median) ≈ 0.5.
      - Evaluates survival at fixed time points (months = [0, 3, 6, 9, 12, 15,
        18, 21, 24]) to produce a step-like survival curve.

    For each time point, returns:
      - months: time since subscription start (x-axis).
      - survival_rate_pct: probability of still being subscribed at that time,
        expressed as a percentage (0–100).

    The frontend can plot these as a shaded area chart to visualize how quickly
    the subscription cohort decays over time.
    """

    # get median-of-medians as global scale (in months)
    agg = db.query(
        func.avg(FactUserAnalyticsSnapshot.survival_median_time_to_downgrade)
    ).one()
    median_days = agg[0] or 180.0  # fallback 6 months if null
    median_months = median_days / 30.0

    time_points = [0, 3, 6, 9, 12, 15, 18, 21, 24]

    def approx_survival(t_months: float) -> float:
        # simple exponential-like drop anchored at median
        # S(median) ≈ 0.5
        if t_months <= 0:
            return 1.0
        lam = (0.5) ** (1.0 / median_months)
        return lam ** t_months

    curve: List[Dict] = []
    for m in time_points:
        s = approx_survival(m)
        curve.append(
            {
                "months": m,
                "survival_rate_pct": s * 100.0,
            }
        )

    return curve









# Additional endpoints that are not needed yet
# -------- DIMUSER CRUD --------
@app.get("/users", response_model=list[DimUserSchema])
def get_users(db: Session = Depends(get_db)):
    users = db.query(DimUser).all()
    return users

@app.post("/users", response_model=DimUserSchema, status_code=status.HTTP_201_CREATED)
def add_user(user: DimUserCreate, db: Session = Depends(get_db)):
    db_user = DimUser(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/users/{user_key}", response_model=DimUserSchema)
def update_user(user_key: int, user_update: DimUserCreate, db: Session = Depends(get_db)):
    user = db.query(DimUser).filter(DimUser.user_key == user_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_update.dict().items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_key}")
def delete_user(user_key: int, db: Session = Depends(get_db)):
    user = db.query(DimUser).filter(DimUser.user_key == user_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# -------- PLANS CRUD --------
@app.get("/plans", response_model=list[DimSubscriptionPlanSchema])
def get_plans(db: Session = Depends(get_db)):
    return db.query(DimSubscriptionPlan).all()

@app.post("/plans", response_model=DimSubscriptionPlanSchema, status_code=status.HTTP_201_CREATED)
def add_plan(plan: DimSubscriptionPlanCreate, db: Session = Depends(get_db)):
    db_plan = DimSubscriptionPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.put("/plans/{subscription_plan_key}", response_model=DimSubscriptionPlanSchema)
def update_plan(subscription_plan_key: int, plan_update: DimSubscriptionPlanCreate, db: Session = Depends(get_db)):
    plan = db.query(DimSubscriptionPlan).filter(DimSubscriptionPlan.subscription_plan_key == subscription_plan_key).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for k, v in plan_update.dict().items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return plan

@app.delete("/plans/{subscription_plan_key}")
def delete_plan(subscription_plan_key: int, db: Session = Depends(get_db)):
    plan = db.query(DimSubscriptionPlan).filter(DimSubscriptionPlan.subscription_plan_key == subscription_plan_key).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"success": True, "message": "Plan deleted successfully"}

# -------- DIMDATE CRUD --------
@app.get("/dates", response_model=list[DimDateSchema])
def get_dates(db: Session = Depends(get_db)):
    return db.query(DimDate).all()

@app.post("/dates", response_model=DimDateSchema, status_code=status.HTTP_201_CREATED)
def add_date(date: DimDateCreate, db: Session = Depends(get_db)):
    db_date = DimDate(**date.dict())
    db.add(db_date)
    db.commit()
    db.refresh(db_date)
    return db_date

@app.put("/dates/{date_key}", response_model=DimDateSchema)
def update_date(date_key: int, date_update: DimDateCreate, db: Session = Depends(get_db)):
    date_row = db.query(DimDate).filter(DimDate.date_key == date_key).first()
    if not date_row:
        raise HTTPException(status_code=404, detail="Date not found")
    for k, v in date_update.dict().items():
        setattr(date_row, k, v)
    db.commit()
    db.refresh(date_row)
    return date_row

@app.delete("/dates/{date_key}")
def delete_date(date_key: int, db: Session = Depends(get_db)):
    date_row = db.query(DimDate).filter(DimDate.date_key == date_key).first()
    if not date_row:
        raise HTTPException(status_code=404, detail="Date not found")
    db.delete(date_row)
    db.commit()
    return {"success": True, "message": "Date deleted successfully"}

# -------- Example Analytic Endpoint --------
@app.get("/count_risk_customers")
def count_risk_customers(db: Session = Depends(get_db), threshold: float = Query(0.7)):
    risk_customers = db.query(FactUserAnalyticsSnapshot).filter(FactUserAnalyticsSnapshot.churn_probability >= threshold).count()
    return {"count_risk_customers": risk_customers}

# -------- Dummy Endpoints for Milestone 2 --------
@app.get("/dummy")
def dummy_get():
    return {"msg": "GET working"}

@app.post("/dummy")
def dummy_post(data: dict):
    return {"msg": "POST working", "data": data}

@app.put("/dummy")
def dummy_put(data: dict):
    return {"msg": "PUT working", "data": data}

@app.delete("/dummy")
def dummy_delete():
    return {"msg": "DELETE working"}

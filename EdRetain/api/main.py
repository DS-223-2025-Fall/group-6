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
# Active premium learners
@app.get("/dashboard/active-premium-learners")
def get_active_premium_learners(
    db: Session = Depends(get_db),
):
    """
    Retrieve the latest Active Premium Learners KPI for the dashboard card.

    This endpoint queries the DashboardMetrics table, selects the row with the
    most recent snapshot_date_key, and returns:
      - active_premium_learners: the current count of active premium learners
        at the time of the latest snapshot.
      - active_premium_change_pct: the percentage change in active premium
        learners compared with the previous period, as precomputed in the
        latest DashboardMetrics record.

    If no DashboardMetrics rows are available, the endpoint responds with
    HTTP 404 to indicate that no dashboard metrics data exists yet.
    """
    latest_row = (
        db.query(DashboardMetrics)
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics available")

    return {
        "active_premium_learners": latest_row.active_premium_learners,
        "active_premium_change_pct": latest_row.active_premium_change_pct,
    }


# At risk learners 
@app.get("/dashboard/at-risk-learners")
def get_at_risk_learners(
    db: Session = Depends(get_db),
):
    """
    Retrieve the latest At-Risk Learners KPIs for the dashboard card.

    This endpoint queries the DashboardMetrics table, selects the record with
    the most recent snapshot_date_key, and returns:
      - at_risk_learners: the current count of learners classified as at-risk
        in the latest available snapshot.
      - at_risk_change_count: the absolute change in the number of at-risk
        learners compared with the previous period, as stored in the same
        DashboardMetrics row.

    If no DashboardMetrics rows exist in the database, the endpoint responds
    with HTTP 404 to indicate that dashboard metrics data is not available.
    """
    latest_row = (
        db.query(DashboardMetrics)
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics available")

    return {
        "at_risk_learners": latest_row.at_risk_learners,
        "at_risk_change_count": latest_row.at_risk_change_count,
    }


# Average retention rate
@app.get("/dashboard/average-retention-rate")
def get_average_retention_rate(
    db: Session = Depends(get_db),
):
    """
    Retrieve the latest Average Retention Rate KPIs for the dashboard card.

    This endpoint queries the DashboardMetrics table, selects the record with
    the most recent snapshot_date_key, and returns:
      - average_retention_rate: the overall retention percentage from the
        latest available snapshot.
      - retention_rate_change_pct: the percentage change in retention rate
        compared with the previous period, as stored in that same
        DashboardMetrics row.

    If no DashboardMetrics rows exist in the database, the endpoint responds
    with HTTP 404 to indicate that dashboard metrics data is not available.
    """
    latest_row = (
        db.query(DashboardMetrics)
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics available")

    return {
        "average_retention_rate": latest_row.average_retention_rate,
        "retention_rate_change_pct": latest_row.retention_rate_change_pct,
    }



# Trend of churn and retention rate
@app.get("/dashboard/retention-churn-trend")
def get_retention_churn_trend(
    db: Session = Depends(get_db),
):
    """
    Retrieve monthly retention and churn rates for the trend line chart.

    This endpoint queries all rows from the DashboardMetrics table, joins
    them with the DimDate table on snapshot_date_key to obtain calendar
    dates, and returns a time-ordered list of data points. For each month,
    it outputs:
      - date: the calendar date associated with the snapshot.
      - month_name: the human-readable month name (from DimDate if present,
        otherwise derived from the date).
      - monthly_retention_rate: the retention rate for that month, taken
        from monthly_retention_rate if available, or from retention_rate
        as a fallback.
      - monthly_churn_rate: the churn rate for that month, taken from
        monthly_churn_rate if available, or from churn_rate as a fallback.

    The results are ordered by DimDate.full_date in ascending order to be
    directly consumable by a front-end line chart component.
    """
    rows = (
        db.query(DashboardMetrics, DimDate)
        .join(DimDate, DashboardMetrics.snapshot_date_key == DimDate.date_key)
        .order_by(DimDate.full_date.asc())
        .all()
    )

    data = []
    for metrics, dim_date in rows:
        monthly_ret = getattr(metrics, "monthly_retention_rate", None)
        if monthly_ret is None:
            monthly_ret = getattr(metrics, "retention_rate", None)

        monthly_churn = getattr(metrics, "monthly_churn_rate", None)
        if monthly_churn is None:
            monthly_churn = getattr(metrics, "churn_rate", None)

        data.append(
            {
                "date": dim_date.full_date,
                "month_name": getattr(
                    dim_date, "month_name", dim_date.full_date.strftime("%b")
                ),
                "monthly_retention_rate": monthly_ret,
                "monthly_churn_rate": monthly_churn,
            }
        )

    return data


# Learners' segmentation
@app.get("/dashboard/learner-segmentation")
def get_learner_segmentation(
    db: Session = Depends(get_db),
):
    """
    Donut chart: Retrieve the latest learner engagement segmentation for the donut chart.

    This endpoint queries the DashboardMetrics table, selects the record with
    the most recent snapshot_date_key, and returns four engagement buckets:
      - highly_engaged: count and percentage of highly engaged learners.
      - medium_engaged: count and percentage of moderately engaged learners.
      - at_risk: count and percentage of learners at risk of churn.
      - dormant: count and percentage of dormant or inactive learners.

    The percentages are taken directly from the latest DashboardMetrics row.
    If no DashboardMetrics data is available, the endpoint responds with HTTP 404.
    """
    latest_row = (
        db.query(DashboardMetrics)
        .order_by(DashboardMetrics.snapshot_date_key.desc())
        .first()
    )

    if not latest_row:
        raise HTTPException(status_code=404, detail="No dashboard metrics available")

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
    db: Session = Depends(get_db),
):
    """
    Bar chart: Retrieve the top model features driving churn for the bar chart.

    This endpoint first finds the most recent snapshot_date_key in the
    FeatureImportance table for rows where model_type is 'churn_prediction'.
    It then returns all feature importance records for that snapshot, ordered
    by importance_rank in ascending order, so that the most important features
    appear first.

    The response is a list of objects, each containing:
      - feature_name: the name of the feature.
      - importance_score: the feature's importance score in the churn model.
      - importance_rank: the feature's rank by importance (1 is most important).

    If no churn_prediction feature importance data is available, the endpoint
    responds with HTTP 404 to indicate that no relevant snapshot exists.
    """
    latest_key = (
        db.query(func.max(FeatureImportance.snapshot_date_key))
        .filter(FeatureImportance.model_type == "churn_prediction")
        .scalar()
    )
    if latest_key is None:
        raise HTTPException(status_code=404, detail="No feature importance data")

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
            "importance_rank": r.importance_rank,
        }
        for r in rows
    ]


# Second page, RFM analysis
@app.get("/learners/rfm-analysis")
def get_learners_rfm_analysis(
    country: Optional[str] = Query(None, description="Filter by country"),
    subscription_tier: Optional[str] = Query(
        None, description="Filter by subscription tier"
    ),
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Retrieve the latest RFM / churn / CLV analytics per learner for the table view.

    For each learner, this endpoint:
      - Finds the most recent FactUserAnalyticsSnapshot (by snapshot_date_key).
      - Finds the most recent FactUserDailyActivity record (by date_key) to get
        days_since_last_login.
      - Joins DimUser, DimSubscriptionPlan, and these latest fact rows to build
        a single consolidated record.

    Optional filters:
      - country: if provided and not "All Countries", restricts learners to the
        specified DimUser.country.
      - subscription_tier: if provided and not "All", restricts learners to the
        specified DimSubscriptionPlan.tier.

    The response returns one object per learner with:
      - user_id: external/natural user identifier.
      - country: learner's country.
      - segment_label: business-friendly segment label from the analytics model.
      - kmeans_segment_label: cluster label from k‑means segmentation.
      - rfm_segment: RFM segment code for the learner.
      - clv: predicted customer lifetime value.
      - churn_risk_pct: churn_probability as a 0–1 fraction.
      - last_active_days_ago: days_since_last_login from the latest activity row.
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
            & (
                FactUserAnalyticsSnapshot.snapshot_date_key
                == subq_latest_snap.c.latest_key
            ),
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
            & (
                FactUserDailyActivity.date_key
                == subq_latest_activity.c.latest_date_key
            ),
        )
    )

    if country and country != "All Countries":
        q = q.filter(DimUser.country == country)

    if subscription_tier and subscription_tier != "All":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)

    rows = q.all()

    result: List[Dict] = []
    for user, snap, plan, activity in rows:
        result.append(
            {
                "user_id": user.user_id_nk,
                "country": user.country,
                "segment_label": snap.segment_label,
                "kmeans_segment_label": snap.kmeans_segment_label,
                "rfm_segment": snap.rfm_segment,
                "clv": snap.clv_value,
                "churn_risk_pct": snap.churn_probability,
                "last_active_days_ago": activity.days_since_last_login,
            }
        )

    return result


# Third page
@app.get("/learners/filters")
def get_learners_filters(
    db: Session = Depends(get_db),
) -> Dict[str, List[str]]:
    """
    Retrieve available filter options for the Learners RFM Analysis page.

    This endpoint queries the DimUser and DimSubscriptionPlan tables to build
    distinct, non-null lists of:
      - countries: all unique DimUser.country values, sorted alphabetically.
      - subscription_tiers: all unique DimSubscriptionPlan.tier values, sorted
        alphabetically.

    The resulting lists are returned in a JSON object and are intended to
    populate the Country and Subscription Tier dropdowns on the frontend.
    """
    # Distinct countries
    country_rows = (
        db.query(DimUser.country)
        .filter(DimUser.country.isnot(None))
        .distinct()
        .order_by(DimUser.country.asc())
        .all()
    )
    countries = [row[0] for row in country_rows if row[0]]

    # Distinct subscription tiers
    tier_rows = (
        db.query(DimSubscriptionPlan.tier)
        .filter(DimSubscriptionPlan.tier.isnot(None))
        .distinct()
        .order_by(DimSubscriptionPlan.tier.asc())
        .all()
    )
    subscription_tiers = [row[0] for row in tier_rows if row[0]]

    return {
        "countries": countries,
        "subscription_tiers": subscription_tiers,
    }


# High-risk sumamry
@app.get("/high-risk/summary")
def get_high_risk_summary(
    risk_threshold: float = Query(0.7, description="Minimum churn_probability to be high-risk"),
    subscription_tier: Optional[str] = Query(
        None, description="Filter by subscription tier"
    ),
    country: Optional[str] = Query(
        None, description="Filter by learner country"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve high-risk learner summary metrics for the header cards.

    This endpoint queries FactUserAnalyticsSnapshot to identify learners whose
    churn_probability meets or exceeds the specified risk_threshold (default 0.7).
    It joins with DimSubscriptionPlan and DimUser to support filtering and
    computes two metrics:
      - total_high_risk_learners: the total count of learners meeting the risk
        threshold, subject to any applied filters.
      - new_high_risk_recent: the count of those high-risk learners whose
        analytics snapshot falls within the most recent 7 date_keys.

    Optional filters:
      - subscription_tier: if provided and not "All Subscriptions", restricts
        to the specified tier. If omitted or "All Subscriptions", excludes the
        "Free" tier.
      - country: if provided and not "All Countries", restricts learners to
        the specified DimUser.country.
      - risk_threshold: minimum churn_probability to classify a learner as
        high-risk (default 0.7).

    The "recent" count uses the last 7 date_key values in DimDate to approximate
    learners flagged as high-risk in the most recent week of snapshots.
    """

    q = (
        db.query(FactUserAnalyticsSnapshot, DimSubscriptionPlan, DimUser)
        .join(
            DimSubscriptionPlan,
            FactUserAnalyticsSnapshot.subscription_plan_key
            == DimSubscriptionPlan.subscription_plan_key,
        )
        .join(
            DimUser,
            FactUserAnalyticsSnapshot.user_key == DimUser.user_key,
        )
        .filter(FactUserAnalyticsSnapshot.churn_probability >= risk_threshold)
    )

    if subscription_tier and subscription_tier != "All Subscriptions":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)
    else:
        q = q.filter(DimSubscriptionPlan.tier != "Free")

    if country and country != "All Countries":
        q = q.filter(DimUser.country == country)

    total_high_risk = q.count()

    latest_key_subq = (
        db.query(func.max(DimDate.date_key))
        .join(
            FactUserAnalyticsSnapshot,
            FactUserAnalyticsSnapshot.snapshot_date_key == DimDate.date_key,
        )
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
    """
    Map a detailed RFM segment label to a broader campaign type category.

    This helper function examines the provided RFM segment label and returns
    one of four campaign types based on keyword matching:
      - "retention": assigned to segments indicating at-risk, declining, casual,
        or dormant premium users who need intervention to prevent churn.
      - "reactivation": assigned to segments indicating recently churned users
        who may be re-engaged.
      - "upsell": assigned to segments indicating active, engaged, loyal, or
        promising users who are candidates for upgrade or expansion offers.
      - "onboarding": the default fallback for segments that do not match the
        above categories, typically representing new or unclassified users.

    Args:
        rfm_segment (str): The RFM segment label (may be None or empty).

    Returns:
        str: One of "retention", "reactivation", "upsell", or "onboarding".
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
    risk_threshold: float = Query(
        0.7, description="Minimum churn_probability to include"
    ),
    subscription_tier: Optional[str] = Query(
        None, description="Filter by subscription tier"
    ),
    country: Optional[str] = Query(
        None, description="Filter by learner country"
    ),
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Retrieve a detailed list of high-risk learners for the table view.

    This endpoint selects the latest analytics snapshot and latest daily-activity
    record for each learner, then filters learners whose churn_probability is
    greater than or equal to the specified risk_threshold (default 0.7). It
    joins DimUser, DimSubscriptionPlan, FactUserAnalyticsSnapshot, and
    FactUserDailyActivity to assemble learner profile, risk, and engagement
    information.

    Optional filters:
      - subscription_tier: if provided and not "All Subscriptions", restricts
        learners to the specified DimSubscriptionPlan.tier. If omitted or
        "All Subscriptions", excludes the "Free" tier.
      - country: if provided and not "All Countries", restricts learners to the
        specified DimUser.country.
      - risk_threshold: minimum churn_probability for inclusion in the list.

    For each high-risk learner, the response includes:
      - name: external/natural user identifier (user_id_nk).
      - segment: human-readable segment label from the analytics model.
      - days_inactive: days_since_last_login from the latest activity record.
      - churn_probability: predicted churn probability as a 0–1 value.
      - suggested_action: recommended campaign action (channel and offer)
        derived from the learner's RFM segment.
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
            & (
                FactUserAnalyticsSnapshot.snapshot_date_key
                == subq_latest_snap.c.latest_key
            ),
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
    else:
        q = q.filter(DimSubscriptionPlan.tier != "Free")

    if country and country != "All Countries":
        q = q.filter(DimUser.country == country)

    rows = q.all()

    result: List[Dict] = []
    for user, snap, plan, activity in rows:
        suggested_action = choose_suggested_action(snap.rfm_segment)

        result.append(
            {
                "name": user.user_id_nk,
                "segment": snap.segment_label,
                "days_inactive": activity.days_since_last_login,
                "churn_probability": snap.churn_probability,
                "suggested_action": suggested_action,
            }
        )

    return result


# Churn reason - Bar chart
@app.get("/high-risk/reasons-for-churn")
def get_reasons_for_churn(db: Session = Depends(get_db)) -> List[Dict]:
    """
    Bar chart: Retrieve the top reasons for churn for the bar chart.

    This endpoint queries the ChurnReasons table to find the most recent
    snapshot_date_key, then returns all churn reason records from that snapshot,
    ordered by reason_count in descending order so that the most common reasons
    appear first.

    Each returned object contains:
      - reason: the user-friendly display name for the churn reason category.
      - count: the number of at-risk learners with this primary churn reason.

    If no ChurnReasons data is available, an empty list is returned.
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
    country: Optional[str] = Query(
        None, description="Optional filter for learner country"
    ),
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Retrieve the distribution of high-risk learners by subscription tier for the donut chart.

    This endpoint selects the latest analytics snapshot for each learner, filters
    for those whose churn_probability meets or exceeds the specified risk_threshold,
    and aggregates the count of high-risk learners by DimSubscriptionPlan.tier.

    Required parameter:
      - risk_threshold: minimum churn_probability to classify a learner as high-risk.

    Optional filters:
      - subscription_tier: if provided and not "All Subscriptions", restricts the
        aggregation to the specified tier. If omitted or "All Subscriptions",
        excludes the "Free" tier from the results.
      - country: if provided and not "All Countries", restricts learners to the
        specified DimUser.country before aggregation.

    The response is a list of objects, each containing:
      - tier: the subscription tier name.
      - count: the number of high-risk learners in that tier.
      - pct: the percentage of high-risk learners this tier represents out of the
        filtered total.

    The percentage is calculated as (tier_count / total_high_risk) * 100.
    """
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
        .join(
            DimUser,
            FactUserAnalyticsSnapshot.user_key == DimUser.user_key,
        )
        .filter(
            FactUserAnalyticsSnapshot.snapshot_date_key == subq_latest_snap.c.latest_key,
            FactUserAnalyticsSnapshot.churn_probability >= risk_threshold,
        )
    )

    if subscription_tier and subscription_tier != "All Subscriptions":
        q = q.filter(DimSubscriptionPlan.tier == subscription_tier)
    else:
        q = q.filter(DimSubscriptionPlan.tier != "Free")

    if country and country != "All Countries":
        q = q.filter(DimUser.country == country)

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
    Retrieve an overview of active and recent campaigns for the table view.

    This endpoint joins CampaignPerformance, DimCampaign, and DimDate tables to
    assemble key campaign metrics. It returns all campaigns, ordered by launch
    date in descending order (most recent first).

    For each campaign, the response includes:
      - campaign: the campaign name.
      - target_segment: the target audience segment (defaults to "Unknown" if null).
      - launch_date: the campaign launch date in ISO format (YYYY-MM-DD), or null
        if unavailable.
      - open_rate_pct: the campaign open rate as a percentage.
      - retention_lift_pct: the retention lift (percentage point improvement over
        control group).
      - status: the current status of the campaign (e.g., Active, Completed, Paused).
    """
    rows = (
        db.query(
            CampaignPerformance.campaign_name.label("campaign_name"),
            CampaignPerformance.target_segment.label("target_segment"),
            DimDate.full_date.label("launch_date"),
            CampaignPerformance.open_rate.label("open_rate"),
            CampaignPerformance.retention_lift.label("retention_lift"),
            CampaignPerformance.status.label("status"),
        )
        .join(DimCampaign, CampaignPerformance.campaign_key == DimCampaign.campaign_key)
        .join(DimDate, DimCampaign.start_date_key == DimDate.date_key)
        .order_by(DimDate.full_date.desc())
        .all()
    )

    result: List[Dict] = []
    for r in rows:
        result.append(
            {
                "campaign": r.campaign_name,
                "target_segment": r.target_segment or "Unknown",
                "launch_date": r.launch_date.isoformat() if r.launch_date else None,
                "open_rate_pct": r.open_rate,
                "retention_lift_pct": r.retention_lift,
                "status": r.status,
            }
        )

    return result



@app.get("/campaigns/performance-comparison")
def get_campaign_performance_comparison(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Retrieve campaign performance metrics for the comparison chart (Lift vs. Churn Rate).

    This endpoint joins CampaignPerformance and DimCampaign tables to extract
    retention rates and lift for each campaign. It calculates the campaign churn
    rate as (100 - campaign_retention_rate) and returns campaigns ordered
    alphabetically by name.

    For each campaign, the response includes:
      - campaign: the campaign name.
      - churn_rate_pct: the calculated churn rate percentage for the campaign group
        (derived as 100 minus campaign_retention_rate).
      - retention_lift_pct: the retention lift (percentage point improvement over
        the control group).

    This endpoint provides data suitable for visualizing the relationship between
    campaign-driven churn reduction and retention lift in a scatter or comparison chart.
    """
    rows = (
        db.query(
            DimCampaign.campaign_name.label("campaign_name"),
            CampaignPerformance.campaign_retention_rate.label(
                "campaign_retention_rate"
            ),
            CampaignPerformance.control_retention_rate.label("control_retention_rate"),
            CampaignPerformance.retention_lift.label("retention_lift"),
        )
        .join(
            CampaignPerformance,
            CampaignPerformance.campaign_key == DimCampaign.campaign_key,
        )
        .order_by(DimCampaign.campaign_name.asc())
        .all()
    )

    result: List[Dict] = []
    for r in rows:
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
    Retrieve the latest model accuracy metric and its change for the accuracy card.

    This endpoint queries the ModelPerformanceMetrics table for the specified
    model_type, selects the two most recent snapshots (ordered by snapshot_date_key
    in descending order), and computes:
      - current_accuracy_pct: the accuracy of the most recent model snapshot,
        converted to a percentage (multiplied by 100).
      - accuracy_change_pct: the absolute percentage point change in accuracy
        from the previous snapshot to the current one. If only one snapshot is
        available, this field is null.

    Query parameters:
      - model_type: the type of model to query (default: "churn_prediction").

    If no performance metrics are available for the specified model_type, both
    fields in the response are null.
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
    Retrieve the latest model precision metric and its change for the precision card.

    This endpoint queries the ModelPerformanceMetrics table for the specified
    model_type, selects the two most recent snapshots (ordered by snapshot_date_key
    in descending order), and computes:
      - current_precision_pct: the precision of the most recent model snapshot,
        converted to a percentage (multiplied by 100).
      - precision_change_pct: the absolute percentage point change in precision
        from the previous snapshot to the current one. If only one snapshot is
        available, this field is null.

    Query parameters:
      - model_type: the type of model to query (default: "churn_prediction").

    If no performance metrics are available for the specified model_type, both
    fields in the response are null.
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
    Retrieve the latest model recall metric and its change for the recall card.

    This endpoint queries the ModelPerformanceMetrics table for the specified
    model_type, selects the two most recent snapshots (ordered by snapshot_date_key
    in descending order), and computes:
      - current_recall_pct: the recall of the most recent model snapshot,
        converted to a percentage (multiplied by 100).
      - recall_change_pct: the absolute percentage point change in recall
        from the previous snapshot to the current one. If only one snapshot is
        available, this field is null.

    Query parameters:
      - model_type: the type of model to query (default: "churn_prediction").

    If no performance metrics are available for the specified model_type, both
    fields in the response are null.
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
    Retrieve the latest model AUC-ROC score and its change for the AUC-ROC card.

    This endpoint queries the ModelPerformanceMetrics table for the specified
    model_type, selects the two most recent snapshots (ordered by snapshot_date_key
    in descending order), and computes:
      - current_auc_roc: the AUC-ROC score of the most recent model snapshot
        (returned as a decimal value, typically between 0 and 1).
      - auc_roc_change: the absolute change in AUC-ROC score from the previous
        snapshot to the current one. If only one snapshot is available, this
        field is null.

    Query parameters:
      - model_type: the type of model to query (default: "churn_prediction").
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
    Retrieve feature importance rankings for the horizontal bar chart.

    This endpoint queries the FeatureImportance table to find the most recent
    snapshot_date_key for the "churn_prediction" model_type, then returns all
    feature importance records from that snapshot, ordered by importance_rank
    in ascending order (most important features first).

    For each feature, the response includes:
      - feature_name: the name of the feature.
      - importance_score: the feature's importance score in the churn model.

    If no feature importance data is available for the churn_prediction model,
    an empty list is returned.
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


# Roc curve
@app.get("/models/roc-curve")
def get_model_roc_curve(
    model_type: str = "churn_prediction",
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Retrieve approximate ROC curve data points for the churn prediction accuracy chart.

    This endpoint queries the ModelPerformanceMetrics table for the most recent
    snapshot of the specified model_type. If an AUC-ROC value is available, it
    generates a synthetic ROC curve by approximating true positive rate (TPR)
    values across false positive rate (FPR) intervals from 0.0 to 1.0 in steps
    of 0.1, using the AUC to shape the curve.

    If no model performance data is available or the AUC-ROC is null, the endpoint
    returns a diagonal baseline curve (TPR = FPR) representing random classifier
    performance.

    Query parameters:
      - model_type: the type of model to query (default: "churn_prediction").

    The response is a list of data points, each containing:
      - fpr: false positive rate (0.0 to 1.0).
      - tpr: true positive rate (0.0 to 1.0).

    This data is suitable for rendering an ROC curve visualization on the frontend.
    """
    latest = (
        db.query(ModelPerformanceMetrics)
        .filter(ModelPerformanceMetrics.model_type == model_type)
        .order_by(desc(ModelPerformanceMetrics.snapshot_date_key))
        .first()
    )
    if not latest or latest.auc_roc is None:
        return [{"fpr": x / 10.0, "tpr": x / 10.0} for x in range(0, 11)]

    auc = latest.auc_roc

    points: List[Dict] = []
    for i in range(0, 11):
        fpr = i / 10.0
        base = fpr ** 0.5
        tpr = min(1.0, max(0.0, base * (2 * auc - 1 + 1)))
        points.append({"fpr": fpr, "tpr": tpr})

    return points


# Segment-retention-probability
@app.get("/models/segment-retention-probability")
def get_segment_retention_probability(
    db: Session = Depends(get_db),
) -> List[Dict]:
    """
    Retrieve segment-wise retention probability for the bar chart.

    This endpoint selects the latest analytics snapshot for each learner, groups
    them by engagement_level (segment), and computes the average retention
    probability for each segment. Retention probability is calculated as
    (1 - churn_probability).

    The response is a list of segments, each containing:
      - segment: the engagement level label (e.g., "Highly Engaged", "At Risk"),
        or "Unknown" if the engagement_level is null.
      - retention_probability_pct: the average retention probability for that
        segment, converted to a percentage (multiplied by 100).

    This data is suitable for visualizing comparative retention rates across
    different learner engagement segments in a bar chart.
    """
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
            func.avg(1.0 - FactUserAnalyticsSnapshot.churn_probability).label(
                "retention_prob"
            ),
        )
        .join(
            subq_latest,
            (FactUserAnalyticsSnapshot.user_key == subq_latest.c.user_key)
            & (
                FactUserAnalyticsSnapshot.snapshot_date_key
                == subq_latest.c.latest_key
            ),
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
    Retrieve an approximate survival curve for expected subscription duration.

    This endpoint computes the average survival_median_time_to_downgrade from
    all records in FactUserAnalyticsSnapshot to estimate the median time (in days)
    until a learner downgrades or churns. If no data is available or the value is
    invalid, it defaults to 180 days (6 months).

    The endpoint then generates a synthetic survival curve over a 24-month period
    (with data points at 0, 3, 6, 9, 12, 15, 18, 21, and 24 months) using an
    exponential decay model based on the median survival time. The survival rate
    at each time point represents the estimated percentage of learners still
    subscribed at that duration.

    The response is a list of time points, each containing:
      - months: the time elapsed in months.
      - survival_rate_pct: the estimated percentage of learners still subscribed
        at that time point (0–100).

    This data is suitable for rendering a survival curve chart showing how
    subscription retention decays over time.
    """
    agg = db.query(
        func.avg(FactUserAnalyticsSnapshot.survival_median_time_to_downgrade)
    ).one()

    raw_value = agg[0]

    if raw_value is None:
        median_days = 180.0
    else:
        try:
            median_days = float(raw_value)
        except (TypeError, ValueError):
            median_days = 180.0

    if median_days <= 0:
        median_days = 180.0

    median_months = median_days / 30.0

    time_points = [0, 3, 6, 9, 12, 15, 18, 21, 24]

    def approx_survival(t_months: float) -> float:
        if t_months <= 0:
            return 1.0

        lam = (0.5) ** (1.0 / median_months)
        s = lam ** t_months
        return max(0.0, min(1.0, s))

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


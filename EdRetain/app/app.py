import os
from datetime import date
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# -------------------------------------------------------------------
# Basic configuration
# -------------------------------------------------------------------

API_BASE_URL = (
    os.getenv("API_BASE_URL")
    or os.getenv("API_URL")
    or "http://api:8000"
)

st.set_page_config(
    page_title="EdRetain Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session-level storage for campaigns created from the UI 
if "created_campaigns" not in st.session_state:
    st.session_state["created_campaigns"] = []
if "show_create_campaign" not in st.session_state:
    st.session_state["show_create_campaign"] = False

# -------------------------------------------------------------------
# Endpoint paths
# -------------------------------------------------------------------

RFM_ENDPOINT_PATH = "/learners/rfm-analysis"
FILTERS_ENDPOINT_PATH = "/learners/filters"

HIGH_RISK_SUMMARY_PATH = "/high-risk/summary"
HIGH_RISK_LEARNERS_PATH = "/high-risk/learners"
HIGH_RISK_REASONS_PATH = "/high-risk/reasons-for-churn"
HIGH_RISK_CHURN_BY_TIER_PATH = "/high-risk/churn-by-tier"

CAMPAIGNS_OVERVIEW_PATH = "/campaigns/overview"
CAMPAIGNS_PERFORMANCE_COMPARISON_PATH = "/campaigns/performance-comparison"

MODELS_ACCURACY_PATH = "/models/accuracy"
MODELS_PRECISION_PATH = "/models/precision"
MODELS_RECALL_PATH = "/models/recall"
MODELS_AUC_ROC_PATH = "/models/auc-roc"
MODELS_FEATURE_IMPORTANCE_PATH = "/models/feature-importance"
MODELS_SEGMENT_RETENTION_PATH = "/models/segment-retention-probability"
MODELS_SURVIVAL_CURVE_PATH = "/models/survival-curve"
MODELS_ROC_CURVE_PATH = "/models/roc-curve"

DASH_ACTIVE_PREMIUM_PATH = "/dashboard/active-premium-learners"
DASH_AT_RISK_PATH = "/dashboard/at-risk-learners"
DASH_AVG_RETENTION_PATH = "/dashboard/average-retention-rate"
DASH_TREND_PATH = "/dashboard/retention-churn-trend"
DASH_SEGMENTATION_PATH = "/dashboard/learner-segmentation"
DASH_TOP_FEATURES_PATH = "/dashboard/top-features-driving-churn"


# -------------------------------------------------------------------
# API helper
# -------------------------------------------------------------------

def api_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    error_prefix: Optional[str] = None,
) -> Optional[Any]:
    """
    Send a GET request to the backend and return the decoded JSON response.

    Parameters
    ----------
    path:
        Relative endpoint path (e.g. "/dashboard/active-premium-learners").
    params:
        Optional query parameters to include in the request.
    error_prefix:
        Short text used in the error message if the call fails.

    Returns
    -------
    obj or None
        Parsed JSON object (dict or list) on success, otherwise None.
    """
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json() or {}
    except Exception as exc:
        label = error_prefix or f"Could not load data from {path}"
        st.error(f"{label}: {exc}")
        return None


# -------------------------------------------------------------------
# Fetch helpers (convert API JSON to DataFrames / dicts)
# -------------------------------------------------------------------

def fetch_active_premium_learners() -> Dict[str, Any]:
    """
    Retrieve the latest active premium learners KPIs for the dashboard.
    """
    data = api_get(DASH_ACTIVE_PREMIUM_PATH, error_prefix="Could not load Active Premium Learners")
    return data or {}


def fetch_at_risk_learners_card() -> Dict[str, Any]:
    """
    Retrieve the latest at-risk learners KPIs for the dashboard.
    """
    data = api_get(DASH_AT_RISK_PATH, error_prefix="Could not load At-Risk Learners")
    return data or {}


def fetch_average_retention_rate_card() -> Dict[str, Any]:
    """
    Retrieve the latest average retention rate KPIs for the dashboard.
    """
    data = api_get(DASH_AVG_RETENTION_PATH, error_prefix="Could not load Average Retention Rate")
    return data or {}


def fetch_retention_churn_trend() -> pd.DataFrame:
    """
    Retrieve and prepare the retention/churn trend data for the line chart.
    """
    data = api_get(DASH_TREND_PATH, error_prefix="Could not load retention/churn trend")
    if not isinstance(data, list) or not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.rename(
        columns={
            "month_name": "Month",
            "retention_rate": "Retention (%)",
            "churn_rate": "Churn (%)",
            "monthly_retention_rate": "Retention (%)",
            "monthly_churn_rate": "Churn (%)",
        }
    )
    keep_cols = [c for c in ["Month", "Retention (%)", "Churn (%)"] if c in df.columns]
    return df[keep_cols]


def fetch_learner_segmentation_dashboard() -> pd.DataFrame:
    """
    Retrieve segmentation data for the dashboard donut chart and normalize labels.
    """
    data = api_get(DASH_SEGMENTATION_PATH, error_prefix="Could not load learner segmentation")
    if not isinstance(data, dict) or not data:
        return pd.DataFrame()

    mapping = {
        "highly_engaged": "Highly Engaged",
        "medium_engaged": "Medium Engaged",
        "at_risk": "At-Risk",
        "dormant": "Dormant",
    }
    rows: List[Dict[str, Any]] = []
    for key, val in data.items():
        label = mapping.get(key, key)
        pct = (val or {}).get("pct")
        rows.append({"Segment": label, "Percentage": pct})
    return pd.DataFrame(rows)


def fetch_top_features_dashboard() -> pd.DataFrame:
    """
    Retrieve feature importance for churn drivers used on the main dashboard.
    """
    data = api_get(DASH_TOP_FEATURES_PATH, error_prefix="Could not load top features driving churn")
    if not isinstance(data, list) or not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return df.rename(
        columns={
            "feature_name": "Feature",
            "importance_score": "Impact",
        }
    )


def fetch_rfm_learners(
    country: Optional[str] = None,
    subscription_tier: Optional[str] = None,
) -> pd.DataFrame:
    """
    Retrieve learner-level RFM and churn data with optional filters.

    Parameters
    ----------
    country:
        Country filter, or None / "All Countries" for no restriction.
    subscription_tier:
        Subscription tier filter, or None / "All" for no restriction.

    Returns
    -------
    DataFrame
        One row per learner with RFM, CLV, and churn information.
    """
    params: Dict[str, Any] = {}
    if country and country != "All Countries":
        params["country"] = country
    if subscription_tier and subscription_tier != "All":
        params["subscription_tier"] = subscription_tier

    data = api_get(RFM_ENDPOINT_PATH, params=params, error_prefix="Could not load RFM data from API")
    if data is None:
        return pd.DataFrame()

    if isinstance(data, dict):
        data = data.get("learners", data.get("items", [])) or []

    if not isinstance(data, list):
        st.error("Unexpected response format from RFM endpoint.")
        return pd.DataFrame()

    return pd.DataFrame(data)


def fetch_learners_filters() -> Dict[str, List[str]]:
    """
    Retrieve available country and subscription tier values for filter widgets.
    """
    data = api_get(FILTERS_ENDPOINT_PATH, error_prefix="Could not load filter values from API")
    if not isinstance(data, dict):
        return {"countries": [], "subscription_tiers": []}

    countries = [str(c) for c in (data.get("countries") or [])]
    tiers = [str(t) for t in (data.get("subscription_tiers") or [])]

    return {
        "countries": countries,
        "subscription_tiers": tiers,
    }


def fetch_high_risk_summary(
    risk_threshold: float,
    subscription_tier: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve aggregate statistics for the high-risk learners header cards.
    """
    params: Dict[str, Any] = {"risk_threshold": risk_threshold}
    if subscription_tier and subscription_tier != "All Subscriptions":
        params["subscription_tier"] = subscription_tier
    if country and country != "All Countries":
        params["country"] = country

    data = api_get(HIGH_RISK_SUMMARY_PATH, params=params, error_prefix="Could not load high-risk summary from API")
    return data or {}


def fetch_high_risk_learners(
    risk_threshold: float,
    subscription_tier: Optional[str] = None,
    country: Optional[str] = None,
) -> pd.DataFrame:
    """
    Retrieve detailed high-risk learner records for the At-Risk table.
    """
    params: Dict[str, Any] = {"risk_threshold": risk_threshold}
    if subscription_tier and subscription_tier != "All Subscriptions":
        params["subscription_tier"] = subscription_tier
    if country and country != "All Countries":
        params["country"] = country

    data = api_get(HIGH_RISK_LEARNERS_PATH, params=params, error_prefix="Could not load high-risk learners from API")
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_reasons_for_churn() -> pd.DataFrame:
    """
    Retrieve aggregated churn reasons for the bar chart on the At-Risk page.
    """
    data = api_get(HIGH_RISK_REASONS_PATH, error_prefix="Could not load reasons for churn from API")
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_churn_by_tier(
    risk_threshold: float,
    subscription_tier: Optional[str] = None,
    country: Optional[str] = None,
) -> pd.DataFrame:
    """
    Retrieve distribution of high-risk learners by subscription tier.
    """
    params: Dict[str, Any] = {"risk_threshold": risk_threshold}
    if subscription_tier and subscription_tier != "All Subscriptions":
        params["subscription_tier"] = subscription_tier
    if country and country != "All Countries":
        params["country"] = country

    data = api_get(HIGH_RISK_CHURN_BY_TIER_PATH, params=params, error_prefix="Could not load churn-by-tier data from API")
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_campaigns_overview() -> pd.DataFrame:
    """
    Retrieve campaign overview data (including launch date, status, and impact).
    """
    data = api_get(CAMPAIGNS_OVERVIEW_PATH, error_prefix="Could not load campaign overview from API")
    if not isinstance(data, list):
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return df.rename(
        columns={
            "campaign": "Campaign",
            "target_segment": "Target Segment",
            "launch_date": "Launch Date",
            "open_rate_pct": "Open Rate (%)",
            "retention_lift_pct": "Retention Lift (%)",
            "status": "Status",
        }
    )


def fetch_campaigns_performance_comparison() -> pd.DataFrame:
    """
    Retrieve campaign performance metrics for the grouped bar chart.
    """
    data = api_get(
        CAMPAIGNS_PERFORMANCE_COMPARISON_PATH,
        error_prefix="Could not load campaign performance data from API",
    )
    if not isinstance(data, list):
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return df.rename(
        columns={
            "campaign": "Campaign",
            "churn_rate_pct": "Churn Rate (%)",
            "retention_lift_pct": "Retention Lift (%)",
        }
    )


def fetch_model_accuracy() -> Dict[str, Any]:
    """
    Retrieve current and delta accuracy values for the model metrics card.
    """
    data = api_get(MODELS_ACCURACY_PATH, error_prefix="Could not load model accuracy from API")
    return data or {}


def fetch_model_precision() -> Dict[str, Any]:
    """
    Retrieve current and delta precision values for the model metrics card.
    """
    data = api_get(MODELS_PRECISION_PATH, error_prefix="Could not load model precision from API")
    return data or {}


def fetch_model_recall() -> Dict[str, Any]:
    """
    Retrieve current and delta recall values for the model metrics card.
    """
    data = api_get(MODELS_RECALL_PATH, error_prefix="Could not load model recall from API")
    return data or {}


def fetch_model_auc_roc() -> Dict[str, Any]:
    """
    Retrieve the latest AUC-ROC summary value for the model metrics card.
    """
    data = api_get(MODELS_AUC_ROC_PATH, error_prefix="Could not load model AUC-ROC from API")
    return data or {}


def fetch_feature_importance() -> pd.DataFrame:
    """
    Retrieve detailed feature importance data for the Analytics page.
    """
    data = api_get(MODELS_FEATURE_IMPORTANCE_PATH, error_prefix="Could not load feature importance from API")
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_segment_retention_probability() -> pd.DataFrame:
    """
    Retrieve average retention probability by engagement segment.
    """
    data = api_get(
        MODELS_SEGMENT_RETENTION_PATH,
        error_prefix="Could not load segment retention probability from API",
    )
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_survival_curve() -> pd.DataFrame:
    """
    Retrieve the approximated survival curve for subscription duration.
    """
    data = api_get(MODELS_SURVIVAL_CURVE_PATH, error_prefix="Could not load survival curve from API")
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_model_roc_curve() -> pd.DataFrame:
    """
    Retrieve ROC curve points (FPR/TPR) for the Analytics page.
    """
    data = api_get(MODELS_ROC_CURVE_PATH, error_prefix="Could not load ROC curve from API")
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


# -------------------------------------------------------------------
# Small UI helper
# -------------------------------------------------------------------

def get_kpi_card(title: str, value: str) -> None:
    """
    Render a simple KPI card with a title and a large numeric value.
    """
    with st.container(border=True):
        st.markdown(
            f"<p style='font-size: 14px; color: #555;'>{title}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(f"## {value}")


# -------------------------------------------------------------------
# Pages
# -------------------------------------------------------------------

def dashboard_page() -> None:
    """
    Render the main dashboard page with KPIs, trend chart, segmentation,
    and key drivers of churn.
    """
    st.title("EdRetain Dashboard")
    st.markdown("---")

    # KPI row
    active = fetch_active_premium_learners()
    at_risk = fetch_at_risk_learners_card()
    avg_ret = fetch_average_retention_rate_card()

    active_val = active.get("active_premium_learners")
    risk_val = at_risk.get("at_risk_learners")
    ret_val = avg_ret.get("average_retention_rate")

    col1, col2, col3 = st.columns(3)
    with col1:
        get_kpi_card("Active Premium Learners", "—" if active_val is None else f"{active_val:,}")
    with col2:
        get_kpi_card("At-Risk Learners", "—" if risk_val is None else f"{risk_val:,}")
    with col3:
        get_kpi_card(
            "Average Retention Rate",
            "—" if ret_val is None else f"{ret_val:.1f}%",
        )

    st.markdown("---")
    chart_col1, chart_col2 = st.columns([3, 2])

    # Retention / Churn trend
    with chart_col1:
        st.subheader("Retention and Churn Trend Over Time")
        trend_df = fetch_retention_churn_trend()
        if trend_df.empty:
            st.info("No trend data available.")
        else:
            df_melt = trend_df.melt("Month", var_name="Metric", value_name="Value")
            fig = px.line(
                df_melt,
                x="Month",
                y="Value",
                color="Metric",
            )
            fig.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0})
            st.plotly_chart(fig, use_container_width=True)

    # Segmentation donut
    with chart_col2:
        st.subheader("Learner Segmentation by Engagement Level")
        seg_df = fetch_learner_segmentation_dashboard()
        if seg_df.empty:
            st.info("No segmentation data available.")
        else:
            fig = px.pie(
                seg_df,
                values="Percentage",
                names="Segment",
                hole=0.5,
            )
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(
                height=400,
                margin={"t": 0, "b": 0, "l": 0, "r": 0},
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Top Features Driving Churn")

    features_df = fetch_top_features_dashboard()
    if features_df.empty:
        st.info("No feature importance data available.")
    else:
        if "Impact" in features_df.columns:
            features_df = features_df.nlargest(5, "Impact")
            features_df = features_df.sort_values("Impact", ascending=True)

        fig = px.bar(
            features_df,
            x="Impact",
            y="Feature",
            orientation="h",
            labels={"Impact": "Relative Impact Score"},
        )
        fig.update_layout(height=300, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        st.plotly_chart(fig, use_container_width=True)


def learners_page() -> None:
    """
    Render the Learners page with RFM analysis, K-Means segments,
    and churn-oriented views.
    """
    st.title("👤 Learners")
    st.header("Learner Segmentation Explorer")

    filters = fetch_learners_filters()
    country_options = ["All Countries"] + sorted(filters["countries"])
    tier_options = ["All"] + sorted(filters["subscription_tiers"])

    st.markdown("---")
    col1, col2, _ = st.columns([1, 1, 3])

    with col1:
        country = st.selectbox("Country", country_options)
    with col2:
        subscription_tier = st.selectbox("Subscription Tier", tier_options)

    rfm_raw = fetch_rfm_learners(
        country=country,
        subscription_tier=subscription_tier,
    )

    if rfm_raw.empty:
        st.warning("No learners returned for the selected filters.")
        return

    # Align backend columns to UI names
    rfm_df = rfm_raw.rename(
        columns={
            "user_id": "User ID",
            "country": "Country",
            "segment_label": "Segment",
            "kmeans_segment_label": "KMeans Segment",
            "rfm_segment": "RFM Score",
            "clv": "CLV ($)",
            "churn_risk_pct": "Churn Risk (%)",
            "last_active_days_ago": "Last Active",
        }
    )

    for col_name in ["RFM Score", "CLV ($)", "Churn Risk (%)"]:
        if col_name in rfm_df.columns:
            rfm_df[col_name] = pd.to_numeric(rfm_df[col_name], errors="coerce")

    tab1, tab2, tab3 = st.tabs(
        ["RFM Analysis", "K-Means Segmentation", "Churn Prediction"]
    )

    # Tab 1: RFM
    with tab1:
        st.subheader("RFM Analysis: Behavioral View")
        display_cols = [
            "User ID",
            "Country",
            "Segment",
            "RFM Score",
            "CLV ($)",
            "Churn Risk (%)",
            "Last Active",
        ]
        existing_cols = [c for c in display_cols if c in rfm_df.columns]
        st.caption(f"Rows shown: {len(rfm_df)}")
        st.dataframe(
            rfm_df[existing_cols],
            use_container_width=True,
            hide_index=True,
        )

    # Tab 2: K-Means
    with tab2:
        st.subheader("K-Means Segmentation Overview")
        if "KMeans Segment" not in rfm_df.columns:
            st.info("K-Means segment information is not available.")
        else:
            seg_df = rfm_df.copy()
            summary = (
                seg_df.groupby("KMeans Segment")
                .agg(
                    Learners=("User ID", "nunique"),
                    Avg_RFM=("RFM Score", "mean"),
                    Avg_CLV=("CLV ($)", "mean"),
                    Avg_Churn_Risk=("Churn Risk (%)", "mean"),
                )
                .reset_index()
                .sort_values("Learners", ascending=False)
            )
            summary = summary.rename(columns={"KMeans Segment": "Segment"})
            for col in ["Avg_RFM", "Avg_CLV", "Avg_Churn_Risk"]:
                if col in summary.columns:
                    summary[col] = summary[col].round(2)

            st.dataframe(summary, use_container_width=True, hide_index=True)

            st.markdown("**Learners per Segment**")
            chart_data = summary.set_index("Segment")[["Learners"]]
            st.bar_chart(chart_data)

    # Tab 3: Churn prediction
    with tab3:
        st.subheader("Churn Prediction View")
        if "Churn Risk (%)" not in rfm_df.columns:
            st.info("Churn risk information is not available.")
        else:
            cp_df = rfm_df.copy()
            cp_df["Churn Risk (%)"] = pd.to_numeric(
                cp_df["Churn Risk (%)"], errors="coerce"
            )

            max_risk = cp_df["Churn Risk (%)"].max()
            if pd.isna(max_risk):
                threshold = None
            elif max_risk <= 1.0 + 1e-6:
                threshold = 0.7
            else:
                threshold = 70.0

            if threshold is not None:
                cp_df["Predicted Status"] = np.where(
                    cp_df["Churn Risk (%)"] >= threshold,
                    "High risk",
                    "Lower risk",
                )
            else:
                cp_df["Predicted Status"] = "Unknown"

            cp_df = cp_df.sort_values("Churn Risk (%)", ascending=False)

            cols_to_show = [
                c
                for c in [
                    "User ID",
                    "Country",
                    "Segment",
                    "Churn Risk (%)",
                    "Predicted Status",
                    "Last Active",
                ]
                if c in cp_df.columns
            ]
            st.markdown("**Top learners by predicted churn risk**")
            st.dataframe(
                cp_df[cols_to_show].head(50),
                use_container_width=True,
                hide_index=True,
            )


def at_risk_page() -> None:
    """
    Render the At-Risk page with header KPIs, detailed learner table,
    churn reasons, and churn-by-tier distribution.
    """
    st.title("🚨 At-Risk")
    st.header("High-Risk Learners")

    filters = fetch_learners_filters()
    country_options = ["All Countries"] + sorted(filters["countries"])
    tier_options = ["All Subscriptions"] + sorted(filters["subscription_tiers"])

    st.markdown("---")
    col_filter1, col_filter2, col_filter3 = st.columns([1.5, 2, 2.5])

    risk_options = {
        "> 70% Risk": 0.70,
        "> 50% Risk": 0.50,
        "> 30% Risk": 0.30,
    }

    with col_filter1:
        risk_label = st.selectbox(
            "Risk Threshold",
            list(risk_options.keys()),
            label_visibility="collapsed",
        )
    risk_threshold = risk_options[risk_label]

    with col_filter2:
        subscription_tier = st.selectbox(
            "Subscription Tier",
            tier_options,
            label_visibility="collapsed",
        )
    with col_filter3:
        country = st.selectbox(
            "Country",
            country_options,
            label_visibility="collapsed",
        )

    summary = fetch_high_risk_summary(
        risk_threshold=risk_threshold,
        subscription_tier=subscription_tier,
        country=country,
    )
    learners_df = fetch_high_risk_learners(
        risk_threshold=risk_threshold,
        subscription_tier=subscription_tier,
        country=country,
    )
    reasons_df = fetch_reasons_for_churn()
    churn_tier_df = fetch_churn_by_tier(
        risk_threshold=risk_threshold,
        subscription_tier=subscription_tier,
        country=country,
    )

    total_high_risk = summary.get("total_high_risk_learners", 0)
    new_high_risk = summary.get("new_high_risk_recent", 0)

    st.markdown(
        """
        <style>
        .kpi-container {
            display: flex;
            align-items: center;
            gap: 20px;
            padding-bottom: 20px;
        }
        .kpi-main {
            font-size: 2.5rem;
            font-weight: 600;
            color: #e59c00;
        }
        .kpi-text-line1 {
            margin: 0;
            padding: 0;
            font-size: 0.9rem;
            color: #555;
        }
        .kpi-text-line2 {
            margin: 0;
            padding: 0;
            font-size: 0.9rem;
            color: #e59c00;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-main">{total_high_risk}</div>
            <div>
                <p class="kpi-text-line1">Total high-risk learners (above selected threshold)</p>
                <p class="kpi-text-line2">⬆️ {new_high_risk} new learners moved into high-risk this week.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    chart_col1, chart_col2 = st.columns([2, 1])

    # Table of high-risk learners
    with chart_col1:
        st.subheader("High-Risk Learner List")
        if learners_df.empty:
            st.info("No high-risk learners for the selected filters.")
        else:
            display_df = learners_df.rename(
                columns={
                    "name": "User ID",
                    "segment": "Segment",
                    "days_inactive": "Days Inactive",
                    "churn_probability": "Churn Probability",
                    "suggested_action": "Action",
                }
            )
            if "Churn Probability" in display_df.columns:
                display_df["Churn Probability"] = pd.to_numeric(
                    display_df["Churn Probability"], errors="coerce"
                )
                max_val = display_df["Churn Probability"].max()
                if pd.notna(max_val) and max_val <= 1.0 + 1e-6:
                    display_df["Churn Probability"] = (
                        display_df["Churn Probability"] * 100.0
                    ).round(1)

            cols_to_show = [
                "User ID",
                "Segment",
                "Days Inactive",
                "Churn Probability",
                "Action",
            ]
            cols_to_show = [c for c in cols_to_show if c in display_df.columns]

            st.data_editor(
                display_df[cols_to_show],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Action": st.column_config.TextColumn(
                        "Action",
                        help="Recommended campaign action for this learner",
                        width="medium",
                    )
                },
                disabled=[
                    "User ID",
                    "Segment",
                    "Days Inactive",
                    "Churn Probability",
                ],
            )

    # Reasons + Churn by tier charts
    with chart_col2:
        st.subheader("Reasons for Churn")
        if reasons_df.empty:
            st.info("No churn reason data available.")
        else:
            reasons_df = reasons_df.rename(
                columns={"reason": "Reason", "count": "Count"}
            )
            fig_reasons = px.bar(
                reasons_df,
                x="Reason",
                y="Count",
            )
            fig_reasons.update_layout(
                height=250,
                margin={"t": 10, "b": 50, "l": 0, "r": 0},
                xaxis={"categoryorder": "total descending"},
            )
            st.plotly_chart(fig_reasons, use_container_width=True)

        st.subheader("Churn by Tier")
        if churn_tier_df.empty:
            st.info("No churn-by-tier data available.")
        else:
            churn_tier_df = churn_tier_df.rename(
                columns={
                    "tier": "Tier",
                    "count": "Count",
                    "pct": "Percentage",
                }
            )
            fig_pie = px.pie(
                churn_tier_df,
                values="Count",
                names="Tier",
                hole=0.5,
            )
            fig_pie.update_traces(textinfo="percent+label")
            fig_pie.update_layout(
                height=250,
                margin={"t": 10, "b": 0, "l": 0, "r": 0},
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)


def campaigns_page() -> None:
    """
    Render the Campaigns page with an editable table and performance comparison.
    """
    st.title("📢 Campaigns")
    st.header("Retention Campaigns Overview")

    st.markdown("---")
    _, col2 = st.columns([4, 1])
    with col2:
        create_clicked = st.button("✨ Create New Campaign", use_container_width=True)

    if create_clicked:
        st.session_state["show_create_campaign"] = not st.session_state["show_create_campaign"]

    if st.session_state["show_create_campaign"]:
        st.subheader("Create New Campaign")
        with st.form("create_campaign_form"):
            campaign_name = st.text_input("Campaign name")
            target_segment = st.selectbox(
                "Target segment",
                ["At-Risk", "Dormant", "Highly Engaged", "Medium", "All"],
            )
            launch_date = st.date_input("Launch date", value=date.today())
            status = st.selectbox("Status", ["Planned", "Active"])

            submitted = st.form_submit_button("Add to table")
            if submitted:
                if not campaign_name:
                    st.error("Please enter a campaign name.")
                else:
                    new_row = {
                        "Campaign": campaign_name,
                        "Target Segment": target_segment,
                        "Launch Date": launch_date,
                        "Open Rate (%)": 0.0,
                        "Retention Lift (%)": 0.0,
                        "ROI (%)": 0.0,
                        "Status": status,
                    }
                    st.session_state["created_campaigns"].append(new_row)
                    st.session_state["show_create_campaign"] = False
                    st.success("Campaign added to table (not saved to database).")

    st.markdown("---")

    campaigns_df = fetch_campaigns_overview()
    if campaigns_df.empty and not st.session_state["created_campaigns"]:
        st.info("No campaign overview data available.")
    else:
        if st.session_state["created_campaigns"]:
            extra_df = pd.DataFrame(st.session_state["created_campaigns"])
            if campaigns_df.empty:
                campaigns_df = extra_df
            else:
                campaigns_df = pd.concat([campaigns_df, extra_df], ignore_index=True)

        st.subheader("Active & Recent Campaigns")
        st.dataframe(campaigns_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    comparison_df = fetch_campaigns_performance_comparison()
    st.subheader("Campaign Performance Comparison (Lift vs. Churn Rate)")

    if comparison_df.empty:
        st.info("No campaign performance data available.")
    else:
        needed_cols = ["Campaign", "Churn Rate (%)", "Retention Lift (%)"]
        missing = [c for c in needed_cols if c not in comparison_df.columns]
        if missing:
            st.error(f"Missing columns in comparison data: {missing}")
        else:
            fig = px.bar(
                comparison_df,
                x="Campaign",
                y=["Churn Rate (%)", "Retention Lift (%)"],
                barmode="group",
            )
            fig.update_layout(
                yaxis_title="Rate (%)",
                height=400,
                margin={"t": 0, "b": 0, "l": 0, "r": 0},
            )
            st.plotly_chart(fig, use_container_width=True)


def analytics_page() -> None:
    """
    Render the Analytics page with model performance indicators,
    feature importance, ROC curve, segment retention, and survival curve.
    """
    st.title("📈 Analytics")
    st.header("Predictive Insights")

    st.markdown("---")

    acc = fetch_model_accuracy()
    prec = fetch_model_precision()
    rec = fetch_model_recall()
    auc = fetch_model_auc_roc()

    acc_val = acc.get("current_accuracy_pct")
    prec_val = prec.get("current_precision_pct")
    rec_val = rec.get("current_recall_pct")
    auc_val = auc.get("current_auc_roc")

    def fmt_pct(x: Optional[float]) -> str:
        return f"{x:.1f}%" if x is not None else "—"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Model Accuracy", fmt_pct(acc_val))
    with col2:
        st.metric("Precision", fmt_pct(prec_val))
    with col3:
        st.metric("Recall", fmt_pct(rec_val))
    with col4:
        auc_main = f"{auc_val:.3f}" if auc_val is not None else "—"
        st.metric("AUC-ROC Score", auc_main)

    st.markdown("---")
    chart_col1, chart_col2 = st.columns([3, 2])

    # Feature importance
    with chart_col1:
        st.subheader("Feature Importance")
        fi_df = fetch_feature_importance()
        if fi_df.empty:
            st.info("No feature importance data from API.")
        else:
            fi_df = fi_df.rename(
                columns={
                    "feature_name": "Feature",
                    "importance_score": "Importance",
                }
            )
            if "Importance" in fi_df.columns:
                fi_df["Importance"] = pd.to_numeric(fi_df["Importance"], errors="coerce")

            fig_fi = px.bar(
                fi_df.sort_values("Importance"),
                x="Importance",
                y="Feature",
                orientation="h",
            )
            fig_fi.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0})
            st.plotly_chart(fig_fi, use_container_width=True)

    # ROC curve
    with chart_col2:
        st.subheader("Churn Prediction Accuracy (ROC Curve)")
        roc_df = fetch_model_roc_curve()
        if roc_df.empty:
            st.info("No ROC data from API.")
        else:
            roc_df = roc_df.rename(
                columns={
                    "fpr": "False Positive Rate",
                    "tpr": "True Positive Rate",
                }
            )
            fig_roc = px.line(
                roc_df,
                x="False Positive Rate",
                y="True Positive Rate",
            )
            fig_roc.add_shape(
                type="line",
                line=dict(dash="dash"),
                x0=0,
                y0=0,
                x1=1,
                y1=1,
            )
            fig_roc.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0})
            st.plotly_chart(fig_roc, use_container_width=True)

    st.markdown("---")
    bottom_col1, bottom_col2 = st.columns(2)

    # Segment retention
    with bottom_col1:
        st.subheader("Segment-wise Retention Probability")
        seg_df = fetch_segment_retention_probability()
        if seg_df.empty:
            st.info("No segment retention data from API.")
        else:
            seg_df = seg_df.rename(
                columns={
                    "segment": "Segment",
                    "retention_probability_pct": "Probability (%)",
                }
            )
            if "Probability (%)" in seg_df.columns:
                seg_df["Probability (%)"] = pd.to_numeric(
                    seg_df["Probability (%)"], errors="coerce"
                )

            all_segments = sorted(seg_df["Segment"].dropna().unique().tolist())
            segment_filter = st.selectbox(
                "Filter by segment",
                options=["All Segments"] + all_segments,
                index=0,
            )

            seg_plot_df = seg_df.copy()
            if segment_filter != "All Segments":
                seg_plot_df = seg_plot_df[seg_plot_df["Segment"] == segment_filter]

            fig_seg = px.bar(
                seg_plot_df,
                x="Segment",
                y="Probability (%)",
            )
            fig_seg.update_layout(height=300, margin={"t": 0, "b": 0, "l": 0, "r": 0})
            st.plotly_chart(fig_seg, use_container_width=True)

    # Survival curve
    with bottom_col2:
        st.subheader("Survival Curve (Expected Subscription Duration)")
        surv_df = fetch_survival_curve()
        if surv_df.empty:
            st.info("No survival data from API.")
        else:
            surv_df = surv_df.rename(
                columns={
                    "months": "Months",
                    "survival_rate_pct": "Survival Rate (%)",
                }
            )
            fig_surv = px.area(
                surv_df,
                x="Months",
                y="Survival Rate (%)",
                line_shape="hvh",
            )
            fig_surv.update_layout(height=300, margin={"t": 0, "b": 0, "l": 0, "r": 0})
            st.plotly_chart(fig_surv, use_container_width=True)


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------

def main() -> None:
    """
    Define the sidebar navigation and route to the selected page.
    """
    st.sidebar.image("https://placehold.co/100x30/007bff/white?text=EdRetain")
    st.sidebar.markdown("## EdRetain Dashboard")

    page = st.sidebar.radio(
        "Navigation",
        options=["Dashboard", "Learners", "At-Risk", "Campaigns", "Analytics"],
        index=0,
    )
    st.sidebar.markdown("---")

    if page == "Dashboard":
        dashboard_page()
    elif page == "Learners":
        learners_page()
    elif page == "At-Risk":
        at_risk_page()
    elif page == "Campaigns":
        campaigns_page()
    elif page == "Analytics":
        analytics_page()


if __name__ == "__main__":
    main()

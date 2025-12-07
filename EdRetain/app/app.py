import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

# --- Configuration and Setup ---
# Set the page configuration to use a wide layout
st.set_page_config(
    page_title="EdRetain Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Utility Functions for Mock Data (to represent the charts and tables) ---

def get_kpi_card(title, value, delta, color='inverse'):
    """Creates a stylized KPI metric card."""
    with st.container(border=True):
        st.markdown(f"<p style='font-size: 14px; color: #555;'>{title}</p>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        col1.markdown(f"## {value}")
        col2.metric(label="", value=f"{delta}", delta_color=color, delta=delta)

def generate_mock_data():
    """Generates all necessary mock dataframes."""
    np.random.seed(42)

    # Dashboard Data
    dates = pd.date_range(start="2024-01-01", periods=6, freq='M').strftime('%b')
    retention_churn_df = pd.DataFrame({
        'Month': dates,
        'Retention (%)': np.random.randint(70, 95, 6),
        'Churn (%)': np.random.randint(5, 30, 6)
    })
    top_features_df = pd.DataFrame({
        'Feature': ['Inactivity Days', 'Course Completion', 'Login Frequency', 'Payment Issues', 'Support Tickets'],
        'Impact': np.sort(np.random.randint(30, 100, 5))[::-1]
    })
    segmentation_data = pd.DataFrame({
        'Segment': ['Highly Engaged', 'Medium Engaged', 'At-Risk', 'Dormant'],
        'Percentage': [45, 30, 10, 15]
    })

    # Learners/Risk Data - Updated to match prototype names and values for high-risk users
    learner_data = pd.DataFrame({
        'Name': ['John Doe', 'Aram Hakobyan', 'Sarah South', 'Maria Garcia', 'Lilit Petrosyan', 'David Chen',
                 'Lisa Anderson', 'Tigran Sargsyan', 'Emma Wilson', 'Davit Avetisyan'],
        'Country': ['USA', 'Armenia', 'USA', 'Spain', 'Armenia', 'China', 'USA', 'Armenia', 'USA', 'Armenia'],
        'Segment': ['At-Risk', 'Dormant', 'Highly Engaged', 'Medium Engaged', 'Dormant', 'Highly Engaged',
                    'At-Risk', 'Dormant', 'At-Risk', 'Dormant'],
        'RFM Score': [320, 280, 512, 398, 180, 495, 300, 250, 310, 200],
        'CLV ($)': [1840, 1500, 3200, 2100, 890, 2780, 1700, 1200, 1900, 1000],
        'Churn Risk (%)': [85, 90, 5, 25, 88, 12, 78, 88, 72, 93],
        'Days Inactive': [15, 23, 0, 7, 25, 0, 12, 18, 9, 25],
        'Last Active': ['15 days ago', '23 days ago', '1 hour ago', '7 days ago', '25 days ago', '2 hours ago',
                        '12 days ago', '18 days ago', '9 days ago', '25 days ago'],
        # Initialize Actions as lists of strings for the multiselect column
        'Action': [['Email', 'Discount']] * 10
    })

    # Campaigns Data
    campaign_df = pd.DataFrame({
        'Campaign': ['Re-engagement Email', 'Discount Offer', 'Feature Announcement', 'Course Completion Bonus', 'Feedback Survey'],
        'Target Segment': ['At-Risk', 'Dormant', 'Highly Engaged', 'Medium', 'All'],
        'Launch Date': pd.to_datetime(['2024-10-15', '2024-11-01', '2024-10-20', '2024-09-25', '2024-10-05']),
        'Open Rate (%)': [42, 38, 65, 51, 48],
        'Retention Lift (%)': [8.5, 12.0, 3.5, 9.0, 5.0],
        'ROI (%)': [250, 320, 180, 220, 120],
        'Status': ['Completed', 'Completed', 'Completed', 'Completed', 'Active']
    })
    comparison_df = pd.DataFrame({
        'Campaign': ['Re-engagement', 'Discount', 'Feature', 'Completion'],
        'Churn Rate (%)': [41, 39, 62, 50],
        'Retention Lift (%)': [8, 12, 4, 10]
    })

    # Analytics Data
    analytics_df = pd.DataFrame({
        'Feature': ['Support Tickets', 'Feature Usage', 'Time on Platform', 'Login Frequency', 'Course Completion Rate', 'Days Since Last Login'],
        'Importance': np.sort(np.random.uniform(0.5, 5.0, 6))[::-1]
    })
    retention_prob_df = pd.DataFrame({
        'Segment': ['Highly Engaged', 'Medium', 'At Risk', 'Dormant'],
        'Probability (%)': [92, 75, 35, 15]
    })

    return retention_churn_df, top_features_df, segmentation_data, learner_data, campaign_df, comparison_df, analytics_df, retention_prob_df

# --- Page Content Functions ---

def get_kpi_card(title, value, delta, color='inverse'):
    """Creates a stylized KPI metric card."""
    with st.container(border=True):
        st.markdown(f"<p style='font-size: 14px; color: #555;'>{title}</p>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        col1.markdown(f"## {value}")
        col2.metric(label="", value=f"{delta}", delta_color=color, delta=delta)

def dashboard_page(data):
    """
    Renders the main Dashboard page (Page 1 of prototype).
    """
    st.title("EdRetain Dashboard")

    # 1. KPI Row
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        get_kpi_card("Active Premium Learners", "2,847", "12% from last month", 'inverse')
    with col2:
        get_kpi_card("At-Risk Learners", "342", "↑ 8 new this week", 'inverse')
    with col3:
        get_kpi_card("Average Retention Rate", "80.5%", "↓ 2.2% from last month", 'inverse') 

    # 2. Main Charts Row
    st.markdown("---")
    chart_col1, chart_col2 = st.columns([3, 2])

    # Retention and Churn Trend Over Time
    with chart_col1:
        st.subheader("Retention and Churn Trend Over Time")
        df_melt = data['retention_churn_df'].melt('Month', var_name='Metric', value_name='Value')
        fig = px.line(df_melt, x='Month', y='Value', color='Metric',
                      color_discrete_map={'Retention (%)': 'darkgreen', 'Churn (%)': 'lightcoral'})
        fig.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        st.plotly_chart(fig, use_container_width=True)

    # Learner Segmentation by Engagement Level (Donut Chart)
    with chart_col2:
        st.subheader("Learner Segmentation by Engagement Level")
        fig = px.pie(data['segmentation_data'], values='Percentage', names='Segment', hole=0.5,
                     color='Segment',
                     color_discrete_map={
                         'Highly Engaged': 'lightgreen',
                         'Medium Engaged': 'lightblue',
                         'At-Risk': 'gold',
                         'Dormant': 'indianred'
                     })
        fig.update_traces(textposition='outside', textinfo='percent+label')
        fig.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # 3. Bottom Bar Chart
    st.markdown("---")
    st.subheader("Top Features Driving Churn")
    fig = px.bar(data['top_features_df'].sort_values('Impact', ascending=True),
                 x='Impact', y='Feature', orientation='h',
                 color_discrete_sequence=['#1f77b4'],
                 labels={'Impact': 'Relative Impact Score'})
    fig.update_layout(height=300, margin={"t": 0, "b": 0, "l": 0, "r": 0})
    st.plotly_chart(fig, use_container_width=True)


def learners_page(data):
    """
    Renders the Learners page (Page 2 of prototype).
    """
    st.title("👤 Learners")
    st.header("Learner Segmentation Explorer")

    # Filters and Sub-Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        st.selectbox("Country", ["All Countries", "USA", "Armenia", "China", "Spain"])
    with col2:
        st.selectbox("Subscription Tier", ["Premium", "Pro", "Basic"])

    tab1, tab2, tab3 = st.tabs(["RFM Analysis", "K-Means Segmentation", "Churn Prediction"])

    with tab1:
        st.subheader("RFM Analysis: Behavioral View")
        st.caption("Recency, Frequency, and Monetary Value breakdown.")
        st.dataframe(data['learner_data'].drop(columns=['Days Inactive', 'Action']), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("K-Means Segmentation")
        st.info("💡 Groups learners into segments for targeted actions.")
        st.markdown("**Example Segment Description:** The 'Loyalists' segment (High CLV, High RFM Score) shows an average churn risk of 5%.")

    with tab3:
        st.subheader("Churn Prediction")
        st.info("🤖 ML models estimate churn probability per segment for proactive intervention.")
        st.markdown("**Prediction Overview:** Overall model accuracy is 87.5%.")


def at_risk_page(data):
    """
    Renders the At-Risk page (Page 3 of prototype)
    """
    st.title("🚨 At-Risk")
    st.header("High-Risk Learners")

    # KPI and Filters 
    st.markdown("""
        <div style="
            display: flex; 
            align-items: center; 
            gap: 20px; 
            padding-bottom: 20px;
        ">
            <div style="
                font-size: 2.5rem; 
                font-weight: 600;
                color: #e59c00; /* Amber for high risk */
            ">342</div>
            <div>
                <p style="
                    margin: 0; 
                    padding: 0; 
                    font-size: 0.9rem; 
                    color: #555;
                ">Total At-Risk Learners</p>
                <p style="
                    margin: 0; 
                    padding: 0; 
                    font-size: 0.9rem; 
                    color: #e59c00; 
                    font-weight: 500;
                ">⬆️ 8 new premium learners identified as high-risk this week.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Filters based on the prototype image
    col1, col2, col3 = st.columns([1.5, 2, 4])
    with col1:
        st.selectbox("Risk Threshold", ["> 70% Risk", "50% Risk", "30% Risk"], label_visibility="collapsed")
    with col2:
        st.selectbox("Subscription Tier", ["All Subscriptions", "Premium", "Pro", "Basic"], label_visibility="collapsed")
    with col3:
        st.empty() 

    st.markdown("---")

    # Layout for Charts and Table
    chart_col1, chart_col2 = st.columns([2, 1])

    with chart_col1:
        st.subheader("High-Risk Learner List")
        
        high_risk_df = data['learner_data'][data['learner_data']['Churn Risk (%)'] > 70].copy()
        
        # Rename column for display only
        display_df = high_risk_df.rename(columns={'Churn Risk (%)': 'Churn Probability'})
        
        # Apply the list column configuration. 
        edited_df = st.data_editor(
            display_df[['Name', 'Segment', 'Days Inactive', 'Churn Probability', 'Action']], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Action": st.column_config.ListColumn(
                    "Action",
                    help="Enter required intervention actions as a comma-separated list (e.g., Email, Discount)", 
                    width="medium",
                )
            },
            # Disable editing on all other columns
            disabled=['Name', 'Segment', 'Days Inactive', 'Churn Probability']
        )

    with chart_col2:
        # Reasons for Churn Bar Chart 
        st.subheader("Reasons for Churn")
        reasons_data = pd.DataFrame({
            'Reason': ['Inactivity', 'Course Dropout', 'Payment Delay', 'Support Issues'],
            'Count': [55, 35, 20, 12] 
        })
        fig = px.bar(reasons_data, x='Reason', y='Count', color_discrete_sequence=['#1f77b4'])
        fig.update_layout(height=250, margin={"t": 10, "b": 50, "l": 0, "r": 0}, xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig, use_container_width=True)

        # Churn by Tier Pie Chart 
        st.subheader("Churn by Tier")
        tier_data = pd.DataFrame({'Tier': ['Premium', 'Basic', 'Pro'], 'Percentage': [45, 35, 20]})
        fig_pie = px.pie(tier_data, values='Percentage', names='Tier', hole=0.5,
                         color_discrete_map={'Premium': '#1f77b4', 'Basic': '#a6c6e2', 'Pro': '#2ca02c'}) 
        fig_pie.update_traces(textinfo='percent+label')
        fig_pie.update_layout(height=250, margin={"t": 10, "b": 0, "l": 0, "r": 0}, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)


def campaigns_page(data):
    """
    Renders the Campaigns page (Page 4 of prototype).
    """
    st.title("📢 Campaigns")
    st.header("Retention Campaigns Overview")

    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col2:
        st.button("✨ Create New Campaign", use_container_width=True)

    st.subheader("Active & Recent Campaigns")
    st.dataframe(data['campaign_df'], use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Campaign Performance Comparison (Lift vs. Churn Rate)")
    df = data['comparison_df']
    fig = px.bar(df, x='Campaign', y=['Churn Rate (%)', 'Retention Lift (%)'], barmode='group',
                 color_discrete_map={'Churn Rate (%)': '#1f77b4', 'Retention Lift (%)': '#2ca02c'})
    fig.update_layout(
        yaxis_title="Rate (%)",
        height=400,
        margin={"t": 0, "b": 0, "l": 0, "r": 0}
    )
    st.plotly_chart(fig, use_container_width=True)


def analytics_page(data):
    """
    Renders the Analytics page (Page 5 of prototype).
    """
    st.title("📈 Analytics")
    st.header("Predictive Insights")

    # Model Metrics KPI Row
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Model Accuracy", "87.5%", "+3.2%")
    col2.metric("Precision", "84.2%", "+1.5%")
    col3.metric("Recall", "89.8%", "+2.1%")
    col4.metric("AUC-ROC Score", "0.91", "+0.05")

    st.markdown("---")

    # Main Chart Row
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.subheader("Feature Importance")
        fig = px.bar(data['analytics_df'].sort_values('Importance'),
                     x='Importance', y='Feature', orientation='h',
                     color_discrete_sequence=['#1f77b4'],
                     labels={'Importance': 'Relative Importance'})
        fig.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.subheader("Churn Prediction Accuracy (ROC Curve)")
        # Mock ROC Curve: A placeholder chart
        roc_data = pd.DataFrame({
            'False Positive Rate': np.linspace(0, 1, 100),
            'True Positive Rate': np.power(np.linspace(0, 1, 100), 0.5)
        })
        fig = px.line(roc_data, x='False Positive Rate', y='True Positive Rate', title="ROC Curve")
        fig.add_shape(type='line', line=dict(dash='dash'), x0=0, y0=0, x1=1, y1=1) # Diagonal line
        fig.update_layout(height=400, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Bottom Charts Row
    bottom_col1, bottom_col2 = st.columns(2)

    with bottom_col1:
        st.subheader("Segment-wise Retention Probability")
        fig = px.bar(data['retention_prob_df'], x='Segment', y='Probability (%)',
                     color_discrete_sequence=['#1f77b4'])
        fig.update_layout(height=300, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        st.plotly_chart(fig, use_container_width=True)

    with bottom_col2:
        st.subheader("Survival Curve (Expected Subscription Duration)")
        # Mock Survival Curve: A placeholder area chart
        survival_data = pd.DataFrame({
            'Months': np.arange(0, 25, 3),
            'Survival Rate (%)': [100, 95, 85, 70, 50, 30, 15, 5, 0]
        })
        fig = px.area(survival_data, x='Months', y='Survival Rate (%)',
                      line_shape='hvh', color_discrete_sequence=['#1f77b4'])
        fig.update_layout(height=300, margin={"t": 0, "b": 0, "l": 0, "r": 0})
        st.plotly_chart(fig, use_container_width=True)


def feedback_page():
    """
    Renders the Feedback page (Page 6 of prototype).
    """
    st.title("💬 Feedback")
    st.header("Feedback & Continuous Learning")

    st.markdown("---")

    # System Status
    st.subheader("System Status")
    col1, col2 = st.columns([1, 4])
    col1.metric("Last Data Refresh", "3 hours ago")
    with col2:
        st.button("🔄 Refresh Now", key="refresh_data_btn")

    st.markdown("---")

    # Submit Feedback Form
    st.subheader("Submit Feedback")
    with st.form("feedback_form"):
        st.text_area("Your observation or suggestion",
                     placeholder="Share your insights about the model, dashboard, or retention strategies...")
        st.selectbox("Select category", ["Choose a category", "Data Quality", "Feature Request", "Bug Report", "Model Insight"])
        st.form_submit_button("Submit Feedback", type="primary")


# --- Main Application Logic ---

def main():
    """
    Handles the sidebar navigation and content rendering.
    """
    # 1. Generate Mock Data
    retention_churn_df, top_features_df, segmentation_data, learner_data, campaign_df, comparison_df, analytics_df, retention_prob_df = generate_mock_data()

    all_data = {
        'retention_churn_df': retention_churn_df,
        'top_features_df': top_features_df,
        'segmentation_data': segmentation_data,
        'learner_data': learner_data,
        'campaign_df': campaign_df,
        'comparison_df': comparison_df,
        'analytics_df': analytics_df,
        'retention_prob_df': retention_prob_df,
    }

    # 2. Sidebar Navigation
    st.sidebar.image("https://placehold.co/100x30/007bff/white?text=EdRetain") # Placeholder for EdRetain logo
    st.sidebar.markdown("## EdRetain Dashboard")

    page = st.sidebar.radio("Navigation",
        options=["Dashboard", "Learners", "At-Risk", "Campaigns", "Analytics", "Feedback"],
        index=0 
    )


    st.sidebar.markdown("---")
    

    # 3. Render Selected Page Content
    if page == "Dashboard":
        dashboard_page(all_data)
    elif page == "Learners":
        learners_page(all_data)
    elif page == "At-Risk":
        at_risk_page(all_data)
    elif page == "Campaigns":
        campaigns_page(all_data)
    elif page == "Analytics":
        analytics_page(all_data)
    elif page == "Feedback":
        feedback_page()

if __name__ == "__main__":
    main()
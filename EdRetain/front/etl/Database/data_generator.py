"""
Data Generation Functions for Online Educational Platform
"""
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

def generate_subscription_plan():
    """
    Create a list of EdRetain subscription plans with details.

    Returns:
        List[dict]: Each dictionary contains details of a subscription plan, including 
                    key, name, tier, billing cycle, price, currency, and available features.
    """   
    plans = [
        {
            "subscription_plan_key": 1,
            "plan_id_nk": "PLAN_FREE_001",
            "plan_name": "Free Tier",
            "tier": "Free",
            "billing_cycle": "N/A",
            "base_price": 0.00,
            "currency": "USD",
            "has_certificate": False,
            "has_mentoring": False,
            "has_downloads": False
        },
        {
            "subscription_plan_key": 2,
            "plan_id_nk": "PLAN_STD_MONTHLY_002",
            "plan_name": "Standard Monthly",
            "tier": "Standard",
            "billing_cycle": "Monthly",
            "base_price": 14.99,
            "currency": "USD",
            "has_certificate": True,
            "has_mentoring": False,
            "has_downloads": True
        },
        {
            "subscription_plan_key": 3,
            "plan_id_nk": "PLAN_STD_ANNUAL_003",
            "plan_name": "Standard Annual",
            "tier": "Standard",
            "billing_cycle": "Annual",
            "base_price": 149.99,
            "currency": "USD",
            "has_certificate": True,
            "has_mentoring": False,
            "has_downloads": True
        },
        {
            "subscription_plan_key": 4,
            "plan_id_nk": "PLAN_PREM_MONTHLY_004",
            "plan_name": "Premium Monthly",
            "tier": "Premium",
            "billing_cycle": "Monthly",
            "base_price": 29.99,
            "currency": "USD",
            "has_certificate": True,
            "has_mentoring": True,
            "has_downloads": True
        },
        {
            "subscription_plan_key": 5,
            "plan_id_nk": "PLAN_PREM_ANNUAL_005",
            "plan_name": "Premium Annual",
            "tier": "Premium",
            "billing_cycle": "Annual",
            "base_price": 299.99,
            "currency": "USD",
            "has_certificate": True,
            "has_mentoring": True,
            "has_downloads": True
        }
    ]
    return plans


def generate_user(user_key):
    """
    Generate a fake EdRetain user record with logical plan/status.

    Args:
        user_key (int): Unique user ID.

    Returns:
        dict: User information for the DimUser table.
    """
    signup_date = fake.date_between(start_date='-3y', end_date='today')
    birth_date = fake.date_of_birth(minimum_age=16, maximum_age=70)
    
    # Randomly assign initial plan
    initial_plan = random.randint(1, 5)
    
    # Conditional logic based on initial_plan
    if initial_plan in [4, 5]:  # Started with Premium
        is_premium_ever = True
        current_status = random.choices(
            ['Active', 'Cancelled', 'Paused', 'Downgraded'],
            weights=[0.65, 0.15, 0.10, 0.10]
        )[0]
        
    elif initial_plan in [2, 3]:  # Started with Standard
        # 30% upgraded to Premium at some point
        is_premium_ever = random.random() < 0.30
        
        if is_premium_ever:
            # They upgraded, so they stayed engaged
            current_status = random.choices(
                ['Active', 'Downgraded', 'Paused', 'Cancelled'],
                weights=[0.60, 0.20, 0.10, 0.10]
            )[0]
        else:
            # Never upgraded to Premium
            current_status = random.choices(
                ['Active', 'Cancelled', 'Paused'],
                weights=[0.50, 0.35, 0.15]
            )[0]
            
    else:  # initial_plan == 1 (Free tier)
        # Only 10% of Free users ever upgrade to Premium
        is_premium_ever = random.random() < 0.10
        
        if is_premium_ever:
            # They upgraded from Free
            current_status = random.choices(
                ['Active', 'Downgraded', 'Cancelled'],
                weights=[0.50, 0.30, 0.20]
            )[0]
        else:
            # Still Free or churned
            current_status = random.choices(
                ['Active', 'Inactive', 'Churned'],
                weights=[0.30, 0.40, 0.30]
            )[0]
    
    return {
        "user_key": user_key,
        "user_id_nk": f"USER_{user_key:06d}",
        "signup_date_key": int(signup_date.strftime('%Y%m%d')),
        "birth_date": birth_date,
        "gender": random.choice(['Male', 'Female']),
        "country": fake.country(),
        "city": fake.city(),
        "user_type": random.choice(['Individual', 'Student', 'Professional']),
        "acquisition_channel": random.choice(['Organic Search', 'Social Media', 'Referral', 'Paid Ads', 'Email Campaign']),
        "initial_plan_key": initial_plan,
        "is_premium_ever": is_premium_ever,
        "current_status": current_status,
        "created_at": signup_date,
        "updated_at": fake.date_time_between(start_date=signup_date, end_date='now')
    }

def generate_date(date_obj):
    """
    Create a date dimension record from a datetime object.

    Args:
        date_obj (datetime): Date to convert.

    Returns:
        dict: DimDate attributes.
    """
    return {
        "date_key": int(date_obj.strftime('%Y%m%d')),
        "full_date": date_obj,
        "year": date_obj.year,
        "quarter": (date_obj.month - 1) // 3 + 1,
        "month": date_obj.month,
        "month_name": date_obj.strftime('%B'),
        "week_of_year": date_obj.isocalendar()[1],
        "day_of_month": date_obj.day,
        "day_of_week": date_obj.weekday(),
        "day_name": date_obj.strftime('%A'),
        "is_weekend": date_obj.weekday() >= 5
    }

def generate_campaign(campaign_key):
    """
    Build a fake marketing campaign record.

    Args:
        campaign_key (int): Campaign ID.

    Returns:
        dict: Campaign information for the DimCampaign table.
    """

    campaign_types = {
    "Retention": {
        "target_risk_segments": ["High Risk", "At Risk"],
        "offer_types": ["Discount", "Free Trial Extension"],
        "default_channels": ["Email", "SMS"],
    },
    "Reactivation": {
        "target_risk_segments": ["Churned", "Inactive"],
        "offer_types": ["Free Trial Extension", "Discount"],
        "default_channels": ["Email", "Push Notification"],
    },
    "Upsell": {
        "target_risk_segments": ["Medium Risk", "Active"],
        "offer_types": ["Mentoring Session", "Free Content"],
        "default_channels": ["Email", "In-App"],
    },
    "Onboarding": {
        "target_risk_segments": ["All Users", "New Users"],
        "offer_types": ["Free Content", "Mentoring Session"],
        "default_channels": ["Email", "Push Notification"],
    }}
    
    campaign_type = random.choice(list(campaign_types.keys()))
    risk_segment = random.choice(campaign_types[campaign_type]["target_risk_segments"])
    offer_type = random.choice(campaign_types[campaign_type]["offer_types"])
    channel = random.choice(campaign_types[campaign_type]["default_channels"])
    
    start_date = fake.date_between(start_date='-1y', end_date='today')
    end_date = fake.date_between(start_date=start_date, end_date='+3m')
    
    return {
        "campaign_key": campaign_key,
        "campaign_id_nk": f"CAMP_{campaign_key:04d}",
        "campaign_name": f"{campaign_type} Campaign {fake.word().capitalize()}",
        "campaign_type": campaign_type,
        "target_risk_segment": risk_segment,
        "offer_type": offer_type,
        "default_channel": channel,
        "start_date_key": int(start_date.strftime('%Y%m%d')),
        "end_date_key": int(end_date.strftime('%Y%m%d'))
    }


def generate_channel(channel_key):
    """
    Create a record for a communication channel.

    Args:
        channel_key (int): Channel ID.

    Returns:
        dict: Channel information for the DimChannel table.
    """
    channels_data = [
        {"name": "Email", "cost_per_message": 0.01},
        {"name": "Push Notification", "cost_per_message": 0.005},
        {"name": "SMS", "cost_per_message": 0.05},
        {"name": "In-App", "cost_per_message": 0.00}
    ]
    
    channel = channels_data[channel_key - 1] if channel_key <= len(channels_data) else channels_data[0]
    
    return {
        "channel_key": channel_key,
        "channel_id_nk": f"CHANNEL_{channel_key:03d}",
        "channel_name": channel["name"],
        "channel_type": "Digital",
        "cost_per_message": channel["cost_per_message"]
    }


def generate_user_daily_activity(activity_id, user_key, date_key):
    """
    Generate a fake daily activity record for a user.

    Args:
        activity_id (int): Activity ID.
        user_key (int): User ID.
        date_key (int): Date key (YYYYMMDD).

    Returns:
        dict: Daily activity for FactUserDailyActivity.
    """
    is_active = random.random() > 0.3  # 70% chance of activity
    
    if is_active:
        logins = random.randint(1, 5)
        sessions = random.randint(1, 8)
        minutes = random.randint(10, 300)
        lessons = random.randint(0, 10)
        quizzes = random.randint(0, 5)
        courses = random.randint(1, 3)
        days_active_30d = random.randint(1, 30)
        days_since_login = random.randint(0, 7)
    else:
        logins = 0
        sessions = 0
        minutes = 0
        lessons = 0
        quizzes = 0
        courses = 0
        days_active_30d = random.randint(0, 15)
        days_since_login = random.randint(8, 60)
    
    return {
        "activity_id": activity_id,
        "user_key": user_key,
        "date_key": date_key,
        "subscription_plan_key": random.randint(1, 5),
        "logins_count": logins,
        "sessions_count": sessions,
        "minutes_watched": minutes,
        "lessons_completed": lessons,
        "quizzes_attempted": quizzes,
        "distinct_courses_accessed": courses,
        "active_days_last_30d": days_active_30d,
        "days_since_last_login": days_since_login,
        "is_inactive_7d_flag": days_since_login > 7,
        "is_premium": random.choice([True, False]),
        "has_active_subscription": random.choice([True, False])
    }

def generate_campaign_interaction(interaction_id, user_key, campaign_key, date_key, channel_key):
    """
    Generate a FactCampaignInteraction record.
    
    Args:
        interaction_id (int): Unique identifier for the interaction.
        user_key (int): Foreign key to user.
        campaign_key (int): Foreign key to campaign.
        date_key (int): Foreign key to date (YYYYMMDD).
        channel_key (int): Foreign key to channel.
        
    Returns:
        dict: Synthetic campaign interaction record matching schema.
    """
    # Logical funnel progression for interaction flags
    sent_flag = True  # Always sent
    opened_flag = random.choices([True, False], weights=[0.8, 0.2])[0]
    clicked_flag = opened_flag and random.choices([True, False], weights=[0.5, 0.5])[0]
    converted_flag = clicked_flag and random.choices([True, False], weights=[0.2, 0.8])[0]
    
    # Conversion lag calculation (only if converted)
    time_to_conversion_days = random.randint(0, 7) if converted_flag else None
    
    # Timestamp for when the interaction is created
    created_at = datetime.now()
    
    return {
        "interaction_id": interaction_id,
        "user_key": user_key,
        "campaign_key": campaign_key,
        "date_key": date_key,
        "channel_key": channel_key,
        "sent_flag": sent_flag,
        "opened_flag": opened_flag,
        "clicked_flag": clicked_flag,
        "converted_flag": converted_flag,
        "time_to_conversion_days": time_to_conversion_days,
        "created_at": created_at,
    }

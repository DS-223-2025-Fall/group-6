import os
import pandas as pd
import random
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import create_engine, text
import glob
from os import path

from Database.models import *
from Database.data_generator import (
    generate_subscription_plan,
    generate_user,
    generate_date,
    generate_campaign,
    generate_channel,
    generate_user_daily_activity,
    generate_campaign_interaction,
)
from Database.database import engine, Base

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Configuration
NUM_USERS = 1000
NUM_CAMPAIGNS = 50
NUM_CHANNELS = 4
NUM_DAYS_HISTORY = 90
NUM_INTERACTIONS = 2000

# Generate and save data

logger.info("Generating subscription plans...")
plans = generate_subscription_plan()
plans_df = pd.DataFrame(plans)
plans_df.to_csv("data/dim_subscription_plan.csv", index=False)

logger.info("Generating users...")
users = pd.DataFrame([generate_user(user_key) for user_key in range(1, NUM_USERS + 1)])
users.to_csv("data/dim_user.csv", index=False)

logger.info("Generating date dimension...")
start_date = datetime.now() - timedelta(days=NUM_DAYS_HISTORY)
date_range = pd.date_range(start=start_date, periods=NUM_DAYS_HISTORY)
dates = pd.DataFrame([generate_date(date) for date in date_range])
dates.to_csv("data/dim_date.csv", index=False)

logger.info("Generating campaigns...")
campaigns = pd.DataFrame([generate_campaign(campaign_key) for campaign_key in range(1, NUM_CAMPAIGNS + 1)])
campaigns.to_csv("data/dim_campaign.csv", index=False)

logger.info("Generating channels...")
channels = pd.DataFrame([generate_channel(channel_key) for channel_key in range(1, NUM_CHANNELS + 1)])
channels.to_csv("data/dim_channel.csv", index=False)

logger.info("Generating user daily activity...")
activity_records = []
activity_id = 1
for day in range(NUM_DAYS_HISTORY):
    current_date = date_range[day]
    date_key = int(current_date.strftime('%Y%m%d'))
    active_users = random.sample(range(1, NUM_USERS + 1), k=random.randint(300, 800))
    for user_key in active_users:
        activity_records.append(generate_user_daily_activity(activity_id, user_key, date_key))
        activity_id += 1
activity_df = pd.DataFrame(activity_records)
activity_df.to_csv("data/fact_user_daily_activity.csv", index=False)

# Collect keys for referential integrity
user_keys_list = users["user_key"].tolist()
channel_keys_list = channels["channel_key"].tolist()
campaign_keys_list = campaigns["campaign_key"].tolist()

logger.info("Generating campaign interactions...")
interactions = []
for interaction_id in range(1, NUM_INTERACTIONS + 1):
    user_key = random.choice(user_keys_list)
    campaign_key = random.choice(campaign_keys_list)
    date_key = int(random.choice(date_range).strftime('%Y%m%d'))
    channel_key = random.choice(channel_keys_list)
    interactions.append(
        generate_campaign_interaction(
            interaction_id, user_key, campaign_key, date_key, channel_key
        )
    )
interactions_df = pd.DataFrame(interactions)
interactions_df.to_csv("data/fact_campaign_interaction.csv", index=False)

# Utility function to load CSV into DB
def load_csv_to_table(table_name: str, csv_path: str) -> None:
    df = pd.read_csv(csv_path) 
    df.to_sql(table_name, con=conn, if_exists="append", index=False, method="multi")
    logger.info(f"Loading data into table: {table_name}")

# Loading CSV files into respective tables
folder_path = "data/*.csv"
files = glob.glob(folder_path)
files = sorted(files, key=path.getmtime)
base_names = [path.splitext(path.basename(file))[0] for file in files]

for table in base_names:
    try:
        logger.info(f"Loading data into table: {table}")
        load_csv_to_table(table, path.join("data", f"{table}.csv"))
    except Exception as e:
        logger.error(f"Failed to ingest table {table}. Error: {e}")
        print(f"Failed to ingest table {table}. Moving to next!")

print("Tables are populated.")

sequence_reset_queries = [
    "SELECT setval('fact_campaign_interaction_interaction_id_seq', (SELECT MAX(interaction_id) FROM fact_campaign_interaction))",
    "SELECT setval('dim_user_user_key_seq', (SELECT MAX(user_key) FROM dim_user))",
    "SELECT setval('dim_campaign_campaign_key_seq', (SELECT MAX(campaign_key) FROM dim_campaign))",
    "SELECT setval('dim_channel_channel_key_seq', (SELECT MAX(channel_key) FROM dim_channel))",
    "SELECT setval('dim_date_date_key_seq', (SELECT MAX(date_key) FROM dim_date))",
    "SELECT setval('dim_subscription_plan_subscription_plan_key_seq', (SELECT MAX(subscription_plan_key) FROM dim_subscription_plan))",
    "SELECT setval('fact_user_daily_activity_fact_user_daily_activity_id_seq', (SELECT MAX(fact_user_daily_activity_id) FROM fact_user_daily_activity))",
    #"SELECT setval('fact_user_analytics_snapshot_fact_user_analytics_snapshot_id_seq', (SELECT MAX(fact_user_analytics_snapshot_id) FROM fact_user_analytics_snapshot))",
]

with engine.connect() as conn:
    for query in sequence_reset_queries:
        try:
            conn.execute(text(query))
            logger.info(f"Sequence reset: {query}")
        except Exception as e:
            logger.warning(f"Failed to reset sequence: {query}, Error: {e}")

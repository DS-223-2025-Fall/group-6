import pandas as pd
from loguru import logger
from sqlalchemy import create_engine
from Database.database import engine

# Utility function to load CSV into DB using a SQLAlchemy Connection
def load_csv_to_table(table_name: str, csv_path: str) -> None:
    df = pd.read_csv(csv_path)
    try:
        with engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists="append", index=False, method="multi")
        logger.info(f"Loaded data into table: {table_name}")
    except Exception as e:
        logger.error(f"Failed to ingest table {table_name}. Error: {e}")
        print(f"Failed to ingest table {table_name}. Moving to next!")
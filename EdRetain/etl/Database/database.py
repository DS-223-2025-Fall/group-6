"""
Database Configuration
"""

import sqlalchemy as create_engine
from sqlalchemy.orm import declarative_base
import sqlalchemy.orm as orm
from dotenv import load_dotenv
import os
from sqlalchemy.ext.declarative import declarative_base


def get_db():
    """
    Function to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Load environment variables from .env file
# Load environment variables from a .env file (if present)
load_dotenv()

# Get the database URL from environment variables, fall back to a local default for dev
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/edretaindb",
)

# Create the SQLAlchemy engine (will always receive a string now)
#engine = create_engine(DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


# Base class for declarative models (SQLAlchemy 2.0 style)
Base = declarative_base()

# SessionLocal for database operations
SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
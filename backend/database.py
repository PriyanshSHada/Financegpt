from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import re
from dotenv import load_dotenv
import logging

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. Set it in your Render environment variables.\n"
        "For Render, use the Supabase Session Pooler URL from the Connect page.\n"
        "Copy its host, port, and username exactly as supplied.\n"
        "Get the connection string from Supabase Dashboard → Connect → Session Pooler."
    )

# Select psycopg2 explicitly; SQLAlchemy otherwise defaults to psycopg 3.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgresql://"):]

# Add SSL mode parameter for stable connections
if "sslmode" not in DATABASE_URL and "?" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL + "?sslmode=require"
elif "sslmode" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?", "?sslmode=require&", 1)

# Keep Supabase pooler endpoints unchanged; psycopg2 supports the pooler URL.
if "pooler.supabase.com" in DATABASE_URL:
    logging.warning(
        "Using Supabase connection pooler with psycopg2. "
        "The configured pooler endpoint will be used as provided."
    )
    # Keep pooler URL as-is - let Supabase handle the connection routing

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    # Test connection - Commented out for Render deployment
    # with engine.connect() as conn:
    #     pass
    logging.info("Database connection established successfully")
except Exception as e:
    error_msg = str(e)
    logging.error(
        f"Database connection failed.\n"
        f"Error: {error_msg}\n"
        f"Your DATABASE_URL starts with: {make_url(DATABASE_URL).render_as_string(hide_password=True)[:80]}...\n"
        f"\n"
        f"For Render, use the Supabase Session Pooler URL if the direct database endpoint is unreachable over IPv6.\n"
        f"Copy the pooler host, port, and username exactly from Supabase; this backend preserves them and selects psycopg2.\n"
        f"Get the URL from: Supabase Dashboard → Connect → Session Pooler"
    )
    raise  # Re-raise the exception to prevent app startup with database issues
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

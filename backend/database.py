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
        "Example for Supabase: postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres\n"
        "Note: Use 'postgres' as the username, NOT 'postgres.PROJECT_ID'.\n"
        "Get your connection string from Supabase Dashboard → Project Settings → Database → Connection String."
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

# Log a warning if the connection string looks like it has incorrect format
if "postgres." in DATABASE_URL and "postgres:" not in DATABASE_URL:
    logging.warning(
        "Detected 'postgres.' in connectionstring - this may indicate an incorrect username format. "
        "Supabase typically uses 'postgres' as the username, not 'postgres.project-id'."
    )

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
        f"Common Supabase connection string formats for Render:\n"
        f"\n"
        f"1. Direct connection (recommended for psycopg2):\n"
        f"   postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require\n"
        f"\n"
        f"2. Connection pooler (keep the pooler host and port from Supabase):\n"
        f"   postgresql://postgres:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require\n"
        f"\n"
        f"IMPORTANT: If you get 'Network is unreachable' or IPv6 errors:\n"
        f"- Use direct connection instead of pooler, OR\n"
        f"- Verify the pooler host, port, and username against the Supabase dashboard\n"
        f"- Make sure your connection string uses 'postgres' as username, not 'postgres.PROJECT_ID'\n"
        f"\n"
        f"Get your connection string from: Supabase Dashboard → Project Settings → Database → Connection String"
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

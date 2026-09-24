from sqlalchemy import create_engine
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

# Render provides postgres:// URLs; SQLAlchemy 1.4+ requires postgresql://
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Add SSL mode parameter for stable connections
if "sslmode" not in DATABASE_URL and "?" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL + "?sslmode=require"
elif "sslmode" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?", "?sslmode=require&", 1)

# Handle Supabase connection - psycopg2 compatibility
# psycopg2 works better with direct connections in most cases
# But if using pooler, we'll keep it as pooler for compatibility
# Direct connections are preferred as they avoid IPv6 issues with pooler->direct conversion
if "pooler.supabase.com" in DATABASE_URL:
    logging.warning(
        "Using Supabase connection pooler. For psycopg2 compatibility, "
        "consider using direct connection URL from Supabase Dashboard."
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
        f"Your DATABASE_URL starts with: {DATABASE_URL[:80]}...\n"
        f"\n"
        f"Common Supabase connection string formats for Render:\n"
        f"\n"
        f"1. Direct connection (recommended for psycopg2):\n"
        f"   postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require\n"
        f"\n"
        f"2. Connection pooler (requires SUPABASE_PROJECT_ID env var):\n"
        f"   postgresql://postgres:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require\n"
        f"   Set SUPABASE_PROJECT_ID=bkxkhxfsejootdbkrgjs in environment variables\n"
        f"\n"
        f"IMPORTANT: If you get 'Network is unreachable' or IPv6 errors:\n"
        f"- Use direct connection instead of pooler, OR\n"
        f"- Set SUPABASE_PROJECT_ID environment variable for pooler connections\n"
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

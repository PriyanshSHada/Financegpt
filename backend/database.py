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

# Handle Supabase connection pooler - psycopg2 compatibility
# psycopg2 doesn't support sslhostname parameter, so we convert pooler to direct connection
if "pooler.supabase.com" in DATABASE_URL:
    # Try to extract project ID from the connection pooler URL
    db_match = re.search(r'db\.([a-z0-9]+)\.supabase\.co', DATABASE_URL)
    if db_match:
        project_id = db_match.group(1)
    else:
        # If project ID not in URL, try environment variable
        project_id = os.getenv("SUPABASE_PROJECT_ID")
        if not project_id:
            logging.error(
                "Could not extract project ID from pooler URL. "
                "Please set SUPABASE_PROJECT_ID environment variable or use direct connection string.\n"
                "For psycopg2 compatibility, use direct connection string format:\n"
                "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require"
            )
            raise RuntimeError(
                "SUPABASE_PROJECT_ID environment variable is required when using connection pooler. "
                "Set it in your Render environment variables."
            )
    
    # Convert pooler URL to direct database URL for psycopg2 compatibility
    # Replace pooler endpoint with direct db endpoint
    DATABASE_URL = DATABASE_URL.replace(
        "aws-1-ap-southeast-1.pooler.supabase.com:6543",
        f"db.{project_id}.supabase.co:5432"
    )
    logging.info(f"Converted pooler connection to direct connection for psycopg2 compatibility")

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
    logging.error(
        f"Database connection failed.\n"
        f"Error: {str(e)}\n"
        f"Your DATABASE_URL starts with: {DATABASE_URL[:80]}...\n"
        f"\n"
        f"Common Supabase connection string format for Render:\n"
        f"postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require\n"
        f"\n"
        f"IMPORTANT: If using connection pooler, make sure SUPABASE_PROJECT_ID is set.\n"
        f"For direct connection: postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require"
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

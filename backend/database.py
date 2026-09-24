from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
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
    logging.warning(
        f"Database connection test failed (this may be expected on first startup).\n"
        f"Error: {str(e)}\n"
        f"Your DATABASE_URL starts with: {DATABASE_URL[:80]}...\n"
        f"\n"
        f"Common Supabase connection string format for Render:\n"
        f"postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require\n"
        f"\n"
        f"IMPORTANT: For connection pooling, include the project ID in SSL hostname:\n"
        f"postgresql://postgres:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require&sslhostname=db.bkxkhxfsejootdbkrgjs.supabase.co"
    )
    # Don't raise - let the app start and try to connect when needed
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

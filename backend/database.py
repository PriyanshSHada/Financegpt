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

# Log a warning if the connection string looks like it has incorrect format
if "postgres." in DATABASE_URL and "postgres:" not in DATABASE_URL:
    logging.warning(
        "Detected 'postgres.' in connectionstring - this may indicate an incorrect username format. "
        "Supabase typically uses 'postgres' as the username, not 'postgres.project-id'."
    )

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    # Test connection
    with engine.connect() as conn:
        pass
    logging.info("Database connection established successfully")
except Exception as e:
    logging.error(
        f"Failed to connect to database. Make sure DATABASE_URL is correctly set in Render environment variables.\n"
        f"Error: {str(e)}\n"
        f"Your DATABASE_URL starts with: {DATABASE_URL[:80]}...\n"
        f"\n"
        f"Common Supabase connection string format:\n"
        f"postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres\n"
        f"OR\n"
        f"postgresql://postgres:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
    )
    raise
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

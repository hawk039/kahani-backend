from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from a .env file at the project root
# We explicitly point to the .env file to be safe
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Fallback: try loading without path if the above failed (e.g. in some docker setups)
if not os.getenv("DATABASE_URL"):
    load_dotenv()

# --- PostgreSQL Configuration ---
# The DATABASE_URL is now loaded from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Print current working directory to help debug
    print(f"Current working directory: {os.getcwd()}")
    print(f"Looking for .env at: {env_path}")
    raise ValueError("DATABASE_URL environment variable not set. Please create a .env file.")

# Create the engine with connection pooling options
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Check if connection is alive before using it
    pool_recycle=1800    # Recycle connections every 30 minutes
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

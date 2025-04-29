from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables from a .env file
load_dotenv()

# Debugging: Print to check if DATABASE_URL is loaded
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

# Get the database URL from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Error: DATABASE_URL is not set. Check your .env file.")

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()

# Metadata instance for the database schema
metadata = MetaData()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
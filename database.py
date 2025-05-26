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

def init_db():
    Base.metadata.create_all(bind=engine)

def batch_insert(model, data_list, batch_size=100):
    """Insert records in batches for better performance"""
    db = SessionLocal()
    try:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            db.bulk_insert_mappings(model, batch)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def update_existing_records(model, update_data, filter_field):
    """Update existing records in the database"""
    db = SessionLocal()
    try:
        for data in update_data:
            db.query(model).filter(
                getattr(model, filter_field) == data[filter_field]
            ).update(data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
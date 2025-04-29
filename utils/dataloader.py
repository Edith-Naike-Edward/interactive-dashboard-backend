import pandas as pd
from sqlalchemy.orm import Session
from models import User, Site
from database import engine


def clear_existing_data(db: Session):
    """Clear all existing data"""
    db.query(User).delete()
    db.query(Site).delete()
    db.commit()

def load_sites_from_csv(db: Session, csv_path: str):
    """Load site data from CSV"""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        site = Site(
            site_id=row['site_id'],
            name=row['name'],
            site_type=row['site_type'],
            county_id=row['county_id'],
            sub_county_id=row['sub_county_id'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            is_active=row.get('is_active', True)  # Default to True if column missing
        )
        db.add(site)
    db.commit()

def load_users_from_csv(db: Session, csv_path: str):
    """Load user data from CSV"""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        user = User(
            id=row['id'],
            name=row['name'],
            email=row['email'],
            password=row['password'],
            role=row['role'],
            organisation=row['organisation'],
            site_id=row['site_id'],
            is_active=row.get('is_active', True)  # Default to True if column missing
        )
        db.add(user)
    db.commit()

# def reload_all_data():
#     """Main function to reload all data"""
#     with Session(engine) as db:
#         clear_existing_data(db)
#         load_sites_from_csv(db, "data/raw/sites.csv")
#         load_users_from_csv(db, "data/raw/users.csv")
#         print("Data reload complete!")
def reload_all_data(db: Session):
    clear_existing_data(db)
    load_sites_from_csv(db, "data/raw/sites.csv")
    load_users_from_csv(db, "data/raw/users.csv")
    print("Data reload complete!")

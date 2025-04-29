from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import os
from typing import List, Dict

router = APIRouter(tags=["sites"])

# Define the path to your CSV file
SITE_CSV_PATH = "data/raw/sites.csv"

@router.get("/sites", response_model=List[Dict[str, object]])
def get_sites():
    """Get list of all sites from CSV"""
    try:
        # Check if file exists
        if not os.path.exists(SITE_CSV_PATH):
            raise HTTPException(
                status_code=404,
                detail="Sites data file not found"
            )

        # Read CSV with error handling
        sites_df = pd.read_csv(SITE_CSV_PATH)

        # Validate required columns
        required_columns = {'site_id', 'name'}
        if not required_columns.issubset(sites_df.columns):
            missing = required_columns - set(sites_df.columns)
            raise HTTPException(
                status_code=422,
                detail=f"CSV missing required columns: {missing}"
            )

        # # Clean and validate data
        # sites_df = sites_df.dropna(subset=['site_id', 'name'])  # Remove rows with missing values
        # sites_df = sites_df.drop_duplicates(subset=['site_id'])  # Remove duplicate IDs

        # Convert to list of dictionaries with consistent field names
        sites = sites_df[['site_id', 'name']].rename(columns={'site_id': 'id'}).to_dict('records')

        # Additional validation
        if len(sites) == 0:
            raise HTTPException(
                status_code=404,
                detail="No valid sites found in data file"
            )

        return sites

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=422,
            detail="CSV file is empty or corrupt"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading sites data: {str(e)}"
        )
# # sites.py
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from database import get_db
# from models import Site
# import pandas as pd

# router = APIRouter(tags=["sites"])

# @router.get("/sites")
# def get_sites(db: Session = Depends(get_db)):
#     """Get list of all sites"""
#     # If you're using SQLAlchemy
#     sites = db.query(Site).all()
#     return [{"id": site.id, "name": site.name} for site in sites]
    
#     # OR if you're using CSV:
#     # sites_df = pd.read_csv("data/raw/sites.csv")
#     # return sites_df[["site_id", "name"]].to_dict("records")
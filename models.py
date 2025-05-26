from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Create a base class for declarative class definitions
Base = declarative_base()

# Define a User class which will be mapped to the 'users' table
class User(Base):
    __tablename__ = "users"
    
    # Define columns for the 'users' table
    id = Column(Integer, primary_key=True, index=True)  # Primary key
    name = Column(String, nullable=False)  # User's name
    email = Column(String, unique=True, index=True)  # User's email, must be unique
    password = Column(String, nullable=False)  # User's password
    role = Column(String, nullable=False)  # User's role
    organisation = Column(String, nullable=False)  # User's organisation
    is_active = Column(Boolean, default=True)  # User's active status (1 for active, 0 for inactive)

    site_id = Column(Integer, ForeignKey("sites.site_id"))
    site = relationship("Site", back_populates="users")

class Site(Base):
    __tablename__ = "sites"

    site_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    site_type = Column(String, nullable=False)
    county_id = Column(Integer, nullable=False)
    sub_county_id = Column(Integer, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True) # Default to True if column missing

    users = relationship("User", back_populates="site")
class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    initial = Column(String(100))
    gender = Column(String(10))
    date_of_birth = Column(DateTime)
    age = Column(Integer)
    national_id = Column(String(50))
    sub_county_id = Column(Integer)
    sub_county_name = Column(String(100))
    county_id = Column(Integer)
    county_name = Column(String(100))
    country_id = Column(String(10))
    country_name = Column(String(100))
    phone_number = Column(String(20))
    phone_number_category = Column(String(50))
    landmark = Column(String(200))
    level_of_education = Column(String(100))
    occupation = Column(String(100))
    is_regular_smoker = Column(Boolean)
    is_pregnant = Column(Boolean)
    is_support_group = Column(Boolean)
    insurance_id = Column(String(50))
    insurance_type = Column(String(50))
    insurance_status = Column(String(50))
    site_id = Column(Integer)
    site_name = Column(String(100))
    program_id = Column(String(50))
    program_name = Column(String(100))
    is_active = Column(Boolean)
    is_deleted = Column(Boolean)
    tenant_id = Column(String(50))
    created_by = Column(String(50))
    updated_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Health conditions
    has_hypertension = Column(Boolean)
    on_htn_meds = Column(Boolean)
    has_diabetes = Column(Boolean)
    on_diabetes_meds = Column(Boolean)
    has_mental_health_issue = Column(Boolean)
    on_mh_treatment = Column(Boolean)
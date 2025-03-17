from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

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

# Define a HealthData class which will be mapped to the 'health_data' table
class HealthData(Base):
    __tablename__ = "health_data"
    
    # Define columns for the 'health_data' table
    id = Column(Integer, primary_key=True, index=True)  # Primary key
    age = Column(Integer, nullable=False)  # Age of the individual
    gender = Column(String, nullable=False)  # Gender of the individual
    height = Column(Float, nullable=False)  # Height of the individual
    weight = Column(Float, nullable=False)  # Weight of the individual
    ap_hi = Column(Integer, nullable=False)  # Systolic blood pressure
    ap_lo = Column(Integer, nullable=False)  # Diastolic blood pressure
    cholesterol = Column(Integer, nullable=False)  # Cholesterol level
    gluc = Column(Integer, nullable=False)  # Glucose level
    smoke = Column(Integer, nullable=False)  # Smoking status (0 or 1)
    alco = Column(Integer, nullable=False)  # Alcohol intake status (0 or 1)
    active = Column(Integer, nullable=False)  # Physical activity status (0 or 1)
    cardio = Column(Integer, nullable=False)  # Presence of cardiovascular disease (0 or 1)
    AgeinYr = Column(Integer, nullable=False)  # Age in years
    BMI = Column(Float, nullable=False)  # Body Mass Index
    BMICat = Column(String, nullable=False)  # BMI category
    AgeGroup = Column(String, nullable=False)  # Age group category
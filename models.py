from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

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

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    profile_picture = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")

from database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from auth.models import User


class Item(Base):
    __tablename__='items'
    
    id: int = Column(Integer,primary_key=True, index=True)
    user_id: int = Column(ForeignKey(User.id, ondelete="Cascade"), nullable=False)
    name: str = Column(String, nullable=False)
    
    user=relationship("User", back_populates="items")
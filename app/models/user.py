from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    uid = Column(String, unique=True, index=True, nullable=True)  # Firebase UID
    avatar_url = Column(String, nullable=True) # Added avatar_url

    # Relationship to Story
    stories = relationship("Story", back_populates="owner")

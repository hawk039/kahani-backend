from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base # Updated import

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    genre = Column(String, nullable=False)
    tone = Column(String, nullable=False)
    language = Column(String, nullable=False)
    image_filename = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to User
    owner = relationship("User", back_populates="stories")

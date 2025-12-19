from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base_class import Base # Updated import

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_on = Column(DateTime, default=datetime.utcnow)

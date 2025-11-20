from sqlalchemy.orm import Session
from app.models.blacklist import BlacklistedToken

def blacklist_token(db: Session, token: str):
    db_token = BlacklistedToken(token=token)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def is_token_blacklisted(db: Session, token: str) -> bool:
    return db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None

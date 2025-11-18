from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password

def create_user(db: Session, user: UserCreate):
    hashed = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

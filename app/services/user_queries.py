from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password

# -------------------------
# Email/password user
# -------------------------
def create_user_query(db: Session, user: UserCreate):
    """
    Create a new user with email/password.
    """
    hashed = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_email_query(db: Session, email: str):
    """
    Retrieve a user by email.
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_id_query(db: Session, user_id: int):
    """
    Retrieve a user by ID.
    """
    return db.query(User).filter(User.id == user_id).first()


# -------------------------
# Google user
# -------------------------
def create_user_with_google_query(db: Session, user):
    """
    Create a new user from Google sign-in.
    `user` is a GoogleUserCreate object (uid, email, token)
    """
    new_user = User(
        uid=user.uid,          # Make sure User model has  'uid' column
        email=user.email,
        hashed_password=None   # No password for Google users
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

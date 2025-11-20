# app/services/user_service.py
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password, verify_password, create_access_token
from app.services.user_queries  import create_user_query, get_user_by_email_query, get_user_by_id_query


# Create user with business logic
def create_user(db: Session, user: UserCreate):
    # Check if email already exists
    existing_user = get_user_by_email_query(db, user.email)
    if existing_user:
        raise ValueError("Email already exists")

    # Hash password
    hashed = hash_password(user.password)

    # Save user
    return create_user_query(db, user, hashed)


# Login logic
def login_user(db: Session, email: str, password: str):
    user = get_user_by_email_query(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")

    # Generate token
    token = create_access_token({"sub": user.id})
    return {"user": user, "access_token": token}


# Get user by ID (just call query)
def get_user_by_id(db: Session, user_id: int):
    return get_user_by_id_query(db, user_id)

def get_user_by_email(db: Session, email: str):
    return get_user_by_email_query(db, email)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.user_schema import UserCreate, UserResponse
from app.schemas.user_schema import ForgetPassword, UserResponse
from app.services.user_service import create_user, get_user_by_email
from app.core.security import verify_password, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    return create_user(db, user)

@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return {"access_token": token}

@router.post("/fpassword")
def fpassword(payload: ForgetPassword, db: Session = Depends(get_db)):
    # Step 1: Find user by email
    db_user = get_user_by_email(db, payload.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Step 2: Hash the new password
    hashed_pw = hash_password(payload.new_password)

    # Step 3: Update database
    db_user.hashed_password = hashed_pw
    db.commit()
    db.refresh(db_user)

    return {"message": "Password updated successfully"}


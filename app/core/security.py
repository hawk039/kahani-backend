from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.db.database import get_db
from app.services.token_blacklist_service import is_token_blacklisted
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

# --- JWT CONFIG ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set. Please create a .env file.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- PASSWORD HELPERS (using bcrypt directly) ---

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


# --- TOKEN CREATION ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- CURRENT USER HANDLER ---
def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    from app.services.user_service import get_user_by_email

    if is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=401,
            detail="Token is blacklisted. Please login again."
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

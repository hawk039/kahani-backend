from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.token_blacklist_service import is_token_blacklisted
from fastapi.security import OAuth2PasswordBearer



# --- JWT CONFIG ---
SECRET_KEY = "your-secret-key"  # change before production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- PASSWORD HELPERS ---
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


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
    # Import here to avoid circular import
    from app.services.user_service import get_user_by_email

    # 1) Check if token is blacklisted
    if is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=401,
            detail="Token is blacklisted. Please login again."
        )

    # 2) Decode JWT
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

    # 3) Fetch user from DB
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


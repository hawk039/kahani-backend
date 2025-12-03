from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
import bcrypt  # Use bcrypt directly
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.token_blacklist_service import is_token_blacklisted
from fastapi.security import OAuth2PasswordBearer

# --- JWT CONFIG ---
SECRET_KEY = "your-secret-key"  # change before production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- PASSWORD HELPERS (using bcrypt directly) ---

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    The password is first encoded to UTF-8 bytes.
    The resulting hash is a string.
    """
    # Bcrypt handles the 72-byte limit internally, but we must pass it bytes.
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # Store the hash as a string
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed one.
    """
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
    # Import here to avoid circular import
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
